"""
Memory Bank Manager for Push Notion

This module provides functionality to:
1. Track Notion page operations
2. Maintain sync status
3. Log errors and resolutions
4. Cache configurations
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from packages.Logging import CloudLogger

class MemoryBank:
    """Manages persistent storage for Push Notion operations."""
    
    def __init__(self):
        """Initialize the memory bank."""
        self.logger = CloudLogger(logger_name='Memory_Bank')
        self.base_path = 'memory-bank'
        self._ensure_directory()
        self._initialize_files()
    
    def _ensure_directory(self):
        """Ensure memory bank directory exists."""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
    
    def _initialize_files(self):
        """Initialize memory bank files with default structures."""
        self._write_json('notion_pages.json', {
            "pages": {},
            "last_updated": None,
            "metadata": {
                "total_pages": 0,
                "last_sync": None
            }
        })
        
        self._write_json('sync_status.json', {
            "last_successful_sync": None,
            "sync_history": [],
            "current_status": "initialized",
            "error_count": 0,
            "success_count": 0
        })
        
        self._write_json('error_log.json', {
            "errors": [],
            "patterns": {},
            "resolutions": {},
            "last_error": None,
            "error_stats": {
                "total_errors": 0,
                "resolved_errors": 0
            }
        })
        
        self._write_json('config_cache.json', {
            "notion_settings": {
                "api_version": "2022-06-28",
                "retry_attempts": 3,
                "timeout_seconds": 30
            },
            "logging_settings": {
                "log_level": "INFO",
                "structured_logging": True
            },
            "cache_settings": {
                "ttl_seconds": 3600,
                "max_entries": 1000
            },
            "last_config_update": None
        })
    
    def _write_json(self, filename: str, data: Dict):
        """Write data to a JSON file."""
        filepath = os.path.join(self.base_path, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _read_json(self, filename: str) -> Dict:
        """Read data from a JSON file."""
        filepath = os.path.join(self.base_path, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"File not found: {filename}")
            return {}
    
    def update_page(self, page_id: str, data: Dict):
        """Update or create a page entry."""
        pages = self._read_json('notion_pages.json')
        pages['pages'][page_id] = {
            **data,
            'last_updated': datetime.now().isoformat()
        }
        pages['last_updated'] = datetime.now().isoformat()
        pages['metadata']['total_pages'] = len(pages['pages'])
        self._write_json('notion_pages.json', pages)
    
    def update_sync_status(self, status: str, error: Optional[str] = None):
        """Update sync status and history."""
        sync_data = self._read_json('sync_status.json')
        sync_data['current_status'] = status
        sync_data['last_successful_sync'] = (
            datetime.now().isoformat() if status == 'completed' 
            else sync_data['last_successful_sync']
        )
        
        sync_data['sync_history'].append({
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'error': error
        })
        
        if status == 'completed':
            sync_data['success_count'] += 1
        elif status == 'failed':
            sync_data['error_count'] += 1
            
        self._write_json('sync_status.json', sync_data)
    
    def log_error(self, error: Exception):
        """Log an error and update error statistics."""
        error_data = self._read_json('error_log.json')
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'message': str(error)
        }
        
        error_data['errors'].append(error_entry)
        error_data['last_error'] = error_entry
        error_data['error_stats']['total_errors'] += 1
        
        # Update error patterns
        error_type = type(error).__name__
        if error_type not in error_data['patterns']:
            error_data['patterns'][error_type] = 0
        error_data['patterns'][error_type] += 1
        
        self._write_json('error_log.json', error_data)
    
    def update_config(self, config: Dict):
        """Update configuration cache."""
        config_data = self._read_json('config_cache.json')
        config_data.update(config)
        config_data['last_config_update'] = datetime.now().isoformat()
        self._write_json('config_cache.json', config_data)
    
    def get_config(self) -> Dict:
        """Get current configuration."""
        return self._read_json('config_cache.json')
    
    def get_page(self, page_id: str) -> Optional[Dict]:
        """Get page data by ID."""
        pages = self._read_json('notion_pages.json')
        return pages['pages'].get(page_id)
    
    def get_sync_status(self) -> Dict:
        """Get current sync status."""
        return self._read_json('sync_status.json')
    
    def get_error_stats(self) -> Dict:
        """Get error statistics."""
        return self._read_json('error_log.json')['error_stats'] 