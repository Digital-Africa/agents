from google.cloud import logging as cloud_logging
from google.auth import default
import logging  # Import standard Python logging module
import json
import os
import sys
import time
import threading
from typing import Optional, Dict, Any


class CloudLogger(object):
    """Google Cloud Logging client wrapper with automatic environment detection.
    
    This class provides a simplified interface for logging that automatically
    detects the environment and uses the appropriate logging method:
    - Cloud Functions: Uses Google Cloud Logging with fallback to local
    - Local/Other: Uses standard Python logging with cloud logging as option
    
    Includes robust SSL error handling, automatic retry logic, and runtime
    error detection for cloud logging operations.
    
    Attributes:
        cloud_logging_client (cloud_logging.Client): Google Cloud Logging client
        logger (logging.Logger): Python logger instance
        prefix (str, optional): Prefix to add to all log messages
        project_id (str): Google Cloud project ID
        use_cloud_logging (bool): Whether cloud logging is available
        ssl_error_count (int): Count of SSL errors encountered
        max_ssl_errors (int): Maximum SSL errors before permanent fallback
        retry_delay (float): Current retry delay for exponential backoff
        environment (str): Detected environment ('cloud_function', 'gcp', 'local')
    """
    
    def __init__(self, logger_name, prefix=None, project_id=None, force_local=False, 
                 force_cloud=False, max_ssl_errors=3, initial_retry_delay=1.0):
        """Initialize CloudLogger with automatic environment detection.
        
        Args:
            logger_name (str): Name of the logger
            prefix (str, optional): Prefix to add to all log messages
            project_id (str, optional): Google Cloud project ID. If not provided,
                will use environment variable PUPPY_PROJECT_ID or default to
                'digital-africa-rainbow'
            force_local (bool, optional): Force local logging only, skip cloud logging
            force_cloud (bool, optional): Force cloud logging, skip local logging
            max_ssl_errors (int, optional): Maximum SSL errors before permanent fallback
            initial_retry_delay (float, optional): Initial retry delay in seconds
            
        Raises:
            Exception: If both cloud and local logging fail to initialize
        """
        # Get project ID from parameter, environment variable, or default
        self.project_id = project_id or os.getenv("PUPPY_PROJECT_ID", "digital-africa-rainbow")
        self.prefix = prefix
        self.use_cloud_logging = False
        self.ssl_error_count = 0
        self.max_ssl_errors = max_ssl_errors
        self.retry_delay = initial_retry_delay
        self._lock = threading.Lock()  # Thread safety for SSL error handling
        
        # Detect environment
        self.environment = self._detect_environment()
        
        # Initialize Python logger first (always available)
        self._setup_python_logger(logger_name)
        
        # Determine logging strategy based on environment and parameters
        self._setup_logging_strategy(logger_name, force_local, force_cloud)
    
    def _detect_environment(self):
        """Detect the current environment.
        
        Returns:
            str: Environment type ('cloud_function', 'gcp', 'local')
        """
        # Check for Cloud Function environment variables
        if (os.getenv("FUNCTION_TARGET") or  # Cloud Functions v2
            os.getenv("K_SERVICE") or         # Cloud Run/Cloud Functions v1
            os.getenv("FUNCTION_NAME")):      # Legacy Cloud Functions
            return "cloud_function"
        
        # Check for general GCP environment
        if (os.getenv("GOOGLE_CLOUD_PROJECT") or
            os.getenv("GCP_PROJECT") or
            os.getenv("CLOUDSDK_PROJECT")):
            return "gcp"
        
        # Default to local environment
        return "local"
    
    def _setup_logging_strategy(self, logger_name, force_local, force_cloud):
        """Set up logging strategy based on environment and parameters.
        
        Args:
            logger_name (str): Name of the logger
            force_local (bool): Force local logging only
            force_cloud (bool): Force cloud logging only
        """
        if force_local:
            # User explicitly wants local logging
            print(f"📝 Using local logging (forced) in {self.environment} environment")
            self.use_cloud_logging = False
            self.cloud_logging_client = None
        elif force_cloud:
            # User explicitly wants cloud logging
            print(f"☁️  Attempting cloud logging (forced) in {self.environment} environment")
            self._try_cloud_logging(logger_name)
        else:
            # Automatic behavior based on environment
            if self.environment == "cloud_function":
                # In Cloud Functions, prefer cloud logging with fallback
                print(f"☁️  Cloud Function detected - using cloud logging with fallback")
                self._try_cloud_logging(logger_name)
            elif self.environment == "gcp":
                # In GCP but not Cloud Function, try cloud logging
                print(f"☁️  GCP environment detected - attempting cloud logging")
                self._try_cloud_logging(logger_name)
            else:
                # Local environment, use local logging
                print(f"📝 Local environment detected - using local logging")
                self.use_cloud_logging = False
                self.cloud_logging_client = None
    
    def _setup_python_logger(self, logger_name):
        """Set up Python logger with proper configuration.
        
        Args:
            logger_name (str): Name of the logger
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Only add handler if none exists (prevents duplicate handlers)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _is_ssl_error(self, error):
        """Check if an error is SSL/TLS related.
        
        Args:
            error (Exception): The error to check
            
        Returns:
            bool: True if the error is SSL/TLS related
        """
        error_msg = str(error).lower()
        ssl_indicators = [
            'ssl', 'tls', 'corruption', 'stream removed', 'decryption error',
            'bad_record_mac', 'tsi_data_corrupted', 'sslv3_alert_bad_record_mac',
            'ssl routines', 'openssl_internal', 'secure_endpoint', 'unknown: none stream removed',
            'ssl_transport_security_utils', 'corruption detected'
        ]
        return any(indicator in error_msg for indicator in ssl_indicators)
    
    def _try_cloud_logging(self, logger_name):
        """Attempt to initialize Google Cloud Logging with enhanced error handling.
        
        Args:
            logger_name (str): Name of the logger
        """
        try:
            # Get credentials using Google Auth default
            credentials, _ = default()
            
            # Set up Google Cloud Logging with default credentials and project
            self.cloud_logging_client = cloud_logging.Client(
                credentials=credentials,
                project=self.project_id
            )
            
            # Test the connection with a simple operation
            self.cloud_logging_client.setup_logging()
            
            # If we get here, cloud logging is working
            self.use_cloud_logging = True
            print(f"✅ Cloud logging initialized successfully for project: {self.project_id}")
            
        except Exception as e:
            # Handle specific SSL/TLS errors
            if self._is_ssl_error(e):
                print(f"⚠️  SSL/TLS error detected during initialization, falling back to local logging: {e}")
            else:
                print(f"⚠️  Cloud logging initialization failed, falling back to local logging: {e}")
            
            # Set cloud logging client to None to indicate fallback mode
            self.cloud_logging_client = None
            self.use_cloud_logging = False
            print("📝 Using local Python logging as fallback")

    def _handle_ssl_error(self, error, operation="logging"):
        """Handle SSL errors with retry logic and fallback.
        
        Args:
            error (Exception): The SSL error that occurred
            operation (str): Description of the operation that failed
        """
        with self._lock:
            self.ssl_error_count += 1
            
            if self.ssl_error_count <= self.max_ssl_errors:
                print(f"⚠️  SSL error #{self.ssl_error_count} during {operation}: {error}")
                print(f"🔄 Retrying in {self.retry_delay:.1f} seconds...")
                
                # Exponential backoff
                time.sleep(self.retry_delay)
                self.retry_delay = min(self.retry_delay * 2, 30.0)  # Cap at 30 seconds
                
                return True  # Indicate retry should be attempted
            else:
                print(f"🚫 Maximum SSL errors ({self.max_ssl_errors}) reached, switching to local logging permanently")
                self.use_cloud_logging = False
                self.cloud_logging_client = None
                return False  # Indicate no more retries

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
            try:
                extra_str = json.dumps(extra)
                return f"{msg} | Extra: {extra_str}"
            except (TypeError, ValueError):
                # If JSON serialization fails, convert to string
                extra_str = str(extra)
                return f"{msg} | Extra: {extra_str}"
        return msg

    def _safe_cloud_log(self, level, msg, extra=None, max_retries=2):
        """Safely log to cloud logging with enhanced error handling and retry logic.
        
        Args:
            level (str): Log level ('info', 'warning', 'error', 'debug')
            msg (str): Message to log
            extra (dict, optional): Additional parameters
            max_retries (int): Maximum number of retry attempts
        """
        if not self.use_cloud_logging or not self.cloud_logging_client:
            return
        
        formatted_msg = self._format_message(msg, extra)
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Use the appropriate logging method
                if level == 'info':
                    self.logger.info(formatted_msg)
                elif level == 'warning':
                    self.logger.warning(formatted_msg)
                elif level == 'error':
                    self.logger.error(formatted_msg)
                elif level == 'debug':
                    self.logger.debug(formatted_msg)
                
                # If we get here, logging succeeded
                return
                
            except Exception as e:
                retry_count += 1
                
                if self._is_ssl_error(e):
                    # Handle SSL error with retry logic
                    if self._handle_ssl_error(e, f"{level} logging"):
                        continue  # Retry the operation
                    else:
                        # Permanent fallback to local logging
                        break
                else:
                    # Non-SSL error, log locally and continue
                    print(f"⚠️  Non-SSL cloud logging error, switching to local: {e}")
                    break
        
        # Fallback to local logging
        self._local_log(level, msg, extra)

    def _local_log(self, level, msg, extra=None):
        """Log using local Python logging.
        
        Args:
            level (str): Log level ('info', 'warning', 'error', 'debug')
            msg (str): Message to log
            extra (dict, optional): Additional parameters
        """
        formatted_msg = self._format_message(msg, extra)
        
        if level == 'info':
            self.logger.info(formatted_msg)
        elif level == 'warning':
            self.logger.warning(formatted_msg)
        elif level == 'error':
            self.logger.error(formatted_msg)
        elif level == 'debug':
            self.logger.debug(formatted_msg)

    def info(self, msg, extra=None):
        """Log an info message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        if self.use_cloud_logging:
            self._safe_cloud_log('info', msg, extra)
        else:
            self._local_log('info', msg, extra)

    def warning(self, msg, extra=None):
        """Log a warning message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        if self.use_cloud_logging:
            self._safe_cloud_log('warning', msg, extra)
        else:
            self._local_log('warning', msg, extra)

    def error(self, msg, extra=None):
        """Log an error message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        if self.use_cloud_logging:
            self._safe_cloud_log('error', msg, extra)
        else:
            self._local_log('error', msg, extra)

    def debug(self, msg, extra=None):
        """Log a debug message.
        
        Args:
            msg (str): The message to log
            extra (dict, optional): Additional parameters to include
        """
        if self.use_cloud_logging:
            self._safe_cloud_log('debug', msg, extra)
        else:
            self._local_log('debug', msg, extra)

    def get_status(self):
        """Get the current logging status.
        
        Returns:
            dict: Status information including environment, cloud logging availability, and SSL error count
        """
        return {
            'environment': self.environment,
            'cloud_logging_available': self.use_cloud_logging,
            'project_id': self.project_id,
            'prefix': self.prefix,
            'logger_name': self.logger.name,
            'ssl_error_count': self.ssl_error_count,
            'max_ssl_errors': self.max_ssl_errors,
            'current_retry_delay': self.retry_delay
        }

    def reset_ssl_error_count(self):
        """Reset the SSL error count to allow retrying cloud logging.
        
        This can be useful if SSL issues were temporary and you want to
        attempt cloud logging again.
        """
        with self._lock:
            self.ssl_error_count = 0
            self.retry_delay = 1.0
            print("🔄 SSL error count reset - cloud logging will be attempted again")
