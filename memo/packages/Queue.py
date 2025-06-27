import json
from typing import Optional, Dict, Any
from google.cloud import tasks_v2
from google.oauth2 import service_account
from google.api_core import retry
from packages.Logging import CloudLogger


class Queue:
    """Google Cloud Tasks Queue management class.
    
    Handles queue operations including creation, listing, and management of Cloud Tasks queues.
    Implements retry mechanisms and proper error handling.
    """

    def __init__(self, 
                 project: str = 'digital-africa-rainbow',
                 queue: str = 'async-default',
                 location: str = 'europe-west1',
                 service_account_file: str = '*/sa_keys/puppy-executor-key.json'):
        """Initialize Queue instance.
        
        Args:
            project: Google Cloud project ID
            queue: Default queue name
            location: Google Cloud region
            service_account_file: Path to service account credentials
        """
        self.project = project
        self.queue = queue
        self.location = location
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self._client = None  # Lazy initialization
        self.logging = CloudLogger(logger_name='Puppy_Queue_Management')

    @property
    def client(self) -> tasks_v2.CloudTasksClient:
        """Lazy initialization of Cloud Tasks client.
        
        Returns:
            CloudTasksClient: Authenticated client instance
        """
        if self._client is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.SERVICE_ACCOUNT_FILE)
                self._client = tasks_v2.CloudTasksClient(credentials=credentials)
                self.logging.info("Cloud Tasks client initialized successfully")
            except Exception as e:
                self.logging.error(f"Failed to initialize Cloud Tasks client: {e}")
                raise
        return self._client

    @retry.Retry()  # Implements exponential backoff
    def list_queue(self) -> None:
        """List all queues in the project.
        
        Implements retry mechanism for improved reliability.
        """
        try:
            parent = f'projects/{self.project}/locations/{self.location}'
            queues = self.client.list_queues(parent=parent)
            
            for queue in queues:
                self.logging.info(f"Found queue: {queue.name}")
                print(queue.name)
        except Exception as e:
            self.logging.error(f"Failed to list queues: {e}")
            raise

    @retry.Retry()
    def create_queue(self, queue_name: str, 
                    max_dispatches_per_second: int = 5,
                    max_attempts: int = 3) -> Optional[str]:
        """Create a new Cloud Tasks queue.
        
        Args:
            queue_name: Name of the queue to create
            max_dispatches_per_second: Maximum dispatch rate
            max_attempts: Maximum retry attempts
            
        Returns:
            str: Name of created queue if successful
            
        Raises:
            ValueError: If queue_name is invalid
            Exception: If queue creation fails
        """
        if not queue_name:
            raise ValueError("Queue name must be provided")
            
        try:
            parent = self.client.common_location_path(self.project, self.location)
            
            queue = {
                'name': self.client.queue_path(self.project, self.location, queue_name),
                'rate_limits': {
                    'max_dispatches_per_second': max_dispatches_per_second,
                },
                'retry_config': {
                    'max_attempts': max_attempts,
                }
            }
            
            response = self.client.create_queue(
                request={
                    "parent": parent,
                    "queue": queue
                }
            )
            
            self.logging.info(f"Queue created successfully: {response.name}")
            return response.name
            
        except Exception as e:
            self.logging.error(f"Failed to create queue {queue_name}: {e}")
            raise
