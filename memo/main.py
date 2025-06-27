import requests
from typing import Dict, Any
from packages.Logging import CloudLogger
from packages.PitchDesc import PitchDesc
from packages.Logo import Logo
from packages.KBIS import kbis

# Initialize logger with more descriptive name and structured logging
logger = CloudLogger("pitch_desc_service")

def memo(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process cofounders request and return response.
    
    This function handles the main business logic for processing pitch description requests.
    It makes an API call to fetch pitch data and processes it using the PitchDesc service.
    
    Args:
        request (Dict[str, Any]): The incoming request data containing:
            - Required fields for pitch description processing
            - Any additional metadata or parameters
            
    Returns:
        Dict[str, Any]: The processed response containing:
            - Processed pitch description
            - Status information
            - Any additional metadata
            
    Raises:
        requests.RequestException: If the API request fails
        Exception: For any unexpected errors during processing
    """
    try:
        # Log request details with correlation ID for tracing
        logger.info("Starting pitch description request processing")
        
        # Make API request with proper error handling and timeout
        try:
            logger.debug("Initiating pitch description API request") 
            request= request.get_json(force=True)
            payload = request.get('data')
            logger.debug("Successfully fetched pitch description payload")
                        #extra={'status_code': payload.status_code})

            #payload.raise_for_status()
            
        except requests.RequestException as e:
            logger.error("Failed to fetch pitch description", 
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'status_code': getattr(e.response, 'status_code', None)
                        })
            raise
            
        # Process the response
        logger.debug("Processing pitch description")
        response = {}
        response['pitch_desc'] = PitchDesc(payload).run()
        logger.info("Successfully processed pitch description request", 
        extra={'response': response})
        response['logo'] = Logo(payload).run()
        logger.info("Successfully processed logo request", 
        extra={'response': response})
        response['kbis'] = kbis(payload).run()
        logger.info("Successfully processed kbis request", 
        extra={'response': response})
        return response

    except Exception as e:
        logger.error("Unexpected error in pitch description processing", 
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'stack_trace': str(e.__traceback__)
                    })
        raise
