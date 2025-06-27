from packages.Notion import Notion
from packages.Capsule import CapsuleNotion
from packages.Affinity import Affinity


class Cofounders:
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
    
    def match_satori_id(self, satori_id):
        """
        Retrieve a related page ID from a Notion database.
        
        Args:
            DB (str): Database identifier to look up
            filter_ (dict): Filter criteria for the database query
            
        Returns:
            str: Page ID of the matching record
        """
        
        filter_ = {
                        "property": "satori_id",
                        "rich_text": {
                            "equals": satori_id
                        }
                    }
        
        match = Notion().pull.query_database(self.startups_pool, filter_)
        match = match['results']
        return match
    
    def match_country(self, country):
        """
        Retrieve a related page ID from a Notion database.
        
        Args:
            DB (str): Database identifier to look up
            filter_ (dict): Filter criteria for the database query
            
        Returns:
            str: Page ID of the matching record
        """
        filter_ = {
                        "property": "Country",
                        "rich_text": {
                            "equals": country
                        }
                    }
        match = Notion().pull.query_database(self.mapverse, filter_)
        match = match['results']
        return match
    
    def not_exists(self):
        """
        Check if a cofounder record already exists in the Notion database.
        
        Performs a query to check for existing records with the same founder ID.
        
        Returns:
            bool: True if no matching record exists, False otherwise
        """
        filter_ = {
                        "property": "id founder",
                        "rich_text": {
                                        "equals": self.data['id_founder']
                                    }
                        }

        match = Notion().pull.query_database(self.database, filter_)
        if not match['results']:
            return True
        else:
            return False    

    def transform(self):
        """
        Transform and enrich the raw cofounder data.
        
        Performs the following transformations:
        - Combines first and last name into full name
        - Retrieves startup relation from Notion
        - Fetches and links Affinity person record
        
        Returns:
            dict: Enriched cofounder data
        """
        
        satori_id = self.data['id_startup']
        self.data['full_name'] = self.data['cofounder_first_name'] + " " + self.data['cofounder_last_name']
        email = self.data['cofounder_email']
        country = self.match_country(self.data['cofounder_nationality'])
        relation = self.match_satori_id(satori_id)
        
        if country:
            self.data['Nationality'] = country[0]['id']
        if relation:
            relation = [match['id'] for match in relation]
            self.data['startups_pool'] = relation
        
        affinity = Affinity().get_person(email)
        affinity_link = affinity.get('affinity_url')
        
        if affinity_link == []:
            affinity_link = 'Unknown'
            self.data['affinity_link'] = affinity_link
        else:
            self.data['affinity_link'] = affinity_link[0]
        return self.data

    def build(self):
        """
        Build Notion properties for the cofounder record.
        
        Creates a dictionary of Notion properties including:
        - Title (full name)
        - Startup relation
        - Gender selection
        - First name and last name
        - Founder ID
        - Nationality
        - Affinity URL
        
        Returns:
            dict: Formatted Notion properties
        """
        writer = Notion().writer
        properties = dict()
        #  ['Fullname', 'title', 'title']
        properties['title'] = writer.title(self.data['full_name'])
        
        #  ['Nationality', 'Z%7BZ~', 'relation']
        properties['Z%7BZ~'] = writer.relation(self.data['Nationality']) #TODO : retrieve page_id match with Mapverse
        #  ['Startups Pool', 'AQ%5E%60', 'relation']
        startups_pool =  self.data.get('startups_pool', None)
        if startups_pool:
            properties['AQ%5E%60'] = writer.relation(startups_pool)

        #  ['Gender', 'R%40lG', 'select']
        properties['R%40lG'] = writer.select(self.data['cofounder_gender'])

        #  ['Firstname', 'fapT', 'rich_text']
        properties['fapT'] = writer.text(self.data['cofounder_first_name'])
         #  ['satori_id', 'iELQ', 'rich_text']
        properties['iELQ'] = writer.text(self.data['id_startup'])
        #  ['Lastname', 'yGDG', 'rich_text']
        properties['yGDG'] = writer.text(self.data['cofounder_last_name'])
        # ['id founder', 'XniD', 'rich_text']
        properties['XniD'] = writer.text(self.data['id_founder'])
        #  ['_Nationality_', 'nHOq', 'rich_text']
        properties['nHOq'] = writer.text(self.data['cofounder_nationality'])
        # ['Email', 'Cn%5C%3C', 'rich_text'],
        #properties['Cn%5C%3C'] = writer.text(self.data['encrypted_email']) #TODO : Ecrypted email

        #  ['Affinity', 'gD%3Ao', 'url'],
        properties['gD%3Ao'] = writer.url(self.data['affinity_link'])
        return properties
    
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