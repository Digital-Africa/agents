import requests
from typing import Dict, Any, Optional, List
from packages.Logging import CloudLogger
from packages.Firestore import NotionDatabase, Person
from packages.Slack import get_slack_person_id
from packages.Affinity import Affinity
from packages.Notion import Notion
from packages.Capsule import CapsuleNotion
from flask import Request

# Initialize logger with more descriptive name
logger = CloudLogger("people_onboarding_service")

class ProcessingError(Exception):
    """Custom exception for processing errors."""
    pass

def publish(payload: Dict[str, Any]) -> bool:
    """Process and publish a single person's data to various services.

    Args:
        payload (Dict[str, Any]): Dictionary containing person data from Notion.

    Returns:
        bool: True if processing was successful, False otherwise.

    Raises:
        ProcessingError: If there's an error processing the person's data.
    """
    # Initialize p outside the try block so it's available in the error handling
    p = {'notion_id': 'unknown', 'email': 'unknown'}
    try:
        # Validate payload structure
        if not payload.get('data', {}).get('properties', {}).get('Person', {}).get('people'):
            raise ProcessingError("Invalid payload structure: missing Person data")

        people_ids = payload['data']['properties']['Person']['people'][0]
        
        if not people_ids.get('person', {}).get('email'):
            raise ProcessingError("Invalid payload structure: missing email")

        p = {
                'notion_id': people_ids['id'],
                'email': people_ids['person']['email']
            }
        
        # Log processing of each person
        logger.info("Processing person", 
                   extra={
                       "notion_id": p['notion_id'], 
                       "email": p['email'],
                       "operation": "process"
                   })

        if not Person().query_email(p['email']):
            # Log new person found
            logger.info("New person found", 
                       extra={
                           "notion_id": p['notion_id'], 
                           "email": p['email'],
                           "operation": "new_person"
                       })
            
            try:
                p['slack_id'] = get_slack_person_id(p['email'])
                p['affinity_id'] = Affinity().get_affinity_person_id(p['email'])
                
                # Log successful ID retrievals
                logger.info("Retrieved external IDs", 
                           extra={
                               "slack_id": p['slack_id'], 
                               "affinity_id": p['affinity_id'],
                               "operation": "id_retrieval"
                           })
            except Exception as e:
                logger.error("Failed to retrieve external IDs",
                           extra={
                               "error": str(e),
                               "email": p['email'],
                               "operation": "id_retrieval"
                           })
                raise ProcessingError(f"Failed to retrieve external IDs: {str(e)}")
            
            try:
                Person().update_collection(p)
            except Exception as e:
                logger.error("Failed to update person collection",
                           extra={
                               "error": str(e),
                               "email": p['email'],
                               "operation": "update_collection"
                           })
                raise ProcessingError(f"Failed to update person collection: {str(e)}")
            
            try:
                writer = Notion().writer
                params = {
                    'page_id': people_ids['id'],
                    'database': NotionDatabase().query('internal_team')['id'],
                    'properties': {
                        'affinity_id': writer.number(int(p['affinity_id'])),
                        'slack_id': writer.text(p['slack_id']),
                        'notion_id': writer.text(p['notion_id']),
                        'Email': writer.email(p['email'])
                    }
                }
                
                CapsuleNotion(**params).enqueue()
            except Exception as e:
                logger.error("Failed to enqueue to Capsule",
                           extra={
                               "error": str(e),
                               "email": p['email'],
                               "operation": "capsule_enqueue"
                           })
                raise ProcessingError(f"Failed to enqueue to Capsule: {str(e)}")
            
            # Log successful processing
            logger.info("Successfully processed and enqueued person",
                       extra={
                           "email": p['email'],
                           "operation": "complete"
                       })
            return True
        else:
            logger.info("Person already exists in database",
                       extra={
                           "email": p['email'],
                           "operation": "skip"
                       })
            return True
            
    except ProcessingError:
        raise
    except Exception as e:
        logger.error("Unexpected error processing person",
                    extra={
                        "error": str(e),
                        "email": p['email'],
                        "notion_id": p['notion_id'],
                        "operation": "unexpected_error",
                        "payload": str(payload)  # Log the payload for debugging
                    })
        return False


def people_onboarding(request: Request) -> Dict[str, Any]:
    """Process and onboard new team members from Notion to various integrated services.

    This cloud function synchronizes team member data between Notion and other services
    (Slack, Affinity, Capsule). It identifies new team members in Notion, retrieves their
    corresponding IDs from other services, and updates the Notion database with this
    information.

    Args:
        request (Request): The Flask HTTP request object.

    Returns:
        Dict[str, Any]: A dictionary containing the processing results:
            - status (str): 'success' if the process completed without fatal errors
            - processed (int): Number of successfully processed records
            - errors (int): Number of records that encountered errors

    Raises:
        Exception: If a fatal error occurs during the process that prevents continuation
    """
    # Log function invocation
    logger.info("Starting people onboarding process", 
                extra={"request_id": request.headers.get("X-Request-ID", "unknown")})
    
    try:
        # Get request data
        request_json = request.get_json(silent=True)
        
        # Check if this is a single person request
        try:           
            result = publish(request_json)
            
        except Exception as e:
            logger.error("Error processing request payload",
                        extra={"error": str(e)})
            raise

        # Log final summary
        logger.info("People onboarding process completed", 
                   extra={
                       "sucess": result
                   })
        
        return {
                "status": "success"
                }
        
    except Exception as e:
        logger.error("Fatal error in people onboarding process", 
                    extra={"error": str(e)})
        raise
