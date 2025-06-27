import requests
import time
from datetime import datetime
from packages.Logging import CloudLogger
from packages.Notion import Notion
from packages.Tasks import Tasks
from packages.Slack import SlackMessageBuilder, send_direct_message, SlackCache
from web3 import Web3
import json

# Initialize logger with structured logging
logger = CloudLogger("webhook")

def log_execution_time(func):
    """Decorator to log function execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"[{func.__name__}] Execution completed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[{func.__name__}] Failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    return wrapper

def process_purple_gold(payload: dict) -> dict:
    """
    Handler for 'trading_view' target. Forwards the payload to the purple_gold Cloud Function.

    Args:
        payload (dict): The complete alert payload to be forwarded.

    Returns:
        dict: Response metadata containing:
            - processed_by: Identifier of the processor
            - status_code: HTTP status code from the purple_gold function
            - response: Text response from the purple_gold function
            - execution_time: Time taken to process the request

    Raises:
        requests.RequestException: If the request to purple_gold fails
    """
    start_time = time.time()
    logger.info(f"[process_purple_gold] Starting processing for payload: {payload}")
    
    worker_url = "https://europe-west1-digital-africa-rainbow.cloudfunctions.net/purple_gold"
    try:
        logger.debug(f"[process_purple_gold] Sending request to {worker_url}")
        response = requests.post(worker_url, json=payload)
        response.raise_for_status()
        
        execution_time = time.time() - start_time
        logger.info(f"[process_purple_gold] Successfully processed in {execution_time:.2f}s. Status: {response.status_code}")
        
        return {
            "processed_by": "purple_gold",
            "status_code": response.status_code,
            "response": response.text,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    except requests.RequestException as e:
        execution_time = time.time() - start_time
        logger.error(f"[process_purple_gold] Failed after {execution_time:.2f}s. Error: {str(e)}")
        raise

def process_balance_of(payload: dict) -> dict:
    """
    Handler for 'beta' target. Processes the payload data.

    Args:
        payload (dict): The data payload to be processed.

    Returns:
        dict: Processing result containing:
            - processed_by: Identifier of the processor
            - tasks_created: Number of tasks created
            - execution_time: Time taken to process
    """
    start_time = time.time()
    logger.info(f"[process_balance_of] Starting processing for payload: {payload}")
    
    try:
        data = payload['data']
        params = {'database': 'CONTRACTS', 'query': 'token_list'}
        logger.debug(f"[process_balance_of] Fetching data from Notion with params: {params}")
        
        data = Notion.Query(**params).run()
        reader = Notion.reader
        tasks_created = 0
        
        for c in data:
            try:
                line = {
                    'page_id': c['id'],
                    'Name': reader.title(c['properties']['Name']),
                    'Type': reader.select(c['properties']['Type']),
                    'Network': reader.select(c['properties']['Network']),
                    'Address': Web3.to_checksum_address(reader.text(c['properties']['Address']))
                }
                task = {
                    'url': 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/balance_of',
                    'payload': line
                }
                Tasks().add_task(task)
                tasks_created += 1
                logger.debug(f"[process_balance_of] Created task for {line['Name']}")
            except Exception as e:
                logger.error(f"[process_balance_of] Failed to process contract {c.get('id', 'unknown')}: {str(e)}")
                continue
        
        execution_time = time.time() - start_time
        logger.info(f"[process_balance_of] Successfully created {tasks_created} tasks in {execution_time:.2f}s")
        
        return {
            "status": "success",
            "tasks_created": tasks_created,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[process_balance_of] Failed after {execution_time:.2f}s: {str(e)}")
        raise


def process_simple_direct_message(payload: dict) -> dict:
    """
    Handler for 'simple_direct_message' target. Processes the payload data.

    Args:
        payload (dict): The data payload to be processed.

    Returns:
        dict: Processing result containing:
            - status: Success/failure status
            - execution_time: Time taken to process
            - message_sent: Whether the message was sent successfully
            - error: Error message if any
    """
    start_time = time.time()
    logger.info(f"[process_simple_direct_message] Starting processing for payload: {payload}")
    
    try:
        # Log the full payload structure for debugging
        logger.debug(f"[process_simple_direct_message] Full payload structure: {json.dumps(payload, indent=2)}")
        
        # Extract data from Notion payload
        data = payload.get('data', {})
        if not data:
            raise ValueError("No data found in payload")
            
        # Log the data structure
        logger.debug(f"[process_simple_direct_message] Data structure: {json.dumps(data, indent=2)}")
        
        properties = data.get('properties', {})
        if not properties:
            raise ValueError("No properties found in data")
            
        # Log the properties structure
        logger.debug(f"[process_simple_direct_message] Properties structure: {json.dumps(properties, indent=2)}")
        
        # Extract person information
        asked_by = properties.get('Asked by', {})
        if not asked_by:
            raise ValueError("No 'Asked by' field found in properties")
            
        people = asked_by.get('people', [])
        if not people:
            raise ValueError("No people found in 'Asked by' field")
            
        notion_id = people[0].get('id')
        if not notion_id:
            raise ValueError("No ID found for person")
            
        logger.debug(f"[process_simple_direct_message] Found Notion ID: {notion_id}")
        
        # Get Slack ID from cache
        slack_cache = SlackCache()
        people = slack_cache.get_people()
        if not people:
            raise ValueError("No people found in Slack cache")
            
        # Log the people cache for debugging
        logger.debug(f"[process_simple_direct_message] People cache: {json.dumps(people, indent=2)}")
        
        person = next((p for p in people if p.get('Notion ID') == notion_id), None)
        if not person:
            raise ValueError(f"No matching person found for Notion ID: {notion_id}")
            
        slack_id = person.get('Slack ID')
        if not slack_id:
            raise ValueError(f"No Slack ID found for person: {notion_id}")
            
        logger.debug(f"[process_simple_direct_message] Found Slack ID: {slack_id}")
        
        # Extract message
        message_prop = properties.get('Message', {})
        if not message_prop:
            raise ValueError("No 'Message' field found in properties")
        
        try:
            formula = message_prop.get('formula')
            #if not formula:
            #    raise ValueError("No formula found in Message field")
            message = formula.get('string')
        except Exception as e:
            formula = message_prop.get('rich_text')
            message = formula[0]['text']['content']

        if not message:
            raise ValueError("No message found in formula")
            
        logger.debug(f"[process_simple_direct_message] Extracted message: {message}")
        
        # Get URL
        url = data.get('url')
        if not url:
            raise ValueError("No URL found in data")
            
        logger.debug(f"[process_simple_direct_message] Found URL: {url}")
        
        # Build and send message
        message = SlackMessageBuilder()\
            .text('Coucou ')\
            .emoji('wave')\
            .url(url, 'Ci-dessous la reponse à ton ticket: ')\
            .text('\n'+message)\
            .build()
            
        logger.debug(f"[process_simple_direct_message] Sending message to {slack_id}")
        message_sent = send_direct_message(slack_id, message)
        
        execution_time = time.time() - start_time
        if message_sent:
            logger.info(f"[process_simple_direct_message] Successfully sent message in {execution_time:.2f}s")
        else:
            logger.error(f"[process_simple_direct_message] Failed to send message after {execution_time:.2f}s")
        
        return {
            "status": "success" if message_sent else "failed",
            "execution_time": execution_time,
            "message_sent": message_sent,
            "person": slack_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"[process_simple_direct_message] Failed after {execution_time:.2f}s: {str(e)}"
        logger.error(error_msg)
        # Log the full traceback for debugging
        import traceback
        logger.error(f"[process_simple_direct_message] Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "execution_time": execution_time,
            "message_sent": False,
            "error": str(e),
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
