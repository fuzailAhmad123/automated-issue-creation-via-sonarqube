import os

SONARCLOUD_URL = "https://sonarcloud.io"
PROJECT_KEY = "fuzailAhmad123_automated-issue-creation-via-sonarqube"
ORGANIZATION_KEY = "fuzailahmad123"
SONAR_TOKEN = os.environ.get("SONAR_TOKEN")
PAT_TOKEN = os.environ.get("PAT_TOKEN")
MIN_SEVERITY= "MAJOR"
GITHUB_REPO_OWNER = "fuzailAhmad123"
GITHUB_REPO_NAME = "automated-issue-creation-via-sonarqube"