import requests
import json
import config
from datetime import datetime

def get_sonarcloud_issues():
    """Fetch new issues from SonarCloud"""
    url = f"{config.SONARCLOUD_URL}/api/issues/search"
    params = {
       "componentKeys": config.PROJECT_KEY,
       "organization": config.ORGANIZATION_KEY,
       "resolved": "false",
       "severities": "BLOCKER,CRITICAL,MAJOR",
       "statuses": "OPEN,CONFIRMED",
       "createdAfter": (datetime.now().date().isoformat())
    }

    headers = {
        "Authorization": f"Bearer {config.SONAR_TOKEN}"
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        print(f"Error fetching SonarCloud issues: {response.status_code}, {response.text}")
        return []

def create_github_issue(issue):
    """Create a GitHub issue from a SonarCloud issue"""
    url = f"https://api.github.com/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/issues"

    component = issue.get("component","")
    file_path = component.replace(f"{config.PROJECT_KEY}:", "")
    line = issue.get("line", "Unkown")

    title = f"[{issue.get('severity')}] {issue.get('type')}: {issue.get('message')}"
    body = f""" 
     SonarCloud detected a code quality issue:

     - **Rule** : {issue.get('rule')}
     - **Severity** : {issue.get('severity')}
     - **File** : {file_path}
     - **Line** : {line}
     - **Message** : {issue.get('message')}

     [VIEW IN SONARCLOUD]({config.SONARCLOUD_URL}/project/issues?id={config.PROJECT_KEY}&issues={issue.get('key')}&open={issue.get('key')})
    """

    data = {
        "title": title,
        "body": body,
        "labels": ["sonarcloud", f"severity:{issue.get('severity', '').lower()}"]
    }

    headers = {
        "Authorization" : f"token {config.PAT_TOKEN}",
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
     min_severity_level = severity_levels.get(config.MIN_SEVERITY, 0)

     return issue_severity >= min_severity_level

def main ():
    """Main function to fetch issue from Sonarcloud and create issue on Github"""
    print("Fetching data from SonarCloud")
    issues = get_sonarcloud_issues()

    print(f"found {len(issues)} issues")


    for issue in issues:
        if should_create_issue(issue):
            print(f"Creating GitHub issue for: {issue.get('message', '')}")
            create_github_issue(issue)
        else:
            print(f"Skipping issue (below severity threshold): {issue.get('message')}")

if __name__ == "__main__":
    if not config.SONAR_TOKEN or not config.PAT_TOKEN:
        print("Error: Environment variables SONAR_TOKEN and PAT_TOKEN must be set")
        exit(1)
    main()


