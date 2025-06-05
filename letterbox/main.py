import requests
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.Drive import Drive
from packages.Firestore import StorageDrive
from packages.Notion import Notion
from packages.Capsule import CapsuleNotion
from packages.Firestore import NotionDatabase
from google.cloud.firestore_v1 import FieldFilter

# Initialize logger with more descriptive name
logger = CloudLogger("cofounders_service")

def store_to_notion(response: Dict[str, Any], page_id: str) -> None:
    """
    Store the Google Drive file link in Notion.
    
    Args:
        response (Dict[str, Any]): The response from Google Drive containing file information
        page_id (str): The Notion page ID where the file link should be stored
    
    Returns:
        None
    """
    logger.info(f"Storing Drive link to Notion page {page_id}")
    properties = {}
    writer = Notion().writer
    properties['Drive'] = writer.url(response['webViewLink'])
    params = {
        'page_id': page_id,
        'database': NotionDatabase().query('Memo')['id'],
        'properties': properties,
    }
    CapsuleNotion(**params).enqueue()
    logger.info("Successfully stored Drive link in Notion")

def letterbox(request) -> Dict[str, Any]:
    """
    Process a letterbox request to store files from Notion to Google Drive.
    
    This function:
    1. Extracts file and folder information from the request
    2. Checks if the folder exists in Drive
    3. Creates the folder if it doesn't exist
    4. Stores the file in the appropriate folder
    5. Updates Notion with the Drive link if needed
    
    Args:
        request: The HTTP request containing file and folder information
        
    Returns:
        Dict[str, Any]: Response containing the operation status
        
    Raises:
        ValueError: If no file is found in the request
        Exception: For any other errors during processing
    """
    logger.info("Processing letterbox request")
    
    try:
        # Extract payload data
        payload = request.get_json()
        if not payload or 'data' not in payload:
            raise ValueError("Invalid request payload: missing data field")
            
        folder_name = payload.get('data', {}).get('properties', {}).get('Destination', "untitled_folder")
        logger.info(f"Processing folder: {folder_name}")
        
        # Extract startups pool information
        startups_pool = payload.get('data', {}).get('properties', {}).get('Startups Pool', {})
        if startups_pool.get('relation', {}):
            startups_pool = startups_pool.get('relation', {})[0].get('data', {})
            logger.info(f"Found startups pool: {startups_pool}")
        else:
            startups_pool = None
            logger.warning("No startups pool found in request")
        
        permissions_list = payload.get('data', {}).get('properties', {}).get('Permissions', {})
        page_id = payload.get('data', {}).get('id', {})
        
        # Extract file information
        file = payload.get('data', {}).get('properties', {}).get('Files & Media', {})
        if not file or 'files' not in file or not file['files']:
            logger.error("No file found in request")
            raise ValueError("No file found in request")
            
        file_name = file['files'][0]['name']
        file_url = file['files'][0]['file']['url']
        logger.info(f"Processing file: {file_name}")

        # Initialize services
        drive = Drive()
        db = StorageDrive()
        collection = db.collection_name
        
        # Check for existing folder
        doc = db.client_firestore.collection(collection).where(
            filter=FieldFilter("startups_pool", "==", startups_pool)
        ).get()

        if doc:
            doc = doc[0].to_dict()
            parent_id = doc['root']
            logger.info(f"Found existing folder with parent ID: {parent_id}")
        else:
            parent_id = "15KwWfF__TTOI8u3xvk2FbEOVn_E2cTVy"
            logger.info(f"Using default parent ID: {parent_id}")

        # Process file storage
        if drive.name_not_exists(folder_name):
            logger.info(f"Creating new folder: {folder_name}")
            doc = drive.create_folder(folder_name, parent_id, permissions_list)
            doc['startups_pool'] = startups_pool
            db.client_firestore.collection(collection).document(startups_pool).set(doc, merge=True)
            response = drive.store_notion_file_to_drive(file_url, file_name, doc['folder_id'])
            logger.info(f"Successfully created folder and stored file: {file_name}")
        else:
            logger.info(f"Using existing folder: {folder_name}")
            doc = db.client_firestore.collection(collection).document(startups_pool).get().to_dict()
            response = drive.store_notion_file_to_drive(file_url, file_name, doc['folder_id'])
            store_to_notion(response, page_id)
            logger.info(f"Successfully stored file in existing folder: {file_name}")
            
        return {
            "status": "success",
            "message": f"File {file_name} processed successfully",
            "folder_name": folder_name,
            "file_name": file_name
        }
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing request: {str(e)}")
        raise

