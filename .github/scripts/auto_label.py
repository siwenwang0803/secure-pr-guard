import os
import time
import json
import requests
import jwt
from datetime import datetime, timedelta

def create_jwt():
    """创建 GitHub App JWT"""
    app_id = os.environ['APP_ID']
    private_key = os.environ['PRIVATE_KEY_PEM']
    
    now = datetime.utcnow()
    payload = {
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=10)).timestamp()),
        'iss': int(app_id)
    }
    
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def get_installation_token():
    """获取 Installation Access Token"""
    jwt_token = create_jwt()
    installation_id = os.environ['INSTALLATION_ID']
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    response = requests.post(url, headers=headers)
    
    if response.status_code == 201:
        return response.json()['token']
    else:
        print(f"❌ Failed to get installation token: {response.status_code}")
        return None

def main():
    """主函数 - 自动标签和评论"""
    pr_number = os.environ.get('GITHUB_REF', '').split('/')[-1]
    repo = os.environ.get('GITHUB_REPOSITORY')
    
    print(f"🔍 Processing repository: {repo}")
    
    # 获取 Installation Token
    token = get_installation_token()
    if not token:
        return
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # 如果是 PR 触发，添加标签
    if pr_number and pr_number.isdigit():
        # 添加标签
        labels = ['bot/github-app-tested', 'security/analyzed', 'automated']
        url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/labels'
        
        response = requests.post(url, headers=headers, json={'labels': labels})
        
        if response.status_code == 200:
            print(f'✅ Successfully labeled PR #{pr_number} with: {labels}')
        else:
            print(f'❌ Failed to label PR: {response.status_code}')
    
    print('✅ GitHub App authentication successful!')
    print('✅ Auto-label workflow completed!')

if __name__ == '__main__':
    main()
