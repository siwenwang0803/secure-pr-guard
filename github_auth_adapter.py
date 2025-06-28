"""
GitHub 认证适配器 - 最小化改动
只需要替换 token 获取方式，其他代码保持不变
"""
import os
from github_app import GitHubAppAuth
from dotenv import load_dotenv

load_dotenv()

def get_github_token():
    """
    获取 GitHub token
    这个函数替代原来的 os.getenv("GITHUB_TOKEN")
    """
    try:
        # 使用 GitHub App 认证
        auth = GitHubAppAuth(
            app_id=os.getenv("GITHUB_APP_ID"),
            private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
            installation_id=os.getenv("GITHUB_APP_INSTALLATION_ID")
        )
        return auth.get_installation_token()
    except:
        # 如果 GitHub App 认证失败，回退到 PAT（向后兼容）
        return os.getenv("GITHUB_TOKEN")

# 为了完全兼容，也提供 headers 函数
def get_headers():
    """获取完整的 headers"""
    token = get_github_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
