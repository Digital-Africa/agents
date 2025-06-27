import json
import pandas
import requests
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.storage import GCSStorage
# Initialize logger with more descriptive name
logger = CloudLogger("cofounders_service")

def  FUNCTION(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process cofounders request and return response.
    
    Args:
        request (Dict[str, Any]): The incoming request data
        
    Returns:
        Dict[str, Any]: The processed response
    """
    context = {'bucket_name': 'fuze-subscriptions','service_account_path': 'sa_keys/puppy-agent-memory-bank-key.json'}
    storage = GCSStorage(**context)
    try:
        logger.info("Starting cofounders request processing")
        
        # Make API request with proper error handling
        try:
            logger.debug("Fetching cofounder data")
            file = requests.get()  # Replace with actual endpoint
            file.raise_for_status()  # Raise exception for bad status codes
            file_ = storage.read_csv(**{'blob_name': file]})
            file_ = file_.iloc[1:].reset_index(drop=True).to_dict(orient='records')   
        except requests.RequestException as e:
            logger.error(f"Failed to fetch cofounder data: {str(e)}")
            raise
            
        # Process the response
        if 'cofounder' in file:
            logger.debug("Processing cofounder data")
            for f in file_:
                url  = 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/cofounders'
                params = {'cofounder': json.dumps(f)}
                response = requests.post(url, json=params)
        elif 'startup' in file:
            logger.debug("Processing startup data")
            for f in file_:
                url  = 'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/startups'
                params = {'cofounder': json.dumps(f)}
                response = requests.post(url, json=params)
        
        logger.info("Successfully processed cofounders request")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in cofounders processing: {str(e)}")
        raise


