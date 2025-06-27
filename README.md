# 🚀 Puppy Agents - Cloud-Native Microservices Platform

A collection of specialized cloud functions (agents) that work together to create automated workflows for trading alerts, data processing, and communication systems. Built with Google Cloud Functions, these agents handle everything from TradingView alerts to Discord notifications and Notion database updates.

## 🎯 Executive Summary

Think of this as a digital assistant army where each agent has a specific job:
- **Trading Alert Agents**: Listen for market signals and notify you instantly
- **Communication Agents**: Send messages to Discord, Slack, and other platforms
- **Data Processing Agents**: Handle complex calculations and data transformations
- **Storage Agents**: Manage data persistence and retrieval

All agents work together seamlessly, like a well-oiled machine, to automate your trading and business workflows.

## 🏗️ Architecture

```
[External Triggers] → [Agent Functions] → [Cloud Services]
     ↓                      ↓                    ↓
[TradingView]        [purple_gold]        [Discord/Slack]
[Webhooks]           [push_message]       [Notion]
[APIs]               [balance_of]         [Firestore]
                     [backtest]           [Cloud Tasks]
```

### Core Components

- **Google Cloud Functions**: Serverless execution environment
- **Cloud Tasks**: Asynchronous job queuing
- **Secret Manager**: Secure credential storage
- **Firestore**: Document database for state management
- **Cloud Logging**: Centralized logging and monitoring

## 🤖 Available Agents

### Trading & Finance
- **`purple_gold`** - TradingView alert processor for golden/purple cross signals
- **`balance_of`** - Token balance and supply monitoring
- **`push_to_contract`** - Smart contract interaction agent
- **`backtest`** - Trading strategy backtesting
- **`backtest_signal`** - Signal generation for backtesting

### Communication
- **`push_message`** - Multi-platform message dispatcher (Discord, Slack)
- **`push_notion`** - Notion database integration
- **`application_to_notion`** - Application form processing

### Data & Storage
- **`memory-bank`** - Centralized data storage and retrieval
- **`warehouse`** - Data warehouse operations
- **`files`** - File management and processing
- **`archiver`** - Data archival and cleanup

### Business Operations
- **`cofounders`** - Cofounder management system
- **`startups`** - Startup data processing
- **`people_onboarding`** - Onboarding workflow automation
- **`identity`** - Identity verification and management
- **`tiers_card`** - Membership tier management

### Integration & Utilities
- **`webhook`** - Webhook endpoint management
- **`dispatch`** - Task routing and dispatching
- **`github_sync`** - GitHub integration
- **`letterbox`** - Message queuing and delivery
- **`memo`** - Memo and note management
- **`handle_satori`** - Satori platform integration
- **`create_folder`** - Folder structure management

## 🛠️ Setup & Installation

### Prerequisites
- Google Cloud Platform account
- Python 3.8+
- Google Cloud CLI (`gcloud`)
- Access to required APIs (Cloud Functions, Secret Manager, etc.)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agents
   ```

2. **Install dependencies**
   ```bash
   # Install global requirements
   pip install -r requirements.txt
   
   # Install agent-specific requirements
   cd <agent-name>
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create local environment file
   cp .env.example .env.local
   
   # Add your configuration
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   export PROJECT_ID="your-gcp-project-id"
   ```

4. **Configure secrets in Google Secret Manager**
   ```bash
   # Example: Add Discord webhook URL
   gcloud secrets create DISCORD_WEBHOOK_URL --data-file=webhook-url.txt
   ```

### Testing

Run the test suite to ensure everything works:
```bash
make test
```

## 🚀 Deployment

### Individual Agent Deployment

Each agent has its own deployment script:

```bash
cd <agent-name>
./deploy.sh
```

### Bulk Deployment

Deploy all agents at once:
```bash
# Deploy all agents
for agent in */; do
    if [ -f "$agent/deploy.sh" ]; then
        echo "Deploying $agent..."
        cd "$agent" && ./deploy.sh && cd ..
    fi
done
```

### Environment Configuration

Agents are deployed to different environments:
- **Development**: `dev-` prefix
- **Staging**: `staging-` prefix  
- **Production**: No prefix

## 📝 Logging & Monitoring

### Logging Standards

All agents use the `CloudLogger` class for consistent logging:

```python
from packages.Logging import CloudLogger

logger = CloudLogger("agent_name")

# Usage examples
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error conditions")
```

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions that need attention

### Monitoring

- **Cloud Logging**: Centralized log aggregation
- **Cloud Monitoring**: Performance metrics and alerts
- **Error Reporting**: Automatic error tracking

## 🔧 Development Guidelines

### Code Standards

1. **Function Naming**: Use `snake_case` for functions
2. **Agent Naming**: Use `verb_action` format (e.g., `push_message`, `dispatch_webhook`)
3. **Error Handling**: Always use try-catch blocks with proper logging
4. **Documentation**: Include docstrings for all functions

### Package Structure

```
agents/
├── packages/           # Shared utilities
│   ├── Logging.py     # Cloud logging wrapper
│   ├── SecretAccessor.py  # Secret management
│   ├── Notion.py      # Notion API integration
│   ├── Slack.py       # Slack messaging
│   ├── Tasks.py       # Cloud Tasks integration
│   └── ...
├── <agent-name>/      # Individual agents
│   ├── main.py        # Main function
│   ├── requirements.txt
│   ├── deploy.sh      # Deployment script
│   └── tests/         # Unit tests
└── tests/             # Integration tests
```

### Testing Workflow

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test agent interactions
3. **End-to-End Tests**: Test complete workflows

```bash
# Run all tests
make test

# Run specific agent tests
cd <agent-name>
python -m unittest discover tests/
```

## 🔐 Security

### Secret Management
- All sensitive data stored in Google Secret Manager
- No hardcoded credentials in code
- Environment-specific secret versions

### Access Control
- Minimal IAM permissions per agent
- Service account-based authentication
- Network security through VPC if needed

## 📊 Performance

### Optimization Tips
- Use async operations where possible
- Implement proper error handling and retries
- Monitor cold start times
- Use Cloud Tasks for long-running operations

### Monitoring Metrics
- Function execution time
- Memory usage
- Error rates
- Request volume

## 🤝 Contributing

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/new-agent
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test your changes**
   ```bash
   make test
   ```

4. **Submit a pull request**
   - Include a clear description
   - Reference any related issues
   - Ensure all tests pass

### Adding a New Agent

1. **Create agent directory**
   ```bash
   mkdir new_agent
   cd new_agent
   ```

2. **Create required files**
   - `main.py` - Main function
   - `requirements.txt` - Dependencies
   - `deploy.sh` - Deployment script
   - `tests/` - Unit tests

3. **Follow the template**
   ```python
   from packages.Logging import CloudLogger
   
   logger = CloudLogger("new_agent")
   
   def new_agent(request):
       """Agent entry point."""
       logger.info("Processing request")
       # Your logic here
       return {"status": "success"}
   ```

## 📞 Support

### Getting Help
- Check the logs in Cloud Logging
- Review the agent-specific documentation
- Open an issue for bugs or feature requests

### Common Issues
- **Cold Start Delays**: Normal for Cloud Functions, consider keeping functions warm
- **Secret Access Errors**: Verify IAM permissions and secret names
- **Network Timeouts**: Check external service availability

## 📄 License

This project is proprietary and confidential. All rights reserved.

---

**Last Updated**: December 2024  
**Version**: 1.0.0
