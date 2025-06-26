import os
import requests
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

def fetch_pr_diff(pr_url):
    """
    Fetch diff content from GitHub PR URL
    Example: https://github.com/owner/repo/pull/123
    """
    # Parse URL to extract owner, repo, and PR number
    parts = pr_url.rstrip('/').split('/')
    if len(parts) < 7:
        raise ValueError("Invalid PR URL format")
    
    owner = parts[3]
    repo = parts[4]
    pr_number = parts[6]
    
    # GitHub API headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Fetch diff from GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
    
    return response.text

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_diff.py <PR_URL>")
        sys.exit(1)
    
    pr_url = sys.argv[1]
    try:
        diff = fetch_pr_diff(pr_url)
        print(diff)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)