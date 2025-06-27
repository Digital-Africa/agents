import json
from google.cloud import tasks_v2
from google.oauth2 import service_account
from packages.Logging import CloudLogger
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
import os

@dataclass
class TaskConfig:
    """Configuration for Tasks client.
    
    Attributes:
        project_id (str): Google Cloud project ID
        queue (str): Default queue name
        location (str): Google Cloud region
        service_account_file (str): Path to service account key file
    """
    project_id: str = 'digital-africa-rainbow'
    queue: str = "default"
    location: str = "europe-west1"
    service_account_file: str = "sa_keys/puppy-executor-key.json"

class Tasks(object):
    """Google Cloud Tasks client wrapper.
    
    Provides a simplified interface for working with Google Cloud Tasks,
    including task creation, management, and error handling.
    
    Attributes:
        config (TaskConfig): Configuration for the Tasks client
        client (tasks_v2.CloudTasksClient): Google Cloud Tasks client
        logging (CloudLogger): Logger instance
    """
    
    def __init__(self, config: Optional[TaskConfig] = None):
        """Initialize Tasks client.
        
        Args:
            config (Optional[TaskConfig]): Configuration for the client.
                If not provided, will use default configuration.
        """
        super(Tasks, self).__init__()
        self.config = config or self._load_config_from_env()
        self._initialize_client()
        self.logging = CloudLogger(logger_name='Puppy_Task_Management')
        
        # For backward compatibility
        self.project = self.config.project_id
        self.queue = self.config.queue
        self.location = self.config.location
        self.SERVICE_ACCOUNT_FILE = self.config.service_account_file
    
    def _load_config_from_env(self) -> TaskConfig:
        """Load configuration from environment variables."""
        return TaskConfig(
            project_id=os.getenv("PUPPY_PROJECT_ID", "digital-africa-rainbow"),
            queue=os.getenv("PUPPY_QUEUE", "default"),
            location=os.getenv("PUPPY_LOCATION", "europe-west1"),
            service_account_file=os.getenv("PUPPY_SA_FILE", "sa_keys/puppy-executor-key.json")
        )
    
    def _initialize_client(self) -> None:
        """Initialize the Cloud Tasks client."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.config.service_account_file
            )
            self.client = tasks_v2.CloudTasksClient(credentials=credentials)
        except Exception as e:
            self.logging.error(f"Failed to initialize client: {e}")
            raise
    
    def add_task(self, params: Dict) -> Optional[str]:
        """Add a new task to the queue.
        
        Args:
            params (Dict): Task parameters including:
                - url (str): Target URL for the task (required)
                - payload (Dict): Task payload (optional)
                - queue (str): Queue name (optional, defaults to config queue)
        
        Returns:
            Optional[str]: Task name if successful, None if failed
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not params.get("url"):
            raise ValueError("URL is required")
            
        try:
            url = params["url"]
            payload = params.get("payload", "")
            queue = params.get("queue", self.config.queue)
            
            parent = self.client.queue_path(
                self.config.project_id,
                self.config.location,
                queue
            )
            
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": url,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(payload).encode()
                }
            }
            
            response = self.client.create_task(
                request={"parent": parent, "task": task}
            )
            
            self.logging.info(f"[enqueue_push_notion_task] Task enqueued: {response.name}")
            print(f"[enqueue_push_notion_task] Task enqueued: {response.name}")
            return response
            
        except Exception as e:
            print(f"{e}")
            self.logging.error(f"{e}")
            return None
    
    def add_tasks_batch(self, tasks: List[Dict]) -> Dict[str, List]:
        """Add multiple tasks in batch.
        
        Args:
            tasks (List[Dict]): List of task parameters, each containing:
                - url (str): Target URL for the task (required)
                - payload (Dict): Task payload (optional)
                - queue (str): Queue name (optional)
            
        Returns:
            Dict[str, List]: Dictionary containing successful and failed tasks
        """
        results = {"succeeded": [], "failed": []}
        
        for task_params in tasks:
            try:
                task_name = self.add_task(task_params)
                if task_name:
                    results["succeeded"].append({
                        "params": task_params,
                        "task_name": task_name
                    })
                else:
                    results["failed"].append({
                        "params": task_params,
                        "error": "Task creation failed"
                    })
            except Exception as e:
                results["failed"].append({
                    "params": task_params,
                    "error": str(e)
                })
        
        return results

