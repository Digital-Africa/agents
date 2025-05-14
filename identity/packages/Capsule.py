from packages.Tasks import Tasks, TaskConfig

class CapsuleNotion:
    """
    A class for creating and managing Notion database entries with customizable properties and icons.
    
    This class provides functionality to build Notion database entries with properties, icons,
    and content, and enqueue them for processing through a task queue system.
    
    Attributes:
        icon (str, optional): Icon identifier for the Notion page
        db (str): Notion database ID
        properties (dict): Properties to be set for the Notion page
        page_id (str, optional): ID of an existing Notion page for updates
        content (dict, optional): Content to be added to the Notion page
        capsule (dict): Built capsule containing payload and queue information
    """
    
    def __init__(self, database, properties, content=None, icon=None, page_id=None):
        """
        Initialize a new CapsuleNotion instance.
        
        Args:
            database (str): Notion database ID where the page will be created/updated
            properties (dict): Properties to be set for the Notion page
            content (dict, optional): Content to be added to the Notion page
            icon (str, optional): Icon identifier for the Notion page
            page_id (str, optional): ID of an existing Notion page for updates
        """
        self.icon = icon
        self.db = database
        self.properties = properties
        self.page_id = page_id
        self.content = content
        self.capsule = self.build()

        
    def build(self):
        """
        Build the capsule structure for the Notion page creation/update.
        
        Constructs a dictionary containing the payload and queue information
        needed to create or update a Notion page through the task queue system.
        
        Returns:
            dict: A dictionary containing:
                - payload: The body of the request and optional page_id
                - queue: The queue name for task processing
                - url: The endpoint URL for the Notion API
        """
        body = dict()
        body['parent'] = {'database_id': self.db}
        body['properties'] = self.properties
        
        if self.icon != None:
            body['icon'] =  {'type': 'external','external': {'url': self.icon}}
        if self.content != None:
            pass
            #body['icon'] =  {'type': 'external','external': {'url': self.get_icon()}}

        if self.page_id == None:
            return {    
                        'payload': {'body':body}, 
                        'queue': 'notion-queue', 
                        'url':'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_notion'
                    }
        else:            
            return {    
                        'payload': {'body': body, 'page_id': self.page_id}, 
                        'queue': 'notion-queue', 
                        'url':'https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_notion'
                    }

    def enqueue(self):
        """
        Enqueue the built capsule for processing.
        
        Configures the service account and adds the capsule to the task queue
        for processing by the Notion API.
        
        Returns:
            dict: Response from the task queue system indicating the status of the enqueued task
        # - url (str): Target URL for the task (required)
        # - payload (Dict): Task payload (optional)
        # - queue (str): Queue name (optional, defaults to config queue)
        """

        TaskConfig.servive_account = "sa_keys/puppy-executor-key.json"
        response = Tasks().add_task(self.capsule)
        return response
