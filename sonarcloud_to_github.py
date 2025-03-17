import os
import requests
import json
from datetime import datetime

SONARCLOUD_URL = "https://sonarcloud.io"
PROJECT_KEY = "fuzailAhmad123_automated-issue-creation-via-sonarqube"
ORGANIZATION_KEY = "fuzailahmad123"
SONARCLOUD_TOKEN = os.environ.get("SONAR_TOKEN")
PAT_TOKEN = os.environ.get("PAT_TOKEN")
MIN_SEVERITY= "MAJOR"
GITHUB_REPO_OWNER = "fuzailAhmad123"
GITHUB_REPO_NAME = "automated-issue-creation-via-sonarqube"

def get_sonarcloud_issues():
    """Fetch new issues from SonarCloud"""
    url = f"{SONARCLOUD_URL}/api/issues/search"
    params = {
       "componentKeys": PROJECT_KEY,
       "organization": ORGANIZATION_KEY,
       "resolved": false,
       "severities": "BLOCKER,CRITICAL,MAJOR",
       "statuses": "OPEN,CONFIRMED",
       "createdAfter": (datetime.now().date().isoformat())
    }

    headers = {
        "Authorization": f"Bearer {SONARCLOUD_TOKEN}"
    }

    response = requests.get(urls, params=params, headers=headers)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        print(f"Error fetching SonarCloud issues: {response.status_code}, {response.text}")
        return []

def create_github_issue(issue):
    """Create a GitHub issue from a SonarCloud issue"""
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"

    commponent = issue.get("component","")
    file_path = component.replace(f"{PROJECT_KEY}:", "")
    line = issue.get("line", "Unkown")

    title = f"[{issue.get('severity')}] {issue.get('type')}: {issue.get('message')}"
    body = f""" 
     SonarCloud detected a code quality issue:

     - **Rule** : {issue.get('rule')}
     - **Severity** : {issue.get('severity')}
     - **File** : {file_path}
     - **Line** : {line}
     - **Message** : {issue.get('message')}

     [VIEW IN SONARCLOUD]({SONARCLOUD_URL}/project/issues?id={PROJECT_KEY}&issues={issue.get('key')}&open={issue.get('key')})
    """

    data = {
        "title": title,
        "body": body,
        "labels": [f"sonarcloud", f"severity:{issue.get('severity').lower()}"]
    }

    headers = {
        "Authorization" : f"token {PAT_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print(f"Created GitHub issue: {response.json().get('html_url')}")
        return True
    else:
        print(f"Error creating GitHub issue: {response.status_code}, {response.text}")
        return False

def should_create_issue(issue):
     """Determine if an issue should trigger GitHub issue creation"""
     severity_levels = {
        "BLOCKER": 5,
        "CRITICAL": 4,
        "MAJOR": 3,
        "MINOR": 2,
        "INFO": 1
     }

     issue_severity = severity_levels.get(issue.get("severity", "INFO"), 0)
     min_severity_level = severity_levels.get(MIN_SEVERITY, 0)

     return issue_severity >= min_severity_level

def main ():
    """Main function to fetch issue from Sonarcloud and create issue on Github"""
    print("Fetching data from SonarCloud")
    issues = get_sonarcloud_issues()

    print(f"found {len(issues)} issues")


    for issue in issues:
        if should_create_issue(issue):
            print(f"Creating GitHub issue for: {issue.get('message')}")
            create_github_issue(issue)
        else:
            print(f"Skipping issue (below severity threshold): {issue.get('message')}")

if __name__ == "__main__":
    if not SONARCLOUD_TOKEN or not PAT_TOKEN:
        print("Error: Environment variables SONARCLOUD_TOKEN and PAT_TOKEN must be set")
        exit(1)
    main()