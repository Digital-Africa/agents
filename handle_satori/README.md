# 🐕 Puppy - Satori Data Handler

## Executive Summary

Think of this as your **automatic data organizer** for startup information. When you upload CSV files containing startup data, cofounder details, or important documents, this system automatically sorts everything into the right digital folders - just like having a very smart assistant who never makes mistakes and works 24/7.

**What it does**: Upload a CSV file → Magic happens → Your data is perfectly organized in Google's cloud database.

## How it Works (Simple Version)

1. **Upload**: Drop a CSV file into our Google Cloud Storage bucket
2. **Process**: The system reads the file and organizes the data
3. **Store**: Everything gets stored in the right place with proper labels
4. **Track**: Each piece of data is tracked with status and timestamps

## Testing Workflow

### Local Testing
```bash
# Install dependencies
pip install -r local_requirements.txt

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your test credentials

# Run the function locally
python test_function.py
```

### Cloud Testing
1. Upload a test CSV file to the `fuze-subscriptions` bucket
2. Monitor Cloud Function logs for processing status
3. Verify documents are created in Firestore collections
4. Check execution status and timestamps

### Test Data Requirements
- **Startups file**: Must contain "startups" in filename
- **Cofounders file**: Must contain "cofounder" in filename
- **CSV format**: First row should be headers, data starts from row 2

---

## Technical Architecture

### Philosophy
This agent follows the **Puppy Developer Rules**:
- **Composable & Stateless**: Each function is independent and can be tested in isolation
- **Secrets Management**: All sensitive data is stored in Google Secret Manager
- **Logging First**: Every operation is logged using `Logging.py`
- **Modular Design**: Functions are testable and reusable
- **Minimal IAM**: Only necessary permissions are granted

### Cloud Native Design
- **Runtime**: Google Cloud Functions (Gen2)
- **Storage**: Google Cloud Storage (`fuze-subscriptions` bucket)
- **Database**: Firestore (`memory-bank` database)
- **Messaging**: Pub/Sub for asynchronous operations
- **Scheduling**: Cloud Tasks for job management

### Key Packages
- `Logging.py`: Structured logging wrapper
- `SecretAccessor.py`: Secure secret management
- `Firestore.py`: Database operations with batch support
- `storage.py`: GCS file operations

## Data Processing Flow

```
[CSV Upload to GCS]
        ↓
[Cloud Function Trigger]
        ↓
[File Type Detection]
        ↓
[CSV Processing & Validation]
        ↓
[Batch Document Creation]
        ↓
[Firestore Storage]
        ↓
[Status Tracking & Logging]
```

## File Types & Collections

### Startups Processing
- **Trigger**: Files with "startups" in name
- **Collections**: `startups` + `memos` (auto-generated)
- **Data Fields**: Company profile, sector, innovation, awards, etc.

### Cofounders Processing  
- **Trigger**: Files with "cofounder" in name
- **Collection**: `cofounders`
- **Data Fields**: Founder details, contact info, nationality, etc.

### Document Structure
```json
{
  "payload": {
    // File-specific data
  },
  "execution_status": "pending|not started",
  "source_file": "original_filename.csv",
  "timestamp": "ISO timestamp",
  "satori_id": "unique_identifier"
}
```

## Performance Features

### Batch Operations
- **Efficient Processing**: Uses Firestore batch writes for optimal performance
- **Atomic Operations**: All documents succeed or fail together
- **Reduced Network Calls**: Single batch commit instead of individual writes

### Error Handling
- **Comprehensive Logging**: Every operation is logged with context
- **Graceful Failures**: Errors are caught and logged without breaking the system
- **Status Tracking**: Each document tracks its processing status

## Monitoring & Observability

### Logging Strategy
- **Structured Logs**: JSON-formatted logs for easy parsing
- **Context Tracking**: File names, operation types, and timestamps
- **Debug Information**: Detailed logs for troubleshooting
- **Error Context**: Full error details with file context

### Health Checks
- Monitor Cloud Function execution times
- Track batch operation success rates
- Verify document creation counts
- Check for processing errors

## Deployment

### Environment Setup
```bash
# Deploy to Google Cloud Functions
gcloud functions deploy handle_satori \
  --runtime python39 \
  --trigger-event google.storage.object.finalize \
  --trigger-resource fuze-subscriptions \
  --entry-point handle_satori
```

### Configuration
- **Project**: `digital-africa-fuze`
- **Region**: Auto-selected based on deployment
- **Memory**: 256MB (adjustable based on file sizes)
- **Timeout**: 540 seconds (9 minutes)

## Troubleshooting

### Common Issues
1. **File Not Processed**: Check filename contains required keywords
2. **CSV Format Errors**: Verify headers and data structure
3. **Permission Errors**: Check IAM roles for Cloud Function
4. **Batch Failures**: Monitor Firestore quotas and limits

### Debug Steps
1. Check Cloud Function logs for detailed error messages
2. Verify CSV file format and content
3. Test with smaller files first
4. Monitor Firestore collection creation

## Security & Compliance

### Data Protection
- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: IAM-based permissions
- **Audit Logging**: All operations are logged for compliance

### Secret Management
- **No Hardcoded Secrets**: All credentials stored in Secret Manager
- **Environment Variables**: Local development uses `.env.local`
- **Service Accounts**: Minimal permissions principle

## Need Help?

### Support Channels
- **Logs**: Check Cloud Function logs for detailed information
- **Documentation**: This README and inline code comments
- **Testing**: Use the provided test workflow

### Best Practices
- Always test with small files first
- Monitor batch operation performance
- Keep CSV files under 100MB for optimal processing
- Use descriptive filenames for easier tracking

---

*Built with ❤️ following Puppy Developer Rules - because every good system deserves a loyal companion! 🐾* 