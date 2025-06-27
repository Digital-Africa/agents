from typing import Dict, Optional, Any, List
from flask import Request
from google.cloud.firestore_v1 import FieldFilter
import functions_framework
from google.cloud import firestore
import uuid
import traceback
import json


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
        """Extract and validate data from the request with minimal memory usage."""
        try:
            request_data = request.get_json(force=True).get('data')
            if not request_data:
                self.logger.error("Request validation failed - no data found", extra={
                    'request_id': request.headers.get('X-Request-ID', 'unknown')
                })
                raise ValueError("No data found in request")
            
            # Extract only needed fields
            return {
                'Tiers': request_data['properties']['Tiers']['title'][0]['plain_text'],
                #'Drive': request_data['properties']['Drive']['url'],
                'request_person': request_data['properties']['Person Request']['people'][0]['id'],
                'page_id': request_data['id']
            }
        except KeyError as e:
            self.logger.error("Request validation failed - missing required field", extra={
                'request_id': request.headers.get('X-Request-ID', 'unknown'),
                'missing_field': str(e)
            })
            raise ValueError(f"Missing required field: {str(e)}")
    
    def _create_drive_folder(self, tiers_name: str, root: str, permissions_list: List[str]) -> Dict[str, Any]:
        """Create a folder in Google Drive."""
        request_id = self.logger.request_id
        self.logger.info("Initiating Drive folder creation", extra={
            'request_id': request_id,
            'tiers_name': tiers_name,
            'root_folder_id': root,
            'permissions_count': len(permissions_list),
            'permissions_list': permissions_list
        })
        try: 
            drive_document = self.drive.create_folder(tiers_name, root, permissions_list)
            self.logger.info("Drive folder creation successful", extra={
                'request_id': request_id,
                'folder_id': drive_document['folder_id'],
                'folder_url': drive_document['url']
            })
            return drive_document
        except Exception as e:
            self.logger.error("Drive folder creation failed", extra={
                'request_id': request_id,
                'error': str(e),
                'error_type': type(e).__name__,
                'tiers_name': tiers_name,
                'root_folder_id': root,
                'stack_trace': traceback.format_exc()
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
        """Add a document to Firestore with minimal data."""
        request_id = self.logger.request_id
        try:
            collection_name = 'Tiers'
            # Only store essential fields
            essential_data = {
                'page_id': payload['page_id'],
                'Tiers': payload.get('Tiers'),
                'Drive': payload.get('url'),
                'Contract': [],
                'folder_id': payload.get('folder_id')
            }
            
            self.storage.client_firestore.collection(collection_name).document(payload['page_id']).set(essential_data, merge=True)
            return 'ok'
        except Exception as e:
            self.logger.error("Failed to add document to Firestore", extra={
                'request_id': request_id,
                'error': str(e)
            })
            raise
    
    def notion_update_tiers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update a document in Notion with minimal data."""
        request_id = self.logger.request_id
        try:
            writer = self.notion.writer            
            # Only include essential properties
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
            
            notion_response = CapsuleNotion(**params).run()
            return notion_response.json()
        except Exception as e:
            self.logger.error("Failed to update tiers in Notion", extra={ 
                'request_id': request_id,
                'error': str(e)
            })
            raise

    def send_slack_message(self, request_person, message):
        request_id = self.logger.request_id
        try:
            self.logger.info("Sending Slack message", extra={
                'request_id': request_id,
                'request_person': request_person,
                'message_length': len(message)
            })
            
            user_id = Person().query_notion_id(request_person)
            SlackAPI().send_direct_message(user_id['slack_id'], message)
            
            self.logger.info("Successfully sent Slack message", extra={
                'request_id': request_id,
                'request_person': request_person,
                'slack_user_id': user_id['slack_id']
            })
        except Exception as e:
            self.logger.error("Failed to send Slack message", extra={
                'request_id': request_id,
                'error': str(e),
                'error_type': type(e).__name__,
                'request_person': request_person,
                'stack_trace': traceback.format_exc()
            })
            raise

@functions_framework.http
def tiers_card(request: Request) -> Dict[str, Any]:
    """Cloud Function with optimized memory usage."""
    request_id = str(uuid.uuid4())
    logger = CloudLogger("tiers_card", 'tiers_card').logger
    logger.request_id = request_id
    
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
        
        # Create drive folder only if needed
        permissions_list = []
        drive_document = manager.drive.create_folder(payload['Tiers'], root, permissions_list)
        payload.update(drive_document)
        
        # Update Notion and Firestore
        notion_response = manager.notion_update_tiers(payload)
        payload['tiers_notion_id'] = notion_response['id']
        manager.firestore_add_tiers_card(payload)

        # Send minimal Slack message
        manager.send_slack_message(
            payload['request_person'], 
            f"Tiers folders created for {payload['Tiers']}\n{drive_document['url']}"
        )
        
        return (notion_response, 200, headers)
                    
    except ValueError as e:
        logger.error("Validation error", extra={'error': str(e)})
        return ({'error': str(e)}, 400, headers)
    except Exception as e:
        logger.error("Unexpected error", extra={'error': str(e)})
        return ({'error': 'Internal server error'}, 500, headers)