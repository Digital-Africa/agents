import json
from google.cloud import tasks_v2
from google.oauth2 import service_account
from google.cloud import firestore
from packages.Logging import CloudLogger
from packages.Firestore import Firestore
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
import os
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    """Enumeration of possible task execution states.
    
    States:
        PENDING: Task is created and waiting to be processed
        RUNNING: Task is currently being processed
        COMPLETED: Task has finished successfully
        FAILED: Task encountered an error during processing
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskStatusInfo:
    """Information about a task's execution status.
    
    This class represents the state of a task in the system, including its
    current status, timing information, and execution details.
    
    Attributes:
        task_name (str): The unique identifier of the task
        status (TaskStatus): Current execution state of the task
        created_at (datetime): Timestamp when the task was created
        updated_at (datetime): Timestamp when the status was last updated
        url (str): Target URL that the task will be sent to
        payload (Dict): The data payload associated with the task
        queue_name (str): The name of the queue the task belongs to
        error (Optional[str]): Error message if task failed, None otherwise
    """
    task_name: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    url: str
    payload: Dict
    queue_name: str
    error: Optional[str] = None

@dataclass
class TaskConfig:
    """Configuration for Tasks client.
    
    Attributes:
        project_id (str): Google Cloud project ID
        queue (str): Default queue name
        location (str): Google Cloud region
        service_account_file (str): Path to service account key file
        firestore_collection (str): Name of the Firestore collection for task status
    """
    project_id: str = 'digital-africa-rainbow'
    queue: str = "default"
    location: str = "europe-west1"
    service_account_file: str = "sa_keys/puppy-executor-key.json"
    firestore_collection: str = "task_status"

class Tasks(object):
    """Google Cloud Tasks client wrapper.
    
    Provides a simplified interface for working with Google Cloud Tasks,
    including task creation, management, and error handling.
    
    Attributes:
        config (TaskConfig): Configuration for the Tasks client
        client (tasks_v2.CloudTasksClient): Google Cloud Tasks client
        db (firestore.Client): Firestore client
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
        self._initialize_firestore()
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
            #self.logging.error(f"Failed to initialize client: {e}")
            print(e)
            raise
    
    def _initialize_firestore(self) -> None:
        """Initialize the Firestore client."""
        try:
            self.db = Firestore('system').client_firestore
        except Exception as e:
            self.logging.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    def _store_task_status(self, task_name: str, url: str, payload: Dict, queue: str, status: TaskStatus = TaskStatus.PENDING) -> None:
        """Store task status in Firestore.
        
        Creates or updates a document in Firestore to track the task's execution status.
        This is called automatically when a task is created and can be used to
        initialize task tracking.
        
        Args:
            task_name (str): Unique identifier of the task
            url (str): Target URL for the task
            payload (Dict): Task payload data
            queue (str): Name of the queue the task belongs to
            status (TaskStatus): Initial status of the task, defaults to PENDING
            
        Raises:
            ValueError: If task_name is empty or invalid
            Exception: If Firestore operation fails
        """
        if not task_name or not isinstance(task_name, str):
            raise ValueError("task_name must be a non-empty string")
            
        try:
            # Clean and validate task name
            task_name = task_name.strip()
            if not task_name:
                raise ValueError("task_name cannot be empty after stripping")
                
            # Extract the last part of the task name if it's a full path
            if '/' in task_name:
                task_name = task_name.split('/')[-1]
            
            now = datetime.utcnow()
            task_info = TaskStatusInfo(
                task_name=task_name,
                status=status,
                created_at=now,
                updated_at=now,
                url=url,
                payload=payload,
                queue_name=queue
            )
            
            # Convert to dict for Firestore storage
            task_dict = {
                "task_name": task_info.task_name,
                "status": task_info.status.value,
                "created_at": task_info.created_at,
                "updated_at": task_info.updated_at,
                "url": task_info.url,
                "payload": task_info.payload,
                "queue_name": task_info.queue_name,
                "error": task_info.error
            }
            
            # Ensure collection path is valid
            collection_ref = self.db.collection(self.config.firestore_collection)
            if not collection_ref:
                raise ValueError(f"Invalid collection path: {self.config.firestore_collection}")
            
            # Log the paths for debugging
            self.logging.info(f"Collection path: {self.config.firestore_collection}")
            self.logging.info(f"Document ID: {task_name}")
            
            # Create document with explicit path
            doc_ref = collection_ref.document(task_name)
            doc_ref.set(task_dict, merge=True)
            
            self.logging.info(f"Task status stored successfully: {task_name}")
            
        except Exception as e:
            error_msg = f"Failed to store task status: {str(e)}"
            self.logging.error(error_msg)
            raise ValueError(error_msg)
    
    def add_task(self, params: Dict, task_name: Optional[str] = None) -> Optional[str]:
        """Add a new task to the queue.
        
        Args:
            params (Dict): Task parameters including:
                - url (str): Target URL for the task (required)
                - payload (Dict): Task payload (optional)
                - queue (str): Queue name (optional, defaults to config queue)
            task_name (Optional[str]): Custom name for the task. If not provided,
                a name will be generated by Cloud Tasks.
        
        Returns:
            Optional[str]: Task name if successful, None if failed
            
        Raises:
            ValueError: If required parameters are missing
            Exception: If task creation or status storage fails
        """
        try:
            # Log input parameters for debugging
            self.logging.info(f"Adding task with params: {json.dumps(params, default=str)}")
            if task_name:
                self.logging.info(f"Using custom task name: {task_name}")
            
            # Validate URL
            if not params.get("url"):
                error_msg = "URL is required in params"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
                
            url = params["url"]
            payload = params.get("payload", {})
            queue = params.get("queue", self.config.queue)
            
            # Log configuration
            self.logging.info(f"Using queue: {queue}")
            self.logging.info(f"Project ID: {self.config.project_id}")
            self.logging.info(f"Location: {self.config.location}")
            
            # Validate client
            if not hasattr(self, 'client') or not self.client:
                error_msg = "Cloud Tasks client not initialized"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
            
            try:
                parent = self.client.queue_path(
                    self.config.project_id,
                    self.config.location,
                    queue
                )
                self.logging.info(f"Queue path: {parent}")
            except Exception as e:
                error_msg = f"Failed to create queue path: {str(e)}"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
            
            # Prepare task
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": url,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(payload).encode()
                }
            }
            
            # Add name if provided
            if task_name:
                task["name"] = f"{parent}/tasks/{task_name}"
            
            # Log task details
            self.logging.info(f"Task details: {json.dumps(task, default=str)}")
            
            try:
                response = self.client.create_task(
                    request={"parent": parent, "task": task}
                )
            except Exception as e:
                error_msg = f"Failed to create task in Cloud Tasks: {str(e)}"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
            
            if not response:
                error_msg = "No response received from create_task"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
                
            if not response.name:
                error_msg = "Task created but no name in response"
                self.logging.error(error_msg)
                raise ValueError(error_msg)
            
            # Log successful task creation
            self.logging.info(f"Task created successfully with name: {response.name}")
            
            try:
                # Store task status in Firestore
                self._store_task_status(response.name, url, payload, queue)
                self.logging.info(f"Task status stored in Firestore: {response.name}")
            except Exception as e:
                error_msg = f"Failed to store task status: {str(e)}"
                self.logging.error(error_msg)
                # Don't raise here, as the task was created successfully
            
            self.logging.info(f"[enqueue_push_notion_task] Task enqueued: {response.name}")
            print(f"[enqueue_push_notion_task] Task enqueued: {response.name}")
            return response
            
        except Exception as e:
            error_msg = f"Failed to add task: {str(e)}"
            print(error_msg)
            self.logging.error(error_msg)
            return None
    
    def update_task_status(self, task_name: str, status: TaskStatus, error: Optional[str] = None) -> None:
        """Update the status of a task in Firestore.
        
        This method should be called at different points in the task lifecycle:
        - When task starts processing (TaskStatus.RUNNING)
        - When task completes successfully (TaskStatus.COMPLETED)
        - When task fails (TaskStatus.FAILED)
        - During long-running tasks to update progress
        - When retrying failed tasks
        
        The status update includes a timestamp and optional error message.
        
        Args:
            task_name (str): Unique identifier of the task to update
            status (TaskStatus): New status of the task
            error (Optional[str]): Error message if task failed, or progress information
                for long-running tasks. Defaults to None.
                
        Raises:
            Exception: If the Firestore update fails
        """
        try:
            task_ref = self.db.collection(self.config.firestore_collection).document(task_name)
            task_ref.update({
                "status": status.value,
                "updated_at": datetime.utcnow(),
                "error": error
            })
        except Exception as e:
            self.logging.error(f"Failed to update task status: {e}")
            raise
    
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

