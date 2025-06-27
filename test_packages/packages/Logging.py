from google.cloud import logging as cloud_logging
from google.auth import default
import logging  # Import standard Python logging module
import json
import os


class CloudLogger(object):
    """Google Cloud Logging client wrapper with default credentials.
    
    This class provides a simplified interface for logging to Google Cloud Logging
    using Google Application Credentials for authentication.
    
    Attributes:
        cloud_logging_client (cloud_logging.Client): Google Cloud Logging client
        logger (logging.Logger): Python logger instance
        prefix (str, optional): Prefix to add to all log messages
        project_id (str): Google Cloud project ID
    """
    
    def __init__(self, logger_name, prefix=None, project_id=None):
        """Initialize CloudLogger with Google Application Credentials.
        
        Args:
            logger_name (str): Name of the logger
            prefix (str, optional): Prefix to add to all log messages
            project_id (str, optional): Google Cloud project ID. If not provided,
                will use environment variable PUPPY_PROJECT_ID or default to
                'digital-africa-rainbow'
            
        Raises:
            Exception: If authentication fails or client initialization fails
        """
        # Get project ID from parameter, environment variable, or default
        self.project_id = "digital-africa-rainbow"
        
        try:
            # Get credentials using Google Auth default
            credentials, _ = default()
            
            # Set up Google Cloud Logging with default credentials and project
            self.cloud_logging_client = cloud_logging.Client(
                credentials=credentials,
                project=self.project_id
            )
            self.cloud_logging_client.setup_logging()
            
            # Set up Python logger
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(logging.DEBUG)
            
            # Store prefix
            self.prefix = prefix
            
        except Exception as e:
            # Fallback to basic logging if Google Cloud Logging fails
            print(f"Warning: Failed to initialize Google Cloud Logging for project {self.project_id}: {e}")
            print("Falling back to standard Python logging")
            
            # Set up basic Python logger
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(logging.DEBUG)
            
            # Ensure we have a handler
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            
            self.prefix = prefix
            self.cloud_logging_client = None

    def _format_message(self, msg, extra=None):
        """Format the log message with prefix and extra parameters if provided.
        
        Args:
            msg (str): The main log message
            extra (dict, optional): Additional parameters to log
            
        Returns:
            str: Formatted log message
        """
        # Add prefix if set
        if self.prefix:
            msg = f"[{self.prefix}] {msg}"
           
        if extra:
            # Convert extra dict to JSON string and append to message
            extra_str = json.dumps(extra)
            return f"{msg} | Extra: {extra_str}"
        return msg

    def info(self, msg, extra=None):
        """Log an info message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        formatted_msg = self._format_message(msg, extra)
        self.logger.info(formatted_msg)

    def warning(self, msg, extra=None):
        """Log a warning message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        formatted_msg = self._format_message(msg, extra)
        self.logger.warning(formatted_msg)

    def error(self, msg, extra=None):
        """Log an error message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        formatted_msg = self._format_message(msg, extra)
        self.logger.error(formatted_msg)

    def debug(self, msg, extra=None):
        """Log a debug message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        formatted_msg = self._format_message(msg, extra)
        self.logger.debug(formatted_msg)
