import json
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.Cofounders import Cofounders
from packages.Startups import Startups

# Initialize logger with more descriptive name
logger = CloudLogger("cofounders_service")
HANDLERS = {
                "cofounders": lambda data: Cofounders(data).run(), 
                "startups": lambda data: Startups(data).run()
            }            


def application_to_notion(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process cofounders request and return response.
    
    Args:
        request (Dict[str, Any]): The incoming request data
        
    Returns:
        Dict[str, Any]: The processed response
    """
    try:
        logger.info("Starting cofounders request processing")
        
        # Extract cofounder from request params
        logger.debug("Extracting cofounder data from request")
        request_data = request.get_json(force=True)
        target = request_data.get('target', None)
        data = request_data.get('data', None)

        if target == 'cofounders':
            cofounder = json.loads(cofounder)
            response = Cofounders(data).run()
            logger.debug(f"Processing cofounder data {target} {data}")
            logger.info("Successfully processed cofounders request")
            return response
        elif target == 'startups':
            startups = json.loads(startups)
            response = Startups(startups).run()
            logger.debug(f"Processing startups data {target} {startups}")
            logger.info("Successfully processed startups request")
            return response
        else:
            logger.debug("No cofounder data found or target not supported")
            response = None
            return response
    
    except Exception as e:
        logger.error(f"Unexpected error in cofounders processing: {str(e)}")
        raise


