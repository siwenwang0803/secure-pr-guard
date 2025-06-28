"""
GitHub App Authentication Module
Implements JWT-based authentication for GitHub Apps
"""

import time
import jwt
import requests
from typing import Optional, Dict
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class GitHubAppAuth:
    """Handles GitHub App authentication using JWT and Installation tokens"""
    
    def __init__(self, app_id: str, private_key_path: str, installation_id: str):
        """
        Initialize GitHub App authenticator
        
        Args:
            app_id: GitHub App ID
            private_key_path: Path to the private key .pem file
            installation_id: Installation ID for the repository
        """
        self.app_id = app_id
        self.installation_id = installation_id
        self.private_key = self._load_private_key(private_key_path)
        self._token_cache = {
            "token": None,
            "expires_at": 0
        }
        
    def _load_private_key(self, key_path: str) -> str:
        """Load private key from file"""
        try:
            with open(key_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Private key file not found: {key_path}")
            
    def generate_jwt(self) -> str:
        """
        Generate a JSON Web Token for GitHub App authentication
        
        Returns:
            JWT token string (valid for 10 minutes)
        """
        # JWT expires in 10 minutes (GitHub's maximum)
        now = int(time.time())
        payload = {
            "iat": now,  # Issued at
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.app_id  # Issuer (App ID)
        }
        
        # Create JWT using RS256 algorithm
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256"
        )
        
        logger.debug(f"Generated JWT for App ID: {self.app_id}")
        return token
        
    def get_installation_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh installation access token
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            
        Returns:
            Installation access token (valid for 1 hour)
        """
        # Check if we have a valid cached token
        if not force_refresh and self._token_cache["token"]:
            # Add 5 minute buffer for expiration
            if time.time() < self._token_cache["expires_at"] - 300:
                logger.debug("Using cached installation token")
                return self._token_cache["token"]
        
        # Generate new JWT
        jwt_token = self.generate_jwt()
        
        # Request installation token
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Cache the token
            self._token_cache["token"] = data["token"]
            # Parse expiration time
            expires_at = time.mktime(time.strptime(
                data["expires_at"], 
                "%Y-%m-%dT%H:%M:%SZ"
            ))
            self._token_cache["expires_at"] = expires_at
            
            logger.info(f"Generated new installation token, expires at: {data['expires_at']}")
            return data["token"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get installation token: {e}")
            raise
            
    def get_headers(self) -> Dict[str, str]:
        """
        Get headers for GitHub API requests
        
        Returns:
            Dictionary with Authorization header
        """
        token = self.get_installation_token()
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
    def test_authentication(self) -> bool:
        """
        Test if authentication is working
        
        Returns:
            True if authentication successful
        """
        try:
            headers = self.get_headers()
            response = requests.get(
                "https://api.github.com/installation/repositories",
                headers=headers
            )
            response.raise_for_status()
            
            repos = response.json()
            logger.info(f"Authentication successful! Access to {repos['total_count']} repositories")
            
            # Print accessible repositories
            for repo in repos.get("repositories", [])[:5]:  # Show first 5
                logger.info(f"  - {repo['full_name']}")
                
            return True
            
        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False


# Convenience function for backward compatibility
def get_github_headers(
    app_id: Optional[str] = None,
    private_key_path: Optional[str] = None,
    installation_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Get GitHub API headers using App authentication
    
    This function maintains compatibility with existing code
    that expects a simple header dictionary.
    """
    load_dotenv()
    
    # Use provided values or fall back to environment variables
    app_id = app_id or os.getenv("GITHUB_APP_ID")
    private_key_path = private_key_path or os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    installation_id = installation_id or os.getenv("GITHUB_APP_INSTALLATION_ID")
    
    if not all([app_id, private_key_path, installation_id]):
        raise ValueError(
            "Missing required GitHub App configuration. "
            "Please set GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY_PATH, "
            "and GITHUB_APP_INSTALLATION_ID"
        )
    
    auth = GitHubAppAuth(app_id, private_key_path, installation_id)
    return auth.get_headers()


# Test script
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test authentication
    print("Testing GitHub App authentication...")
    
    try:
        auth = GitHubAppAuth(
            app_id=os.getenv("GITHUB_APP_ID"),
            private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
            installation_id=os.getenv("GITHUB_APP_INSTALLATION_ID")
        )
        
        if auth.test_authentication():
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
