import functions_framework
import requests
import json
import re
from typing import Dict, Any, Optional
from packages.Logging import CloudLogger
from packages.SecretAccessor import SecretAccessor


class NotionGitHubSync:
    """Cloud Function to sync Notion pages with GitHub pull requests."""
    
    def __init__(self):
        """Initialize the sync service with required clients and tokens."""
        self.logger = CloudLogger("NotionGitHubSync")
        self.secret_accessor = SecretAccessor()
        
        # Get API tokens
        self.notion_token = self.secret_accessor.get_secret("notion-token")
        self.github_token = self.secret_accessor.get_secret("github-token")
        
        # API configurations
        self.notion_api_version = "2022-06-28"
        self.github_repo = "your-org/your-repo"
        self.github_api_base = "https://api.github.com"
        self.notion_api_base = "https://api.notion.com/v1"
        
        # Headers for API requests
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": self.notion_api_version,
            "Content-Type": "application/json"
        }
        
        self.github_headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        self.logger.info("NotionGitHubSync initialized successfully")

    def fetch_notion_page(self, page_id: str) -> Dict[str, Any]:
        """
        Fetch page data from Notion API.
        
        Args:
            page_id (str): The Notion page ID
            
        Returns:
            Dict containing page title, description, and branch name
        """
        try:
            self.logger.info(f"Fetching Notion page: {page_id}")
            
            # Get page properties
            url = f"{self.notion_api_base}/pages/{page_id}"
            response = requests.get(url, headers=self.notion_headers)
            response.raise_for_status()
            
            page_data = response.json()
            properties = page_data.get("properties", {})
            
            # Extract title from title property
            title_prop = properties.get("Title", {})
            title = ""
            if title_prop.get("type") == "title":
                title_blocks = title_prop.get("title", [])
                if title_blocks:
                    title = title_blocks[0].get("plain_text", "")
            
            # Extract description from description property
            desc_prop = properties.get("Description", {})
            description = ""
            if desc_prop.get("type") == "rich_text":
                desc_blocks = desc_prop.get("rich_text", [])
                if desc_blocks:
                    description = desc_blocks[0].get("plain_text", "")
            
            # Extract branch name from branch name property
            branch_prop = properties.get("Branch Name", {})
            branch_name = ""
            if branch_prop.get("type") == "rich_text":
                branch_blocks = branch_prop.get("rich_text", [])
                if branch_blocks:
                    branch_name = branch_blocks[0].get("plain_text", "")
            
            # Clean branch name (remove special characters, convert to lowercase)
            if branch_name:
                branch_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', branch_name.lower())
                branch_name = re.sub(r'-+', '-', branch_name).strip('-')
            
            result = {
                "title": title,
                "description": description,
                "branch_name": branch_name
            }
            
            self.logger.info("Notion page data extracted", extra=result)
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching Notion page: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error processing Notion page: {e}")
            raise

    def get_dev_branch_sha(self) -> str:
        """
        Get the SHA of the dev branch.
        
        Returns:
            str: SHA of the dev branch
        """
        try:
            self.logger.info("Getting dev branch SHA")
            
            url = f"{self.github_api_base}/repos/{self.github_repo}/branches/dev"
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            
            branch_data = response.json()
            sha = branch_data.get("commit", {}).get("sha")
            
            if not sha:
                raise ValueError("Could not retrieve SHA from dev branch")
            
            self.logger.info(f"Retrieved dev branch SHA: {sha[:8]}")
            return sha
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting dev branch SHA: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting dev branch SHA: {e}")
            raise

    def create_branch(self, branch_name: str, base_sha: str) -> bool:
        """
        Create a new branch from the dev branch.
        
        Args:
            branch_name (str): Name of the new branch
            base_sha (str): SHA to base the branch on
            
        Returns:
            bool: True if branch created successfully
        """
        try:
            self.logger.info(f"Creating branch: {branch_name}")
            
            url = f"{self.github_api_base}/repos/{self.github_repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            
            response = requests.post(url, headers=self.github_headers, json=data)
            
            # Handle case where branch already exists
            if response.status_code == 422:
                self.logger.warning(f"Branch {branch_name} already exists")
                return True
            
            response.raise_for_status()
            
            self.logger.info(f"Branch {branch_name} created successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating branch: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating branch: {e}")
            raise

    def create_pull_request(self, title: str, description: str, branch_name: str) -> str:
        """
        Create a draft pull request.
        
        Args:
            title (str): PR title
            description (str): PR description
            branch_name (str): Source branch name
            
        Returns:
            str: URL of the created pull request
        """
        try:
            self.logger.info(f"Creating pull request for branch: {branch_name}")
            
            url = f"{self.github_api_base}/repos/{self.github_repo}/pulls"
            data = {
                "title": title,
                "body": description,
                "head": branch_name,
                "base": "dev",
                "draft": True
            }
            
            response = requests.post(url, headers=self.github_headers, json=data)
            response.raise_for_status()
            
            pr_data = response.json()
            pr_url = pr_data.get("html_url")
            
            if not pr_url:
                raise ValueError("Could not retrieve PR URL from response")
            
            self.logger.info(f"Pull request created: {pr_url}")
            return pr_url
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating pull request: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating pull request: {e}")
            raise

    def update_notion_page(self, page_id: str, pr_url: str) -> bool:
        """
        Update the Notion page with PR URL and set status to "In Progress".
        
        Args:
            page_id (str): Notion page ID
            pr_url (str): URL of the created pull request
            
        Returns:
            bool: True if update successful
        """
        try:
            self.logger.info(f"Updating Notion page: {page_id}")
            
            url = f"{self.notion_api_base}/pages/{page_id}"
            
            # Prepare update data
            update_data = {
                "properties": {
                    "PR URL": {
                        "url": pr_url
                    },
                    "Status": {
                        "select": {
                            "name": "In Progress"
                        }
                    }
                }
            }
            
            response = requests.patch(url, headers=self.notion_headers, json=update_data)
            response.raise_for_status()
            
            self.logger.info("Notion page updated successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating Notion page: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating Notion page: {e}")
            raise

    def process_page(self, page_id: str) -> Dict[str, Any]:
        """
        Main processing function that orchestrates the entire sync process.
        
        Args:
            page_id (str): Notion page ID to process
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            self.logger.info(f"Starting sync process for page: {page_id}")
            
            # Step 1: Fetch page data from Notion
            page_data = self.fetch_notion_page(page_id)
            
            if not page_data.get("title"):
                raise ValueError("Page title is required but not found")
            
            if not page_data.get("branch_name"):
                raise ValueError("Branch name is required but not found")
            
            # Step 2: Get dev branch SHA
            dev_sha = self.get_dev_branch_sha()
            
            # Step 3: Create new branch
            self.create_branch(page_data["branch_name"], dev_sha)
            
            # Step 4: Create pull request
            pr_url = self.create_pull_request(
                page_data["title"],
                page_data["description"],
                page_data["branch_name"]
            )
            
            # Step 5: Update Notion page
            self.update_notion_page(page_id, pr_url)
            
            result = {
                "success": True,
                "page_id": page_id,
                "pr_url": pr_url,
                "branch_name": page_data["branch_name"],
                "title": page_data["title"]
            }
            
            self.logger.info("Sync process completed successfully", extra=result)
            return result
            
        except Exception as e:
            self.logger.error(f"Sync process failed: {e}")
            return {
                "success": False,
                "page_id": page_id,
                "error": str(e)
            }


# Global instance of the sync service
sync_service = NotionGitHubSync()


@functions_framework.http
def notion_github_sync(request):
    """
    Google Cloud Function entry point.
    
    Args:
        request: Flask request object
        
    Returns:
        Flask response object
    """
    # Set CORS headers for web requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Validate request method
        if request.method != 'POST':
            return (json.dumps({
                'error': 'Method not allowed. Use POST.'
            }), 405, headers)
        
        # Parse request body
        try:
            request_data = request.get_json()
        except Exception as e:
            return (json.dumps({
                'error': f'Invalid JSON in request body: {e}'
            }), 400, headers)
        
        # Validate required fields
        if not request_data or 'page_id' not in request_data:
            return (json.dumps({
                'error': 'Missing required field: page_id'
            }), 400, headers)
        
        page_id = request_data['page_id']
        
        # Validate page_id format (basic UUID validation)
        if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', page_id):
            return (json.dumps({
                'error': 'Invalid page_id format. Expected UUID format.'
            }), 400, headers)
        
        # Process the page
        result = sync_service.process_page(page_id)
        
        if result['success']:
            return (json.dumps(result), 200, headers)
        else:
            return (json.dumps(result), 500, headers)
            
    except Exception as e:
        sync_service.logger.error(f"Function execution failed: {e}")
        return (json.dumps({
            'error': 'Internal server error',
            'message': str(e)
        }), 500, headers) 