import requests
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the integration"""
    SONARCLOUD_URL = "https://sonarcloud.io"
    PROJECT_KEY = "fuzailAhmad123_automated-issue-creation-via-sonarqube"
    ORGANIZATION_KEY = "fuzailahmad123"
    SONAR_TOKEN = os.environ.get("SONAR_TOKEN")
    PAT_TOKEN = os.environ.get("PAT_TOKEN")
    MIN_SEVERITY = "MAJOR"
    GITHUB_REPO_OWNER = "fuzailAhmad123"
    GITHUB_REPO_NAME = "automated-issue-creation-via-sonarqube"
    
    # Additional configuration options
    ISSUES_LOOKBACK_DAYS = 1  # Look for issues created in the last day
    REQUEST_TIMEOUT = 30  # Timeout for API requests in seconds
    MAX_RETRIES = 3  # Maximum number of retries for API requests

    # Map severity levels to numeric values
    SEVERITY_LEVELS = {
        "BLOCKER": 5,
        "CRITICAL": 4,
        "MAJOR": 3,
        "MINOR": 2,
        "INFO": 1
    }

def get_sonarcloud_issues() -> List[Dict[str, Any]]:
    """
    Fetch new issues from SonarCloud with pagination support
    
    Returns:
        List of SonarCloud issues
    """
    issues = []
    page = 1
    page_size = 100
    
    # Use a lookback period instead of just today
    lookback_date = (datetime.now() - timedelta(days=Config.ISSUES_LOOKBACK_DAYS)).date().isoformat()
    
    while True:
        url = f"{Config.SONARCLOUD_URL}/api/issues/search"
        params = {
            "componentKeys": Config.PROJECT_KEY,
            "organization": Config.ORGANIZATION_KEY,
            "resolved": "false",
            "severities": "BLOCKER,CRITICAL,MAJOR",
            "statuses": "OPEN,CONFIRMED",
            "createdAfter": lookback_date,
            "p": page,
            "ps": page_size
        }
        
        headers = {
            "Authorization": f"Bearer {Config.SONAR_TOKEN}"
        }
        
        try:
            for attempt in range(Config.MAX_RETRIES):
                try:
                    response = requests.get(
                        url, 
                        params=params, 
                        headers=headers, 
                        timeout=Config.REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    break
                except (requests.RequestException, requests.Timeout) as e:
                    if attempt < Config.MAX_RETRIES - 1:
                        logger.warning(f"Attempt {attempt+1} failed: {str(e)}. Retrying...")
                        continue
                    raise
            
            data = response.json()
            batch_issues = data.get("issues", [])
            issues.extend(batch_issues)
            
            # Check if we've received all issues
            total = data.get("total", 0)
            if page * page_size >= total:
                break
                
            page += 1
            
        except requests.RequestException as e:
            logger.error(f"Error fetching SonarCloud issues: {str(e)}")
            break
    
    return issues

def get_next_github_issue_number() -> int:
    """
    Get the next GitHub issue number by finding the highest current issue number
    
    Returns:
        int: The next issue number (current highest + 1)
    """
    url = f"https://api.github.com/repos/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}/issues"
    params = {
        "state": "all",
        "per_page": 1,
        "sort": "created", 
        "direction": "desc"
    }
    
    headers = {
        "Authorization": f"token {Config.PAT_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=Config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                issues = response.json()
                if issues:
                    # The number of the most recent issue plus 1
                    return issues[0]["number"] + 1
                else:
                    # If no issues exist yet
                    return 1
                
            except (requests.RequestException, requests.Timeout) as e:
                if attempt < Config.MAX_RETRIES - 1:
                    logger.warning(f"Attempt {attempt+1} failed when getting next issue number: {str(e)}. Retrying...")
                    continue
                raise
                
    except Exception as e:
        logger.error(f"Error determining next GitHub issue number: {str(e)}")
        # Return 0 if we couldn't determine the next issue number
        return 0

def create_github_issue(issue: Dict[str, Any], next_number: int) -> Tuple[bool, int]:
    """
    Create a GitHub issue from a SonarCloud issue with expected issue number in title
    
    Args:
        issue: SonarCloud issue data
        next_number: Expected issue number to include in the title
        
    Returns:
        Tuple[bool, int]: Success status and actual issue number
    """
    url = f"https://api.github.com/repos/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}/issues"
    
    # Extract issue details
    component = issue.get('component', '')
    file_path = component.replace(f"{Config.PROJECT_KEY}:", "")
    line = issue.get('line', 'Unknown')
    issue_key = issue.get('key', '')
    severity = issue.get('severity', '')
    issue_type = issue.get('type', '')
    message = issue.get('message', '')
    rule = issue.get('rule', '')
    
    # Create a title with expected issue number
    title_prefix = f"#{next_number}" if next_number > 0 else ""
    title = f"{title_prefix} [{severity}] {issue_type}: {message[:80]}{'...' if len(message) > 80 else ''}"
    
    # Create a more detailed body with markdown formatting
    body = f"""
## SonarCloud Issue: {title_prefix}

### Details
- **Rule**: {rule}
- **Severity**: {severity}
- **Type**: {issue_type}
- **File**: `{file_path}`
- **Line**: {line}

### Message
{message}

### Links
- [View in SonarCloud]({Config.SONARCLOUD_URL}/project/issues?id={Config.PROJECT_KEY}&issues={issue_key}&open={issue_key})
- [SonarCloud Rule Definition]({Config.SONARCLOUD_URL}/coding_rules?open={rule}&rule_key={rule})
"""
    
    data = {
        "title": title,
        "body": body,
        "labels": ["sonarcloud", f"severity:{severity.lower()}", f"type:{issue_type.lower()}"]
    }
    
    headers = {
        "Authorization": f"token {Config.PAT_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.post(
                    url, 
                    headers=headers, 
                    data=json.dumps(data),
                    timeout=Config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                result = response.json()
                issue_url = result.get('html_url', '')
                actual_number = result.get('number', 0)
                logger.info(f"Created GitHub issue #{actual_number}: {issue_url}")
                return True, actual_number
            except (requests.RequestException, requests.Timeout) as e:
                if attempt < Config.MAX_RETRIES - 1:
                    logger.warning(f"Attempt {attempt+1} failed: {str(e)}. Retrying...")
                    continue
                raise
    except requests.RequestException as e:
        logger.error(f"Error creating GitHub issue: {str(e)}")
        return False, 0

def should_create_issue(issue: Dict[str, Any]) -> bool:
    """
    Determine if an issue should trigger GitHub issue creation
    
    Args:
        issue: SonarCloud issue data
        
    Returns:
        bool: True if issue should be created, False otherwise
    """
    issue_severity = Config.SEVERITY_LEVELS.get(issue.get('severity', 'INFO'), 0)
    min_severity_level = Config.SEVERITY_LEVELS.get(Config.MIN_SEVERITY, 0)
    
    # Check if we already have an issue for this SonarCloud issue
    # This would require checking existing GitHub issues, which could be added here
    
    return issue_severity >= min_severity_level

def check_prerequisites() -> bool:
    """
    Check if all required environment variables and configuration are set
    
    Returns:
        bool: True if all prerequisites are met, False otherwise
    """
    missing = []
    
    if not Config.SONAR_TOKEN:
        missing.append("SONAR_TOKEN")
    if not Config.PAT_TOKEN:
        missing.append("PAT_TOKEN")
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    return True

def main() -> None:
    """
    Main function to fetch issues from SonarCloud and create issues on GitHub
    """
    logger.info("Starting SonarCloud to GitHub integration")
    
    if not check_prerequisites():
        return
    
    try:
        logger.info("Fetching issues from SonarCloud")
        issues = get_sonarcloud_issues()
        
        if not issues:
            logger.info("No new issues found")
            return
        
        logger.info(f"Found {len(issues)} issues")
        
        # Get the next expected GitHub issue number
        next_issue_number = get_next_github_issue_number()
        logger.info(f"Next expected GitHub issue number: #{next_issue_number}")
        
        created_count = 0
        skipped_count = 0
        current_number = next_issue_number
        
        for issue in issues:
            if should_create_issue(issue):
                logger.info(f"Creating GitHub issue (expected #{current_number}) for: {issue.get('message', '')[:80]}...")
                success, actual_number = create_github_issue(issue, current_number)
                if success:
                    created_count += 1
                    # Update our tracking of the current number based on what GitHub actually assigned
                    if actual_number > 0:
                        current_number = actual_number + 1
                    else:
                        current_number += 1
            else:
                skipped_count += 1
                logger.debug(f"Skipping issue (below severity threshold): {issue.get('message', '')[:80]}...")
        
        logger.info(f"Process completed. Created {created_count} issues, skipped {skipped_count} issues")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()