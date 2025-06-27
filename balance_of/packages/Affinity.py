import requests
from requests.auth import HTTPBasicAuth
from packages.SecretAccessor import SecretAccessor
import urllib


class Affinity(object):
    """
    A class for interacting with the Affinity API to manage lists, persons, and organizations.
    
    This class provides methods to fetch data from Affinity's API endpoints, including
    lists, person records, and organization records. It handles authentication and
    data formatting for API responses.
    
    Attributes:
        TOKEN (str): Authentication token for Affinity API access
    """
    
    def __init__(self):
        """
        Initialize a new Affinity instance.
        
        Sets up the authentication token from the secret manager for API access.
        """
        super(Affinity, self).__init__()
        self.TOKEN = SecretAccessor().get_secret('AFFINITY')
    
    def pull_all_lists(self):
        """
        Fetch all lists from the Affinity API.
        
        Makes a GET request to the Affinity lists endpoint to retrieve all available lists.
        The response is limited to 100 items per request.
        
        Returns:
            list: A list of dictionaries containing list data from Affinity
        """
        url = "https://api.affinity.co/v2/lists"

        query = {
        #"cursor": "string",
        "limit": "100"
        }

        headers = {"Authorization": f"Bearer {self.TOKEN}"}

        response = requests.get(url, headers=headers, params=query)

        affinity_lists = response.json()
        return affinity_lists['data']
    
    def get_person(self, term):
        """
        Search for persons in Affinity based on a search term.
        
        Args:
            term (str): Search term to find matching persons
            
        Returns:
            dict: A dictionary containing:
                - persons_id (list): List of person IDs
                - affinity_url (list): List of Affinity URLs for each person
                - results (dict): Complete API response data
        """
        url = f"https://api.affinity.co/persons"
        
        params = {
        "term": term,
        }
        
        response = requests.get(url, auth=HTTPBasicAuth('', self.TOKEN), params = params)
        #print(response.text)
        result = response.json()
        persons = result.get('persons')
        persons_id = [p.get('id','') for p in persons]
        affinity_urls = [f'https://digitalafrica.affinity.co/persons/{person_id}' for person_id in persons_id]
        return {
                'persons_id':persons_id,
                'affinity_url':affinity_urls,
                'results': result 
                        }
    
    def get_organization(self, term):
        """
        Search for organizations in Affinity based on a search term.
        
        Args:
            term (str): Search term to find matching organizations
            
        Returns:
            dict: A dictionary containing:
                - organizations_id (list): List of organization IDs
                - affinity_url (list): List of Affinity URLs for each organization
                - results (dict): Complete API response data
        """
        url = f"https://api.affinity.co/organizations"
        
        params = {
        "term": term,
        }
        
        response = requests.get(url, auth=HTTPBasicAuth('', self.TOKEN), params = params)
        print(response.text)
        result = response.json()
        organizations = result.get('organizations')
        organizations_id = [p.get('id','') for p in organizations]
        affinity_urls = [f'https://digitalafrica.affinity.co/companies/{organizationsid}' for organizationsid in organizations_id]
        return {
                'organizations_id':organizations_id,
                'affinity_url':affinity_urls,
                'results': result 
                        }

    def get_affinity_person_id(self, email):
        email = urllib.parse.quote(email)
        url = f"https://api.affinity.co/persons?term={email}"
        response = requests.get(url, auth=('', self.TOKEN))
        response = response.json()
        if response['persons'] == []:
            return None
        elif len(response['persons']) > 1:
            raise Exception(f"Multiple persons found for email: {email}")
        else:
            return response['persons'][0]['id']