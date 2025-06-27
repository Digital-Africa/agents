import requests
from flask import Request, jsonify
from packages.Logging import CloudLogger
from packages.Notion import Notion
from datetime import datetime
from packages.Function import Function
from packages.Tasks import Tasks

# Initialize logger
logger = CloudLogger(logger_name='Balance_Of')

def enqueue_contract(wrapper):
    page_id = wrapper['page_id']
    properties = wrapper['properties']
    payload = {'page_id':page_id,
               'body': {'parent': {'database_id': "1b50fcf38494801e843cda14be531c4a"},
                        'properties': properties}}
    task = {
            'url': 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_notion',
            'payload': payload,
            'queue': 'notion-queue'
            }
    response = Tasks().add_task(task)
    return response

def human_readable_abbreviated(number) -> str:
    """
    Convert a large integer (like a BigNumber) into a human-readable abbreviated string.

    :param value: The raw integer value.
    :param decimals: Number of token decimals (default is 18 for ETH).
    :return: Abbreviated human-readable string.
    """
    
    # Define suffixes
    suffixes = ['', 'K', 'M', 'B', 'T']
    magnitude = 0
    
    while abs(number) >= 1000 and magnitude < len(suffixes) - 1:
        number /= 1000.0
        magnitude += 1
    
    return f"{number:.2f}{suffixes[magnitude]}".rstrip('0').rstrip('.')

def format_for_contract(token: dict) -> dict:
    """
    Preprocess the request JSON for Notion integration.
    
    Args:
        request_json (dict): The raw request JSON data
        
    Returns:
        dict: Processed data ready for Notion integration
    """
    try:
        writer = Notion().writer
        # Extract relevant data from request
        token['totalSupply'] = Function().totalSupply(CONTEXT[token['Network']], token['Address'])
        token['balanceOf'] = Function().balanceOf(CONTEXT[token['Network']], token['Address'])
        if token['Address'] == '0x51F5DC1c581e309D73E1c6Ea74176077b3c44e60':
            token['totalSupply'] = token['totalSupply']/1000
            token['balanceOf'] = token['balanceOf']/1000
        
        logger.info(f"[preprocess_for_notion] Processing data for ticker: {token['ticker']}")
        
        # Format properties for Notion
        properties = dict()
        properties['totalSupply'] = writer.number(token['totalSupply'])
        properties['balanceOf'] = writer.number(token['balanceOf'])
        visual_supply = human_readable_abbreviated(token['totalSupply'])
        visual_balance = round(token['balanceOf'], 5)
        properties['Actual Supply'] = writer.text(f"{visual_supply} {token['Name']}")
        properties['Actual Balance'] = writer.text(f"{visual_balance} {token['Name']}")
        page_id = token['page_id']
        wrapper = {'page_id': page_id, 'properties': properties}
        
        logger.info(f"[preprocess_for_notion] Successfully formatted data for Notion")
        return wrapper
        
    except Exception as e:
        logger.error(f"[preprocess_for_notion] Error processing data: {str(e)}")
        raise

def balance_of(request: Request):
    """
    Handle balance of token request and update Notion.
    
    Args:
        request (Request): Flask request object
        
    Returns:
        Response: JSON response with status
    """

    try:
        logger.info("[balance_of] Received new balance update request")
        
        request_json = request.get_json()
        if not request_json:
            logger.error("[balance_of] No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400
            
        # Preprocess data for Notion
        wrapper = format_for_contract(request_json)
        response = enqueue_contract(wrapper)
        logger.info("[balance_of] Sending data to Notion API")
        if response.status_code == 200:
            logger.info("[balance_of] Successfully updated Notion")
            return jsonify({"status": "success", "message": "Balance updated in Notion"}), 200
        logger.error(f"[balance_of] Failed to update Notion: {response.text}")
        return jsonify({"error": "Failed to update Notion", "details": response.text}), response.status_code
            
    except Exception as e:
        logger.error(f"[balance_of] Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500