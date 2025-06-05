import requests
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.storage import GCSStorage
# Initialize logger with more descriptive name
logger = CloudLogger("cofounders_service")
            

def files(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process cofounders request and return response.
    
    Args:
        request (Dict[str, Any]): The incoming request data
        
    Returns:
        Dict[str, Any]: The processed response
    """
    try:
        logger.info("Starting storage request")
        # Make API request with proper error handling
        try:
            logger.debug("Fetching files")
            context = {'bucket_name': 'fuze-subscriptions','service_account_path': 'sa_keys/puppy-agent-memory-bank-key.json'}
            storage = GCSStorage(**context)
            params = {'prefix': ''}
            blobs = storage.list_new_files(**params)

            raw_files = set(filter(lambda x: 'processed_files/' not in x, blobs))
            processed_files = set(e.split('/')[1] for e in filter(lambda x: 'processed_files/' in x, blobs))
            queue = raw_files.difference(processed_files)
            startups_files = list(filter(lambda x: 'startups' in x, queue))
            cofounders_files = list(filter(lambda x: 'cofounders' in x, queue))
            logger.info(f"{len(startups_files)} startup_files and {len(cofounders_files)} cofounders_files")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data: {str(e)}")
            raise
            
        # Send to dispatch
        logger.debug("Processing cofounder data")
        
        v = Cofounders(cofounder).run()
        response = Cofounders(cofounder).run()
        
        logger.info("Successfully processed cofounders request")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in cofounders processing: {str(e)}")
        raise


