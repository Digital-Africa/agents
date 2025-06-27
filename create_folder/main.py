from flask import Request, jsonify
from typing import Dict, Any, Optional
from google.cloud.firestore_v1 import FieldFilter
from packages.Logging import CloudLogger
from packages.Drive import Drive
from packages.Notion import Notion
from packages.Capsule import CapsuleNotion
from packages.Firestore import StorageDriveFolder, NotionDatabase
from packages.Tasks import Tasks
import uuid
import json

class FolderCreator:
    def __init__(self, request: Request):
        self.logger = CloudLogger("create_folder_function", 'create_function')
        self.request_data = request.get_json(force=True)
        self.tiers_id = self.request_data.get('tiers_id')
        self.folder_card = self.request_data.get('folder_card')
        self.parent_id = self.request_data.get('parent_id')
        self.collection_name = 'Folders'
        self.drive = Drive()
        self.notion_writer = Notion().writer
        self.firestore = StorageDriveFolder().client_firestore

    def create_drive_folder(self) -> Optional[Dict[str, Any]]:
        """Create a folder in Google Drive."""
        try:
            _card_ = self.drive.name_not_exists(self.folder_card['name'], self.parent_id)
            if _card_:
                self.logger.info(f"Drive folder {self.folder_card['name']} already exists", extra={'_card_': _card_})
                # Handle case where _card_ is a list containing a dictionary
                if isinstance(_card_, list) and len(_card_) > 0:
                    _card_ = _card_[0]  # Take the first item from the list
                
                if isinstance(_card_, dict):
                    _card_['url'] = f"https://drive.google.com/drive/folders/{_card_['id']}"
                else:
                    self.logger.error(f"Unexpected _card_ type after processing: {type(_card_)}", extra={'_card_': _card_})
                    return None
                return _card_
            
            else:
                self.logger.info("Creating Drive folder", extra={'folder_name': self.folder_card['name']})
                drive_document = self.drive.create_folder(
                    name=self.folder_card['name'],
                    parent_id=self.parent_id,
                    permissions_list=['mohamed.diabakhate@digital-africa.co']
                )
                if not drive_document:
                    self.logger.error(f'Failed to create Drive folder {self.folder_card["name"]}')
                    return None
                
                # Handle case where drive_document is a list containing a dictionary
                if isinstance(drive_document, list) and len(drive_document) > 0:
                    drive_document = drive_document[0]  # Take the first item from the list
                
                if not isinstance(drive_document, dict):
                    self.logger.error(f"Unexpected drive_document type: {type(drive_document)}", extra={'drive_document': drive_document})
                    return None
                    
                self.logger.info("Drive folder created successfully", extra={'drive_url': drive_document['url']})
                return drive_document
        except Exception as e:
            self.logger.error(f"Error in create_drive_folder: {str(e)}", extra={'error_details': str(e), 'folder_card': self.folder_card})
            raise

    def create_notion_page(self, drive_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a page in Notion."""
        try:
            if not isinstance(drive_document, dict):
                self.logger.error(f"Invalid drive_document type: {type(drive_document)}", extra={'drive_document': drive_document})
                return None

            properties = {
                'Drive': self.notion_writer.url(drive_document['url']),
                'Tiers': self.notion_writer.relation(self.tiers_id),
                'Name': self.notion_writer.title(self.folder_card['name']),
            }
            
            if self.parent_id:
                try:
                    parent_page_id = self.firestore.collection('Folders').where(filter=FieldFilter('folder_id', '==', self.parent_id)).get()
                    self.logger.info("Parent page query result", extra={'parent_page_id': parent_page_id})
                    if parent_page_id and len(parent_page_id) > 0:
                        properties['Parent'] = self.notion_writer.relation(parent_page_id[0].id)
                    else:
                        self.logger.warning("No parent page found", extra={'parent_id': self.parent_id})
                except Exception as e:
                    self.logger.error(f"Error querying parent page: {str(e)}", extra={'parent_id': self.parent_id})
                    raise
                
            params = {
                'database': NotionDatabase().query('Folders')['id'],
                'properties': properties,
                'task_name': f'create_folder_{uuid.uuid4()}'
            }
            
            self.logger.info("Creating Notion page", extra={'properties': properties})
            response = CapsuleNotion(**params).run()
            
            if response.status_code != 200:
                self.logger.error('Failed to create Notion page', 
                                extra={'status_code': response.status_code, 'response': response.json()})
                return None
                
            return response.json()
        except Exception as e:
            self.logger.error(f"Error in create_notion_page: {str(e)}", extra={'error_details': str(e), 'drive_document': drive_document})
            raise

    def process_child_folders(self, notion_parent_id: str) -> None:
        """Process child folders if they exist."""
        try:
            if not self.folder_card.get('child'):
                self.logger.info("No child folders to process")
                return

            self.logger.info("Processing child folders", 
                            extra={'child_count': len(self.folder_card['child'])})
            
            for child in self.folder_card['child']:
                try:
                    child_card = self.firestore.collection('DriveFolders').document(child).get().to_dict()
                    self.logger.info("Retrieved child card", extra={'child_id': child, 'child_card': child_card})
                    
                    payload = {
                        'tiers_id': self.tiers_id,
                        'folder_card': child_card,
                        'parent_id': notion_parent_id
                    }
                    
                    task_payload = {
                        'url': 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/create_folder',
                        'payload': payload,
                        'queue': 'notion-queue'
                    }
                    
                    task_name = f'create_folder_child_{uuid.uuid4()}'
                    self.logger.info("Enqueueing child folder task", extra={'child_id': child})
                    Tasks().add_task(task_payload, task_name)
                except Exception as e:
                    self.logger.error(f"Error processing child folder: {str(e)}", extra={'child': child, 'error_details': str(e)})
                    raise
        except Exception as e:
            self.logger.error(f"Error in process_child_folders: {str(e)}", extra={'error_details': str(e), 'notion_parent_id': notion_parent_id})
            raise

    def execute(self) -> tuple[Dict[str, Any], int]:
        """Main execution flow."""
        try:
            self.logger.info("Starting create_folder function execution")
            self.logger.info("Processing folder creation request", extra={
                'tiers_id': self.tiers_id,
                'folder_name': self.folder_card['name'],
                'parent_id': self.parent_id
            })

            # Create Drive folder
            try:
                drive_document = self.create_drive_folder()
                if not drive_document:
                    return jsonify({'error': 'Failed to create Drive folder'}), 500
            except Exception as e:
                self.logger.error(f"Error in drive folder creation: {str(e)}")
                raise

            # Create Notion page
            try:
                notion_response = self.create_notion_page(drive_document)
                if not notion_response:
                    return jsonify({'error': 'Failed to create Notion page'}), 500
            except Exception as e:
                self.logger.error(f"Error in notion page creation: {str(e)}")
                raise

            # Update Firestore
            try:
                drive_document['Tiers'] = self.tiers_id
                self.logger.info("Updating Firestore document", 
                               extra={'page_id': self.folder_card['page_id']})
                self.firestore.collection(self.collection_name).document(
                    self.folder_card['page_id']
                ).set(drive_document, merge=True)
            except Exception as e:
                self.logger.error(f"Error updating Firestore: {str(e)}")
                raise

            # Process child folders
            try:
                self.process_child_folders(notion_response['id'])
            except Exception as e:
                self.logger.error(f"Error processing child folders: {str(e)}")
                raise
            
            return jsonify({'success': True, 'parent_id': notion_response['id']}), 200

        except Exception as e:
            self.logger.error("Error in create_folder function", extra={'error': str(e), 'error_type': type(e).__name__})
            return jsonify({'error': str(e)}), 500

def create_folder(request: Request) -> Dict[str, Any]:
    """Entry point for the create_folder function."""
    folder_creator = FolderCreator(request)
    return folder_creator.execute()
