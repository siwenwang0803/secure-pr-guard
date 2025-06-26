import requests, os, base64, json, re, subprocess, tempfile
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def create_branch_and_commit(owner, repo, base_sha, patch_text):
    branch = f"patch/{base_sha[:7]}"
    # 创建分支
    requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        headers=HEADERS,
        json={"ref": f"refs/heads/{branch}", "sha": base_sha}
    )
    # 上传 patch
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(patch_text.encode())
    tmp.close()
    subprocess.check_call(["git", "apply", tmp.name])
    subprocess.check_call(["git", "commit", "-am", "chore: auto-lint-fix"])
    subprocess.check_call(["git", "push", "origin", branch])
    return branch

def open_pr(owner, repo, branch, pr_number):
    title = f"[auto-fix] Lint patch for PR #{pr_number}"
    body = "🤖 **Secure-PR-Guard** 自动生成的小型格式修补，请审阅。"
    r = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=HEADERS,
        json={
            "title": title,
            "head": branch,
            "base": "master",
            "body": body,
            "draft": True
        }
    )
    return r.json()["html_url"]
