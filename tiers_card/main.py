from typing import Dict, Optional, Any, List
from flask import Request
from google.cloud.firestore_v1 import FieldFilter
import functions_framework
from google.cloud import firestore
import uuid


from packages.Notion import Notion
from packages.Firestore import StorageDriveFolder, NotionDatabase, Person
from packages.Capsule import CapsuleNotion
from packages.Logging import CloudLogger
from packages.Drive import Drive
from packages.Slack import SlackAPI


class TiersCardManager:
    """Manages the creation and handling of tier cards in Notion and Firestore.
    
    This class encapsulates all the logic for creating and managing tier cards,
    including folder creation in Google Drive, Notion page creation, and Firestore storage.
    """
    
    def __init__(self, logger: Any):
        """Initialize the TiersCardManager with lazy loading."""
        self.logger = logger
        self._notion = None
        self._storage = None
        self._drive = None
        self._person = None
    
    @property
    def notion(self):
        """Lazy load Notion client."""
        if self._notion is None:
            self._notion = Notion()
        return self._notion

    @property
    def storage(self):
        """Lazy load Storage client."""
        if self._storage is None:
            self._storage = StorageDriveFolder()
        return self._storage

    @property
    def drive(self):
        """Lazy load Drive client."""
        if self._drive is None:
            self._drive = Drive()
        return self._drive

    @property
    def person(self):
        """Lazy load Person client."""
        if self._person is None:
            self._person = Person()
        return self._person

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
                
            # Extract only needed fields to reduce memory usage
            return {
                'Tiers': request_data['properties']['Tiers']['title'][0]['plain_text'],
                'Drive': request_data['properties']['Drive']['url'],
                'request_person': request_data['properties']['Person Request']['people'][0]['id'],
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
            'root': root,
            'permissions_count': len(permissions_list)
        })
        try: 
            drive_document = self.drive.create_folder(tiers_name, root, permissions_list)
            self.logger.info("Successfully created drive folder ", extra={
                'folder_id': drive_document['folder_id']
            })
            return drive_document
        except Exception as e:
            self.logger.error("Error creating drive folder", extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'payload': tiers_name,
                'stack_trace': str(e.__traceback__)
            })
            raise
    
    def create_tiers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tiers folder with optimized memory usage."""
        try:
            writer = self.notion.writer
            collection_name = 'Tiers'
            
            # Create minimal properties object
            properties = {
                "_self_": writer.relation(payload['page_id']),
                'id': writer.text(payload['page_id']),
                'Drive': writer.url(payload['url'])
            }

            # Store in Firestore with minimal data
            self.storage.client_firestore.collection(collection_name).document(payload['page_id']).set({
                'page_id': payload['page_id'],
                'Tiers': payload.get('Tiers'),
                'Drive': payload.get('url'),
                'Contract': []
            }, merge=True)

            # Create Notion page
            response = CapsuleNotion(
                page_id=payload['page_id'],
                database=NotionDatabase().query('Tiers')['id'],
                properties=properties
            ).run()
            
            return response.json()
            
        except Exception as e:
            self.logger.error("Error creating tiers folder", extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'stack_trace': str(e.__traceback__)
            })
            raise
    
    def firestore_add_tiers_card(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add a document to Firestore.
        
        Args:
            payload (Dict[str, Any]): Dictionary containing document data
            
        Returns:
            Dict[str, Any]: Response from Firestore
        """
        try:
            collection_name = 'Tiers'
            self.storage.client_firestore.collection(collection_name).document(payload['page_id']).set(payload, merge=True)
            self.logger.info("[Firestore] Successfully added document to Firestore", extra={
                    'page_id': payload['page_id'],
                    'collection_name': collection_name
                })
            return 'ok'
        except Exception as e:
            self.logger.error("[Firestore] Error adding document to Firestore", extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'payload': payload,
                'stack_trace': str(e.__traceback__)
            })
            raise
    
    def notion_update_tiers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update a document in Notion.
        
        Args:
            payload (Dict[str, Any]): Dictionary containing document data
            
        Returns:
            Dict[str, Any]: Response from Notion API
        """
        try:
            writer = self.notion.writer            
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
            
            self.logger.info("[Notion] Updating tiers in Notion", extra={
                'page_id': payload['page_id'],
                'tiers_name': payload.get('Tiers'),
                'database_id': params['database']
            })
            notion_response = CapsuleNotion(**params).run()
            self.logger.info("[Notion] Successfully updated tiers in Notion", extra={
                'page_id': payload['page_id'],
                'response_id': notion_response.json().get('id'),
                'response_status': notion_response.status_code
            })
            return notion_response.json()
        except Exception as e:
            self.logger.error(f"[Notion] Error updating tiers in Notion {e}", extra={ 
                'error': str(e),
                'error_type': type(e).__name__,
                'payload': payload,
                'stack_trace': str(e.__traceback__)
            })
            raise

    def send_slack_message(self, request_person, message):
        try:
            user_id = Person().query_notion_id(request_person)
            SlackAPI().send_direct_message(user_id['slack_id'], message)
        except Exception as e:
            self.logger.error(f"[Slack] Error sending direct message {e}", extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'payload': request_person,
                'stack_trace': str(e.__traceback__)
            })
            raise

@functions_framework.http
def tiers_card(request: Request) -> Dict[str, Any]:
    """Cloud Function with optimized memory usage."""
    request_id = str(uuid.uuid4())
    logger = CloudLogger("tiers_card").logger
    
    try:
        # Handle CORS
        if request.method == 'OPTIONS':
            return ('', 204, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            })

        headers = {'Access-Control-Allow-Origin': '*'}
        
        # Process request with minimal memory footprint
        manager = TiersCardManager(logger)
        payload = manager._extract_request_data(request)
        root = request.headers.get("X-root")
        
        if payload['Drive'] is None:
            # Create drive folder only if needed
            permissions_list = []
            drive_document = manager.drive.create_folder(payload['Tiers'], root, permissions_list)
            payload.update(drive_document)
            response = manager.create_tiers(payload)
            payload['tiers_notion_id'] = response['id']
            manager.send_slack_message(payload['request_person'], f"Tiers folders created and unique id generated for {payload['Tiers']}\n\n{drive_document['url']}")
            return (response, 200, headers) 
        else:
            return ({'error': 'Drive URL already exists'}, 400, headers)
            
    except ValueError as e:
        return ({'error': str(e)}, 400, headers)
    except Exception as e:
        logger.error("Error in tiers_card function", extra={
            'request_id': request_id,
            'error': str(e),
            'error_type': type(e).__name__
        })
        return ({'error': 'Internal server error'}, 500, headers)