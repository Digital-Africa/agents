from flask import Request, jsonify
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.Drive import Drive
from packages.Notion import Notion, NotionDatabase
from packages.Capsule import CapsuleNotion
from packages.Firestore import StorageDriveFolder
from packages.Tasks import Tasks

def create_folder(request: Request) -> Dict[str, Any]:
    # Initialize logger
    logger = CloudLogger("create_folder_function")
    logger.info("Starting create_folder function execution")
    
    try:
        requests = request.get_json(force=True)
        tiers_id = requests.get('tiers_id')
        folder_card = requests.get('folder_card')
        parent_id = requests.get('parent_id')
        
        logger.info("Processing folder creation request", extra={
            'tiers_id': tiers_id,
            'folder_name': folder_card['Name'],
            'parent_id': parent_id
        })
        
        collection_name = 'Folders'

        # Create Drive folder
        logger.info("Creating Drive folder", extra={'folder_name': folder_card['Name']})
        drive_document = Drive().create_folder(
            name=folder_card['Name'], 
            parent_id=folder_card['Drive Root'], 
            permissions_list=['mohamed.diabakhate@digital-africa.co']
        )
        
        if drive_document:
            logger.info("Drive folder created successfully", extra={'drive_url': drive_document['url']})
            
            # Create Notion page
            writer = Notion().writer
            properties = {
                'Drive': writer.url(drive_document['url']),
                'Tiers': writer.relation(tiers_id),
                'Name': writer.title(folder_card['Name']),
            }
            if parent_id:
                properties['Parent'] = writer.relation(parent_id)
                
            params = {
                'database': NotionDatabase().query('Folders')['id'],
                'properties': properties
            }
            
            logger.info("Creating Notion page", extra={'properties': properties})
            response = CapsuleNotion(**params).run()
            parent_id = response.json()['id']
            
            if response.status_code == 200:
                response = response.json()
                drive_document['Tiers'] = tiers_id
                
                # Update Firestore
                logger.info("Updating Firestore document", extra={'page_id': folder_card['page_id']})
                StorageDriveFolder().client_firestore.collection(collection_name).document(folder_card['page_id']).set(drive_document, merge=True)
                
                # Process child folders if any
                if folder_card['Child']:
                    logger.info("Processing child folders", extra={'child_count': len(folder_card['Child'])})
                    for child in folder_card['Child']:
                        child_card = StorageDriveFolder().client_firestore.collection('DriveFolders').document(child['id']).get().to_dict()
                        payload = {
                            'tiers_id': tiers_id,
                            'folder_card': child_card,
                            'parent_id': parent_id
                        }
                        task_payload = {
                            'url': 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/create_folder',
                            'payload': payload,
                            'queue': 'notion-queue'
                        }
                        logger.info("Enqueueing child folder task", extra={'child_id': child['id']})
                        Tasks().add_task(task_payload)
                else:
                    logger.info("No child folders to process")
                    return jsonify({'success': True, 'parent_id': parent_id}), 200
            else:
                error_msg = 'Failed to create Notion page'
                logger.error(error_msg, extra={'status_code': response.status_code, 'response': response.json()})
                return jsonify({'error': error_msg}), 500
        else:
            error_msg = 'Failed to create Drive folder'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        logger.error("Error in create_folder function", extra={'error': str(e)})
        return jsonify({'error': str(e)}), 500
