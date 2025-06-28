import requests
import json
import os
import sys
import re

# 修复路径问题 - 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# 使用 GitHub App 认证（最小化改动）
try:
    from github_auth_adapter import get_github_token
    token = get_github_token()
    print("✅ Using GitHub App authentication")
except Exception as e:
    # 如果失败，回退到原来的方式
    print(f"⚠️  GitHub App auth failed ({e}), using PAT fallback")
    token = os.getenv("GITHUB_TOKEN")

def fetch_pr_diff(pr_url):
    """
    Fetch the diff of a pull request from GitHub.
    
    Args:
        pr_url (str): The URL of the pull request
        
    Returns:
        str: The diff content of the pull request
    """
    # Extract owner, repo, and PR number from the URL
    # Expected format: https://github.com/owner/repo/pull/123
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL format: {pr_url}")
    
    owner, repo, pr_number = match.groups()
    
    # GitHub API endpoint for PR diff
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    # GitHub API headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Make the API request
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch PR diff: {response.status_code} - {response.text}")


def save_diff_to_file(diff_content, filename="pr_diff.patch"):
    """Save diff content to a file."""
    with open(filename, 'w') as f:
        f.write(diff_content)
    print(f"Diff saved to {filename}")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        pr_url = sys.argv[1]
    else:
        pr_url = input("Enter PR URL: ")
    
    try:
        diff = fetch_pr_diff(pr_url)
        print(f"Successfully fetched diff for {pr_url}")
        print(f"Diff size: {len(diff)} characters")
        
        # Optionally save to file
        save_to_file = input("Save to file? (y/n): ").lower() == 'y'
        if save_to_file:
            save_diff_to_file(diff)
    except Exception as e:
        print(f"Error: {e}")
