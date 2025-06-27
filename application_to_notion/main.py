import json
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.Cofounders import Cofounders
from packages.Startups import Startups

# Initialize logger with more descriptive name
logger = CloudLogger("Satori To Notion")
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
        request_data = request.get_json(force=True)
        target = request_data.get('target', None)
        data = request_data.get('data', None)
        data = json.loads(data)

        if target == 'cofounders':
            logger.debug(f"Processing cofounder data {target} {data}")            
            response = Cofounders(data).run()
            logger.info("Successfully processed cofounders request")
            return response
        elif target == 'startups':
            logger.debug(f"Processing startups data {target} {data}")
            response = Startups(data).run()
            logger.info("Successfully processed startups request")
            return response
        else:
            logger.debug("No cofounder data found or target not supported")
            return {"status": "error", "message": f"Target '{target}' not supported"}
    
    except Exception as e:
        logger.error(f"Unexpected error in cofounders processing: {str(e)}")
        return {"status": "error", "message": str(e)}


