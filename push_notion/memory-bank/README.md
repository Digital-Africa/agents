# Memory Bank

This directory serves as a persistent storage for the Push Notion integration, maintaining important information and state across function invocations.

## Structure

The memory bank consists of four main JSON files:

### 1. notion_pages.json
Tracks Notion page operations and metadata:
- Page IDs and their properties
- Last update timestamps
- Total page count
- Sync status

### 2. sync_status.json
Maintains synchronization state:
- Last successful sync
- Sync history
- Current status
- Error and success counts

### 3. error_log.json
Records error information:
- Error history
- Error patterns
- Resolution steps
- Error statistics

### 4. config_cache.json
Stores configuration settings:
- Notion API settings
- Logging configuration
- Cache parameters
- Last update timestamp

## Usage

The memory bank is managed by the `MemoryBank` class in `packages/MemoryBank.py`. It provides methods for:

```python
# Initialize memory bank
memory_bank = MemoryBank()

# Update page information
memory_bank.update_page(page_id, data)

# Track sync status
memory_bank.update_sync_status(status, error)

# Log errors
memory_bank.log_error(exception)

# Update configuration
memory_bank.update_config(new_config)

# Retrieve information
page_data = memory_bank.get_page(page_id)
sync_status = memory_bank.get_sync_status()
error_stats = memory_bank.get_error_stats()
```

## File Formats

### notion_pages.json
```json
{
    "pages": {
        "page_id": {
            "properties": {},
            "last_updated": "timestamp"
        }
    },
    "last_updated": "timestamp",
    "metadata": {
        "total_pages": 0,
        "last_sync": "timestamp"
    }
}
```

### sync_status.json
```json
{
    "last_successful_sync": "timestamp",
    "sync_history": [
        {
            "timestamp": "timestamp",
            "status": "status",
            "error": "error_message"
        }
    ],
    "current_status": "status",
    "error_count": 0,
    "success_count": 0
}
```

### error_log.json
```json
{
    "errors": [
        {
            "timestamp": "timestamp",
            "error_type": "type",
            "message": "message"
        }
    ],
    "patterns": {
        "error_type": count
    },
    "resolutions": {},
    "last_error": {},
    "error_stats": {
        "total_errors": 0,
        "resolved_errors": 0
    }
}
```

### config_cache.json
```json
{
    "notion_settings": {
        "api_version": "version",
        "retry_attempts": 3,
        "timeout_seconds": 30
    },
    "logging_settings": {
        "log_level": "level",
        "structured_logging": true
    },
    "cache_settings": {
        "ttl_seconds": 3600,
        "max_entries": 1000
    },
    "last_config_update": "timestamp"
}
``` 