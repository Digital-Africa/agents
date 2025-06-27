"""
Git Webhook Package for Puppy

Provides comprehensive Git webhook functionality including:
- Creating pull requests
- Editing pull request status
- Merging to dev branch
- Sending status notifications when changes occur

Uses SecretAccessor for credentials and CloudLogger for logging.
"""

import json
import hmac
import hashlib
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
from flask import Flask, request, jsonify
from packages.SecretAccessor import SecretAccessor
from packages.Logging import CloudLogger


class GitProvider(ABC):
    """Abstract base class for Git providers (GitHub, GitLab, etc.)"""
    
    @abstractmethod
    def create_pull_request(self, repo: str, base_branch: str, head_branch: str, 
                          title: str, description: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def update_pull_request_status(self, repo: str, pr_id: str, status: str, 
                                 context: str, description: str) -> bool:
        pass
    
    @abstractmethod
    def merge_pull_request(self, repo: str, pr_id: str, merge_method: str = "squash") -> bool:
        pass
    
    @abstractmethod
    def get_pull_request(self, repo: str, pr_id: str) -> Optional[Dict[str, Any]]:
        pass


class GitHubProvider(GitProvider):
    """GitHub-specific implementation of Git provider"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Puppy-Git-Webhook"
        }
    
    def create_pull_request(self, repo: str, base_branch: str, head_branch: str, 
                          title: str, description: str) -> Dict[str, Any]:
        """Create a pull request on GitHub"""
        url = f"{self.base_url}/repos/{repo}/pulls"
        data = {
            "title": title,
            "body": description,
            "head": head_branch,
            "base": base_branch
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_pull_request_status(self, repo: str, pr_id: str, status: str, 
                                 context: str, description: str) -> bool:
        """Update pull request status (commit status) on GitHub"""
        # Get the latest commit SHA from the PR
        pr_data = self.get_pull_request(repo, pr_id)
        if not pr_data:
            return False
        
        commit_sha = pr_data["head"]["sha"]
        url = f"{self.base_url}/repos/{repo}/statuses/{commit_sha}"
        
        data = {
            "state": status.lower(),
            "target_url": f"https://github.com/{repo}/pull/{pr_id}",
            "description": description,
            "context": context
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.status_code == 201
    
    def merge_pull_request(self, repo: str, pr_id: str, merge_method: str = "squash") -> bool:
        """Merge a pull request on GitHub"""
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_id}/merge"
        data = {"merge_method": merge_method}
        
        response = requests.put(url, headers=self.headers, json=data)
        return response.status_code == 200
    
    def get_pull_request(self, repo: str, pr_id: str) -> Optional[Dict[str, Any]]:
        """Get pull request details from GitHub"""
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_id}"
        
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None


class StatusManager:
    """Manages pull request status operations"""
    
    def __init__(self, git_provider: GitProvider, logger: CloudLogger):
        self.git_provider = git_provider
        self.logger = logger
    
    def set_status(self, repo: str, pr_id: str, status: str, context: str, 
                  description: str) -> bool:
        """Set status for a pull request"""
        try:
            success = self.git_provider.update_pull_request_status(
                repo, pr_id, status, context, description
            )
            if success:
                self.logger.info(f"Status updated for PR {pr_id}: {status} - {description}")
            else:
                self.logger.error(f"Failed to update status for PR {pr_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error updating status for PR {pr_id}: {e}")
            return False
    
    def set_pending(self, repo: str, pr_id: str, context: str = "puppy/ci") -> bool:
        """Set pending status"""
        return self.set_status(repo, pr_id, "pending", context, "Processing...")
    
    def set_success(self, repo: str, pr_id: str, context: str = "puppy/ci", 
                   description: str = "All checks passed") -> bool:
        """Set success status"""
        return self.set_status(repo, pr_id, "success", context, description)
    
    def set_failure(self, repo: str, pr_id: str, context: str = "puppy/ci", 
                   description: str = "Checks failed") -> bool:
        """Set failure status"""
        return self.set_status(repo, pr_id, "failure", context, description)


class NotificationManager:
    """Manages status notifications"""
    
    def __init__(self, logger: CloudLogger):
        self.logger = logger
    
    def send_status_notification(self, pr_id: str, status: str, message: str, 
                               repo: str = None) -> None:
        """Send status notification (placeholder for Slack/Notion integration)"""
        notification_data = {
            "pr_id": pr_id,
            "status": status,
            "message": message,
            "repo": repo,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Status notification: {json.dumps(notification_data)}")
        
        # TODO: Integrate with Slack.py and Notion.py for actual notifications
        # Example:
        # from packages.Slack import SlackIntegration
        # slack = SlackIntegration()
        # slack.send_message(channel="#git-updates", message=message)


class WebhookHandler:
    """Handles webhook events from Git providers"""
    
    def __init__(self, git_provider: GitProvider, status_manager: StatusManager, 
                 notification_manager: NotificationManager, logger: CloudLogger):
        self.git_provider = git_provider
        self.status_manager = status_manager
        self.notification_manager = notification_manager
        self.logger = logger
    
    def handle_push_event(self, payload: Dict[str, Any]) -> None:
        """Handle push events"""
        try:
            repo = payload["repository"]["full_name"]
            ref = payload["ref"]
            commits = payload.get("commits", [])
            
            self.logger.info(f"Push event: {len(commits)} commits to {ref} in {repo}")
            
            # Auto-create PR for feature branches
            if ref.startswith("refs/heads/feature/"):
                branch_name = ref.replace("refs/heads/", "")
                self._create_feature_pr(repo, branch_name, commits)
                
        except Exception as e:
            self.logger.error(f"Error handling push event: {e}")
    
    def handle_pull_request_event(self, payload: Dict[str, Any]) -> None:
        """Handle pull request events"""
        try:
            action = payload["action"]
            pr_data = payload["pull_request"]
            repo = payload["repository"]["full_name"]
            pr_id = str(pr_data["number"])
            
            self.logger.info(f"PR event: {action} for PR #{pr_id} in {repo}")
            
            if action == "opened":
                self.status_manager.set_pending(repo, pr_id)
                self.notification_manager.send_status_notification(
                    pr_id, "opened", f"New PR opened: {pr_data['title']}", repo
                )
            elif action == "synchronize":
                self.status_manager.set_pending(repo, pr_id)
                
        except Exception as e:
            self.logger.error(f"Error handling PR event: {e}")
    
    def handle_status_event(self, payload: Dict[str, Any]) -> None:
        """Handle status events"""
        try:
            state = payload["state"]
            context = payload["context"]
            sha = payload["sha"]
            repo = payload["repository"]["full_name"]
            
            self.logger.info(f"Status event: {state} for {context} in {repo}")
            
            # Find PRs associated with this commit
            # This would require additional API calls to map commit to PR
            
        except Exception as e:
            self.logger.error(f"Error handling status event: {e}")
    
    def _create_feature_pr(self, repo: str, branch_name: str, commits: List[Dict]) -> None:
        """Auto-create PR for feature branch"""
        try:
            title = f"Feature: {branch_name.replace('feature/', '')}"
            description = f"Auto-generated PR for {branch_name}\n\nCommits:\n"
            for commit in commits:
                description += f"- {commit['message']}\n"
            
            pr_data = self.git_provider.create_pull_request(
                repo, "dev", branch_name, title, description
            )
            
            self.logger.info(f"Auto-created PR #{pr_data['number']} for {branch_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating feature PR: {e}")


class GitWebhookManager:
    """Main class for managing Git webhook operations"""
    
    def __init__(self, provider: str = "github", secret_name: str = "GITHUB_TOKEN"):
        """Initialize the Git webhook manager"""
        self.provider = provider
        self.logger = CloudLogger("GitWebhookManager")
        
        # Initialize secret accessor
        self.secret_accessor = SecretAccessor()
        token = self.secret_accessor.get_secret(secret_name)
        
        # Initialize Git provider
        if provider.lower() == "github":
            self.git_provider = GitHubProvider(token)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Initialize managers
        self.status_manager = StatusManager(self.git_provider, self.logger)
        self.notification_manager = NotificationManager(self.logger)
        self.webhook_handler = WebhookHandler(
            self.git_provider, self.status_manager, self.notification_manager, self.logger
        )
        
        self.logger.info(f"GitWebhookManager initialized for {provider}")
    
    def create_pull_request(self, repo: str, base_branch: str, head_branch: str, 
                          title: str, description: str) -> Optional[Dict[str, Any]]:
        """Create a pull request"""
        try:
            pr_data = self.git_provider.create_pull_request(
                repo, base_branch, head_branch, title, description
            )
            self.logger.info(f"Created PR #{pr_data['number']} in {repo}")
            return pr_data
        except Exception as e:
            self.logger.error(f"Error creating PR: {e}")
            return None
    
    def update_pr_status(self, repo: str, pr_id: str, status: str, context: str = "puppy/ci", 
                        description: str = None) -> bool:
        """Update pull request status"""
        if description is None:
            if status == "success":
                description = "All checks passed"
            elif status == "failure":
                description = "Checks failed"
            elif status == "pending":
                description = "Processing..."
            else:
                description = f"Status: {status}"
        
        return self.status_manager.set_status(repo, pr_id, status, context, description)
    
    def merge_to_dev(self, repo: str, pr_id: str, merge_method: str = "squash") -> bool:
        """Merge pull request to dev branch"""
        try:
            success = self.git_provider.merge_pull_request(repo, pr_id, merge_method)
            if success:
                self.logger.info(f"Merged PR #{pr_id} to dev in {repo}")
                self.notification_manager.send_status_notification(
                    pr_id, "merged", f"PR #{pr_id} merged to dev", repo
                )
            else:
                self.logger.error(f"Failed to merge PR #{pr_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error merging PR #{pr_id}: {e}")
            return False
    
    def handle_webhook_event(self, event_type: str, payload: Dict[str, Any], 
                           signature: str = None) -> Dict[str, Any]:
        """Handle incoming webhook events"""
        try:
            # Verify webhook signature if provided
            if signature and not self._verify_signature(payload, signature):
                self.logger.error("Invalid webhook signature")
                return {"error": "Invalid signature"}
            
            # Route event to appropriate handler
            if event_type == "push":
                self.webhook_handler.handle_push_event(payload)
            elif event_type == "pull_request":
                self.webhook_handler.handle_pull_request_event(payload)
            elif event_type == "status":
                self.webhook_handler.handle_status_event(payload)
            else:
                self.logger.warning(f"Unhandled event type: {event_type}")
            
            return {"status": "processed"}
            
        except Exception as e:
            self.logger.error(f"Error handling webhook event: {e}")
            return {"error": str(e)}
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature (GitHub specific)"""
        try:
            # Get webhook secret from SecretAccessor
            webhook_secret = self.secret_accessor.get_secret("GITHUB_WEBHOOK_SECRET")
            
            # Create expected signature
            payload_str = json.dumps(payload, separators=(',', ':'))
            expected_signature = "sha256=" + hmac.new(
                webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying signature: {e}")
            return False


# Flask application for webhook endpoints
app = Flask(__name__)
git_manager = None


@app.route('/webhook/git', methods=['POST'])
def webhook_endpoint():
    """Main webhook endpoint"""
    global git_manager
    
    if git_manager is None:
        git_manager = GitWebhookManager()
    
    # Get event type and signature
    event_type = request.headers.get('X-GitHub-Event')
    signature = request.headers.get('X-Hub-Signature-256')
    
    if not event_type:
        return jsonify({"error": "Missing event type"}), 400
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        return jsonify({"error": "Invalid JSON payload"}), 400
    
    # Handle event
    result = git_manager.handle_webhook_event(event_type, payload, signature)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result), 200


@app.route('/webhook/git/status', methods=['POST'])
def status_endpoint():
    """Status update endpoint"""
    global git_manager
    
    if git_manager is None:
        git_manager = GitWebhookManager()
    
    try:
        data = request.get_json()
        repo = data.get('repo')
        pr_id = data.get('pr_id')
        status = data.get('status')
        context = data.get('context', 'puppy/ci')
        description = data.get('description')
        
        if not all([repo, pr_id, status]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = git_manager.update_pr_status(repo, pr_id, status, context, description)
        
        if success:
            return jsonify({"status": "updated"}), 200
        else:
            return jsonify({"error": "Failed to update status"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/webhook/git/merge', methods=['POST'])
def merge_endpoint():
    """Manual merge trigger endpoint"""
    global git_manager
    
    if git_manager is None:
        git_manager = GitWebhookManager()
    
    try:
        data = request.get_json()
        repo = data.get('repo')
        pr_id = data.get('pr_id')
        merge_method = data.get('merge_method', 'squash')
        
        if not all([repo, pr_id]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = git_manager.merge_to_dev(repo, pr_id, merge_method)
        
        if success:
            return jsonify({"status": "merged"}), 200
        else:
            return jsonify({"error": "Failed to merge"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "git-webhook"}), 200


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
