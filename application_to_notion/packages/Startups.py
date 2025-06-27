from packages.Notion import Notion
from packages.Capsule import CapsuleNotion
from packages.Affinity import Affinity
from packages.storage import Operation, Reference


class Startups:
    """
    A class for managing cofounder data and synchronizing it with Notion and Affinity.
    
    This class handles the creation and management of cofounder records, including:
    - Data transformation and enrichment
    - Integration with Notion database
    - Affinity person record linking
    - Duplicate checking
    
    Attributes:
        data (dict): Raw cofounder data containing fields like:
            - id_founder
            - cofounder_first_name
            - cofounder_last_name
            - cofounder_nationality
            - cofounder_email
            - cofounder_gender
            - id_startup
        database (str): Notion database ID for cofounder records
        icon (str): Icon identifier for Notion pages
        capsule (dict): Built Notion properties for the cofounder record
    """
    
    def __init__(self, data):
        """
        Initialize a new Cofounders instance.
        
        Args:
            data (dict): Raw cofounder data containing required fields
        """
        self.data = data
        self.database = '13619a07ff444d05bbee168b31ff7260'
        self.icon = "https://www.notion.so/icons/card_brown.svg"
        self.startups_pool = "67853899c6ff4e78aeb2f25b0875b601"
        self.mapverse = "c4c8efef870e43c298cbd6344b8fb739"
        self.data = self.transform()
        self.capsule = self.build()

    def not_exists(self):
        """
        Check if a startup record already exists in the Notion database.
        
        Performs a query to check for existing records with the same founder ID.
        
        Returns:
            bool: True if no matching record exists, False otherwise
        """
        filter_ = {
                        "property": "satori_id",
                        "rich_text": {
                                        "equals": self.data['id_startup']
                                    }
                        }

        match = Notion().pull.query_database(self.database, filter_)
        if not match['results']:
            return True
        else:
            return False 
                
    def transform(self):
        """
        Transform and enrich the raw startup data.
        
        Returns:
            dict: Transformed data
        """
        return self.data
    
    def build(self):
        """
        Build Notion properties for the startup record.
        
        Returns:
            dict: Formatted Notion properties
        """
        return {}
    
    def run(self):
        """
        Execute the cofounder record creation process.
        
        Checks for existing records and creates a new Notion page if none exists.
        
        Returns:
            dict: Response from the Notion API if successful, None otherwise
        """
        if self.not_exists():
            params = { 
                        'database': self.database,
                        'icon': self.icon,
                        'properties': self.capsule
                    }
            response = CapsuleNotion(**params).enqueue()
            # Convert Tasks response to dictionary to avoid Task object being returned
            if response:
                return {"status": "success", "message": "Cofounder record queued for creation"}
            else:
                return {"status": "error", "message": "Failed to queue cofounder record"}
        else:
            return {"status": "info", "message": "Cofounder record already exists"}