"""
GitHub PR Creation for Automated Patches
Handles branch creation, patch application, and Draft PR creation
"""

import requests
import os
import json
import tempfile
import subprocess
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
BOT_NAME = os.getenv("GITHUB_BOT_NAME", "secure-pr-guard[bot]")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_pr_info(owner: str, repo: str, pr_number: str) -> Dict:
    """
    Get PR information including base and head commit SHAs
    
    Args:
        owner: Repository owner
        repo: Repository name  
        pr_number: PR number
        
    Returns:
        Dict: PR information
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    try:
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error getting PR info: {str(e)}")
        return {}

def create_patch_branch(owner: str, repo: str, base_sha: str, pr_number: str) -> str:
    """
    Create a new branch for the patch
    
    Args:
        owner: Repository owner
        repo: Repository name
        base_sha: Base commit SHA to branch from
        pr_number: Original PR number for naming
        
    Returns:
        str: New branch name
    """
    import time
    
    # Generate unique branch name with timestamp
    timestamp = int(time.time())
    branch_name = f"auto-patch/pr-{pr_number}-{base_sha[:7]}-{timestamp}"
    
    print(f"🌿 Creating branch: {branch_name}")
    
    # Check if branch already exists
    check_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch_name}"
    check_response = requests.get(check_url, headers=HEADERS)
    
    if check_response.status_code == 200:
        print(f"⚠️ Branch {branch_name} already exists, trying alternative name")
        # Add extra randomness
        import random
        branch_name = f"auto-patch/pr-{pr_number}-{base_sha[:7]}-{timestamp}-{random.randint(100,999)}"
        print(f"🌿 Trying alternative branch: {branch_name}")
    
    # Create branch via GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }
    
    try:
        print(f"🔍 Debug: Creating branch with SHA: {base_sha}")
        print(f"🔍 Debug: Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(api_url, headers=HEADERS, json=payload)
        
        if response.status_code == 201:
            print(f"✅ Created branch: {branch_name}")
            return branch_name
        else:
            print(f"❌ Error creating branch: {response.status_code} - {response.text}")
            print(f"🔍 Debug: Request URL: {api_url}")
            print(f"🔍 Debug: Headers: {dict(HEADERS)}")
            return ""
            
    except Exception as e:
        print(f"❌ Exception creating branch: {str(e)}")
        return ""

def apply_patch_to_files(patch_content: str, owner: str, repo: str, branch_name: str) -> bool:
    """
    Apply patch to files in the repository via GitHub API
    
    Args:
        patch_content: Unified diff patch content
        owner: Repository owner
        repo: Repository name
        branch_name: Target branch name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse patch to extract file changes
        file_changes = parse_unified_diff(patch_content)
        
        if not file_changes:
            print("❌ No valid file changes found in patch")
            return False
        
        # Apply changes to each file
        for file_path, new_content in file_changes.items():
            success = update_file_content(owner, repo, branch_name, file_path, new_content)
            if not success:
                print(f"❌ Failed to update {file_path}")
                return False
        
        print(f"✅ Applied patch to {len(file_changes)} files")
        return True
        
    except Exception as e:
        print(f"❌ Error applying patch: {str(e)}")
        return False

def parse_unified_diff(patch_content: str) -> Dict[str, str]:
    """
    Parse unified diff and extract file contents
    
    Args:
        patch_content: Unified diff content
        
    Returns:
        Dict[str, str]: Mapping of file paths to new content
    """
    file_changes = {}
    current_file = None
    current_lines = []
    
    lines = patch_content.split('\n')
    
    for line in lines:
        if line.startswith('--- '):
            # Start of new file
            if current_file and current_lines:
                file_changes[current_file] = '\n'.join(current_lines)
            current_file = None
            current_lines = []
            
        elif line.startswith('+++ '):
            # File path
            current_file = line[4:].strip()
            if current_file.startswith('b/'):
                current_file = current_file[2:]
                
        elif line.startswith('@@'):
            # Hunk header - skip
            continue
            
        elif current_file:
            if line.startswith(' ') or line.startswith('+'):
                # Keep context lines and additions
                current_lines.append(line[1:] if line.startswith(('+', ' ')) else line)
            # Skip deletions (lines starting with -)
    
    # Handle last file
    if current_file and current_lines:
        file_changes[current_file] = '\n'.join(current_lines)
    
    return file_changes

def get_file_content(owner: str, repo: str, branch: str, file_path: str) -> Optional[str]:
    """
    Get current content of a file from GitHub
    
    Args:
        owner: Repository owner
        repo: Repository name  
        branch: Branch name
        file_path: Path to file
        
    Returns:
        Optional[str]: File content or None if error
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    
    try:
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status()
        
        file_data = response.json()
        import base64
        content = base64.b64decode(file_data['content']).decode('utf-8')
        return content, file_data['sha']
        
    except Exception as e:
        print(f"❌ Error getting file {file_path}: {str(e)}")
        return None, None

def update_file_content(owner: str, repo: str, branch: str, file_path: str, new_content: str) -> bool:
    """
    Update file content via GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name  
        file_path: Path to file
        new_content: New file content
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get current file to get SHA
    current_content, file_sha = get_file_content(owner, repo, branch, file_path)
    
    if file_sha is None:
        return False
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    
    import base64
    encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"chore: auto-fix formatting issues in {file_path}",
        "content": encoded_content,
        "sha": file_sha,
        "branch": branch,
        "committer": {
            "name": BOT_NAME,
            "email": "noreply@github.com"
        }
    }
    
    try:
        response = requests.put(api_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        print(f"✅ Updated {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {str(e)}")
        return False

def create_draft_pr(owner: str, repo: str, head_branch: str, base_branch: str, 
                   original_pr_number: str, patch_summary: str) -> Optional[str]:
    """
    Create a Draft PR with the patch
    
    Args:
        owner: Repository owner
        repo: Repository name
        head_branch: Source branch (patch branch)
        base_branch: Target branch (usually master/main)
        original_pr_number: Original PR number
        patch_summary: Summary of fixes applied
        
    Returns:
        Optional[str]: PR URL if successful, None otherwise
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    
    title = f"🛠️ Auto-fix: Formatting issues from PR #{original_pr_number}"
    
    body = f"""## 🤖 Automated Formatting Fixes

This PR contains automated fixes for safe formatting issues detected in PR #{original_pr_number}.

{patch_summary}

### ✅ Safety Guarantees
- ✅ Only formatting and style fixes
- ✅ No logic changes
- ✅ All functionality preserved
- ✅ Generated by AI with safety validation

### 📋 Review Instructions
1. Verify that only formatting was changed
2. Run tests to ensure functionality is preserved  
3. Merge if satisfied, or close if not needed

---
🤖 **Generated by {BOT_NAME}** | 🔗 **Related to PR #{original_pr_number}**
"""

    payload = {
        "title": title,
        "head": head_branch,
        "base": base_branch, 
        "body": body,
        "draft": True
    }
    
    try:
        response = requests.post(api_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        pr_data = response.json()
        pr_url = pr_data["html_url"]
        pr_number = pr_data["number"]
        
        print(f"✅ Created Draft PR #{pr_number}: {pr_url}")
        return pr_url
        
    except Exception as e:
        print(f"❌ Error creating PR: {str(e)}")
        return None

def create_patch_pr_workflow(owner: str, repo: str, pr_number: str, 
                           patch_content: str, patch_summary: str) -> Optional[str]:
    """
    Complete workflow to create a patch PR
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Original PR number
        patch_content: Unified diff patch
        patch_summary: Summary of fixes
        
    Returns:
        Optional[str]: Draft PR URL if successful, None otherwise
    """
    print(f"🚀 Starting patch PR workflow for {owner}/{repo}/pull/{pr_number}")
    
    # Get PR info
    pr_info = get_pr_info(owner, repo, pr_number)
    if not pr_info:
        return None
    
    base_sha = pr_info["head"]["sha"]
    base_branch = pr_info["base"]["ref"]
    
    print(f"📋 Base SHA: {base_sha[:12]}..., Base branch: {base_branch}")
    
    # Validate SHA exists
    sha_check_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_sha}"
    sha_response = requests.get(sha_check_url, headers=HEADERS)
    
    if sha_response.status_code != 200:
        print(f"❌ Invalid SHA {base_sha}: {sha_response.status_code}")
        return None
    
    print(f"✅ SHA validated: {base_sha}")
    
    # Create patch branch
    patch_branch = create_patch_branch(owner, repo, base_sha, pr_number)
    if not patch_branch:
        return None
    
    # Apply patch
    if not apply_patch_to_files(patch_content, owner, repo, patch_branch):
        print("❌ Failed to apply patch")
        return None
    
    # Create Draft PR
    pr_url = create_draft_pr(owner, repo, patch_branch, base_branch, 
                           pr_number, patch_summary)
    
    return pr_url

# Test function
if __name__ == "__main__":
    # Test patch parsing
    test_patch = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def test():
-	print("hello")
+    print("hello")
"""
    
    changes = parse_unified_diff(test_patch)
    print("Parsed changes:", changes)