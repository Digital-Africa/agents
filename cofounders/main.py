import requests
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.Cofounders import Cofounders

# Initialize logger with more descriptive name
logger = CloudLogger("cofounders_service")

def cofounders(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process cofounders request and return response.
    
    Args:
        request (Dict[str, Any]): The incoming request data
        
    Returns:
        Dict[str, Any]: The processed response
    """
    try:
        logger.info("Starting cofounders request processing")
        
        # Make API request with proper error handling
        try:
            logger.debug("Fetching cofounder data")
            cofounder = requests.get("YOUR_API_ENDPOINT_HERE")  # Replace with actual endpoint
            cofounder.raise_for_status()  # Raise exception for bad status codes
        except requests.RequestException as e:
            logger.error(f"Failed to fetch cofounder data: {str(e)}")
            raise
            
        # Process the response
        logger.debug("Processing cofounder data")
        response = Cofounders(cofounder).run()
        
        logger.info("Successfully processed cofounders request")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in cofounders processing: {str(e)}")
        raise


