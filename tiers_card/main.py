from typing import Dict, Optional, Any, List
from flask import Request
from google.cloud.firestore_v1 import FieldFilter
import functions_framework
from google.cloud import firestore

from packages.Notion import Notion
from packages.Firestore import StorageDriveFolder, NotionDatabase, Person
from packages.Capsule import CapsuleNotion
from packages.Logging import CloudLogger
from packages.Drive import Drive


class TiersCardManager:
    """Manages the creation and handling of tier cards in Notion and Firestore.
    
    This class encapsulates all the logic for creating and managing tier cards,
    including folder creation in Google Drive, Notion page creation, and Firestore storage.
    """
    
    def __init__(self, logger: Any):
        """Initialize the TiersCardManager.
        
        Args:
            logger (Any): Logger instance for structured logging
        """
        self.logger = logger
        self.notion = Notion()
        self.storage = StorageDriveFolder()
        self.drive = Drive()
        self.person = Person()
    
    def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract and validate data from the request.
        
        Args:
            request (Request): Flask request object
            
        Returns:
            Dict[str, Any]: Processed request data
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            request_data = request.get_json(force=True).get('data')
            if not request_data:
                raise ValueError("No data found in request")
                
            drive_url = request_data['properties']['Drive']['url']
            tiers_name = request_data['properties']['Tiers']['title'][0]['plain_text']
            
            return {
                'Tiers': tiers_name,
                'Drive': drive_url,
                'page_id': request_data['id']
            }
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
    
    def _create_drive_folder(self, tiers_name: str, root: str, permissions_list: List[str]) -> Dict[str, Any]:
        """Create a folder in Google Drive.
        
        Args:
            tiers_name (str): Name of the tiers folder
            root (str): Root folder ID
            permissions_list (List[str]): List of email addresses to grant permissions
            
        Returns:
            Dict[str, Any]: Created drive folder details
        """
        self.logger.info("Creating Drive folder", extra={
            'tiers_name': tiers_name,
            'root': root
        })
        return self.drive.create_folder(tiers_name, root, permissions_list)
    
    def create_tiers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tiers folder in Notion and Firestore.
        
        Args:
            payload (Dict[str, Any]): Dictionary containing tier card data
            
        Returns:
            Dict[str, Any]: Response from Notion API
            
        Raises:
            Exception: If creation fails
        """
        try:
            writer = self.notion.writer
            collection_name = 'Tiers'
            
            properties = {
                "_self_": writer.relation(payload['page_id']),
                'id': writer.text(payload['page_id']),
                'Drive': writer.url(payload['url'])
            }

            params = {
                'page_id': payload['page_id'],
                'database': NotionDatabase().query('Tiers')['id'],
                'properties': properties
            }
                    
            self.logger.info("Creating tiers folder", extra={
                'page_id': payload['page_id'],
                'tiers_name': payload.get('Tiers')
            })
            payload['Contract'] = []
            self.storage.client_firestore.collection(collection_name).document(payload['page_id']).set(payload, merge=True)
            response = CapsuleNotion(**params).run()
            
            self.logger.info("Successfully created tiers folder", extra={
                'page_id': payload['page_id'],
                'response': response.json()
            })
            return response.json()
            
        except Exception as e:
            self.logger.error("Error creating tiers folder", extra={
                'error': str(e),
                'payload': payload
            })
            raise


@functions_framework.http
def tiers_card(request: Request) -> Dict[str, Any]:
    """Cloud Function to handle tier card creation in Notion and Firestore.
    
    This function processes incoming requests to create tier cards. It:
    1. Extracts and validates the request data
    2. Creates the tiers folder if needed
    3. Creates the corresponding Notion page
    
    Args:
        request (Request): Flask request object containing tier card data
    
    Returns:
        Dict[str, Any]: Response from Notion API
        
    Raises:
        Exception: If processing fails
    """
    logger = CloudLogger("tiers_card").logger
    logger.info("Starting tiers_card function execution")
    
    try:
        # Add CORS headers for browser requests
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)

        # Set CORS headers for the main request
        headers = {
            'Access-Control-Allow-Origin': '*'
        }
        
        manager = TiersCardManager(logger)
        payload = manager._extract_request_data(request)
        root = request.headers.get("X-root")
        
        if payload['Drive'] is None:
            permissions_list = []
            drive_document = manager._create_drive_folder(payload['Tiers'], root, permissions_list)
            payload = payload | drive_document
            response = manager.create_tiers(payload)
            payload['tiers_notion_id'] = response['id']
            logger.info("Successfully completed tiers_card function")
            return (response, 200, headers)
        else:
            error_msg = 'Drive URL already exists'
            logger.error(error_msg, extra={'payload': payload})
            return ({'error': error_msg}, 400, headers)
            
    except ValueError as e:
        logger.error("Validation error in tiers_card function", extra={
            'error': str(e),
            'request_data': request.get_json(force=True) if request.is_json else None
        })
        return ({'error': str(e)}, 400, headers)
    except Exception as e:
        logger.error("Error in tiers_card function", extra={
            'error': str(e),
            'request_data': request.get_json(force=True) if request.is_json else None
        })
        return ({'error': 'Internal server error'}, 500, headers)