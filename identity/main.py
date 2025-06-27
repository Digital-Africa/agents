import requests
from typing import Dict, Any, List, Optional
from packages.Logging import CloudLogger
from packages.Capsule import CapsuleNotion
from packages.Notion import Notion
from packages.storage import Operation, Reference

# Initialize logger with function name
logger = CloudLogger("identity")

# Constants
#['Memo', 'zone_invest', 'startups_pool', 'zone_platform']
MONITORED_DATABASES = ['fe5715570ac747a4aa5452cc3cc9e628', '67853899c6ff4e78aeb2f25b0875b601', '9c0c831726e34ff99de32607e779d2c3', '96a2609ee4e44a01ae4841dd03672bc4']
class SelfNotion:
    """Handles self-referential updates for Notion pages."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize SelfNotion with page data.
        
        Args:
            data (Dict[str, Any]): The Notion page data
        """
        self.data = data
        self.writer = Notion().writer
        self.capsule = self.build()
        self.database = self.data['parent']['database_id']

    def build(self) -> Dict[str, Any]:
        """
        Build the properties dictionary for the Notion update.
        
        Returns:
            Dict[str, Any]: Properties dictionary for the update
        """
        properties = {}
        properties['_self_'] = self.writer.relation(self.data['id'])
        return properties
    
    def run(self) -> Any:
        """
        Execute the Notion page update.
        
        Returns:
            Any: Response from the update operation
        """
        try:
            icon_url = self.data['icon']['external']['url']
        except (KeyError, AttributeError):
            icon_url = None
            
        params = {
            'database': self.database,
            'properties': self.capsule,
            'page_id': self.data['id'],
            'icon': icon_url
        }
        return CapsuleNotion(**params).enqueue()

def identity(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process identity update request and return response.
    
    Args:
        request (Dict[str, Any]): The incoming request data
        
    Returns:
        Dict[str, Any]: The processed response
        
    Raises:
        requests.RequestException: If there's an error with the API request
        Exception: For any other unexpected errors
    """
    try:
        logger.info("Starting identity processing")
        try:
            # handle webhook request
            db_target = request.headers.get("X-database")
        except:
            # handle direct request
            db_target = 'all'

        # Configure database filter
        filter_ = {
                    "property": "_self_",
                    "relation": {
                                    "is_empty": True
                                }
                    }
        
        # Initialize Notion client and get database references
        notion_client = Notion()
        # Collect pages that need updating
        pages: List[Dict[str, Any]] = []
        if db_target == 'all':
            for db_id in MONITORED_DATABASES:
                try:
                    db_pages = notion_client.pull.query_database(db_id, filter_)
                    pages.extend(db_pages['results'])
                except KeyError as e:
                    logger.warning(f"{db_pages} {db_id} not found: {str(e)}")
                    continue
                except requests.RequestException as e:
                    logger.error(f"Failed to query database {db_id}: {str(e)}")
                    continue
            logger.info(f"Ran for all - Found {len(pages)} pages requiring updates")

        else:
            try:
                db_pages = notion_client.pull.query_database(db_target, filter_)
                pages.extend(db_pages['results'])
            except KeyError as e:
                logger.warning(f"{db_pages} {db_target} not found: {str(e)}")
        
            logger.info(f"Ran for {db_target} - Found {len(pages)} pages requiring updates")
        
        # Process each page
        responses = []
        for page in pages:
            try:
                response = SelfNotion(page).run()
                responses.append(response)
                logger.debug(f"Updated page {page['id']}")
            except Exception as e:
                logger.error(f"Failed to update page {page.get('id', 'unknown')}: {str(e)}")
                continue
        
        logger.info("Successfully completed identity updates")
        return {
                    'status': 'success',
                    'updated_pages': len(responses)
                }
        
    except Exception as e:
        logger.error(f"Unexpected error in identity processing: {str(e)}")
        raise
