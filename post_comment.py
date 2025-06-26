"""
GitHub Comment Integration
Posts AI code review results as PR comments
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def post_comment(pr_url: str, body: str) -> bool:
    """
    Post a comment to a GitHub PR
    
    Args:
        pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
        body: Comment body in markdown format
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse PR URL to get API endpoint
        parts = pr_url.rstrip('/').split('/')
        if len(parts) < 7:
            raise ValueError("Invalid PR URL format")
        
        owner = parts[3]
        repo = parts[4] 
        pr_number = parts[6]
        
        # GitHub API endpoint for PR comments
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        # Headers for GitHub API
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Comment payload
        payload = {"body": body}
        
        # Post comment
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Comment posted successfully to {pr_url}")
            return True
        else:
            print(f"❌ Failed to post comment: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting comment: {str(e)}")
        return False

def format_review_comment(review_result: dict, pr_url: str) -> str:
    """
    Format review results into a professional GitHub comment
    
    Args:
        review_result: Analysis results from architect
        pr_url: PR URL for reference
        
    Returns:
        str: Formatted markdown comment
    """
    # Header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "## 🤖 Secure-PR-Guard AI Code Review",
        "",
        f"**Analysis completed at:** {timestamp}",
        f"**PR:** {pr_url}",
        ""
    ]
    
    # Summary
    summary = review_result.get("summary", {})
    risk_level = summary.get("risk_level", "unknown")
    total_issues = summary.get("total_issues", 0)
    security_issues = summary.get("security_issues", 0)
    
    # Risk level emoji
    risk_emoji = {
        "low": "🟢",
        "medium": "🟡", 
        "high": "🔴",
        "critical": "🚨"
    }.get(risk_level, "⚪")
    
    lines.extend([
        f"### {risk_emoji} Risk Assessment: **{risk_level.upper()}**",
        "",
        f"- **Total Issues Found:** {total_issues}",
        f"- **Security Issues:** {security_issues}",
        ""
    ])
    
    # Issues breakdown
    issues = review_result.get("issues", [])
    
    if not issues:
        lines.extend([
            "### ✅ Great job! No issues found",
            "",
            "Your code looks clean and secure. Keep up the good work! 🎉"
        ])
    else:
        # Group issues by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        medium_issues = [i for i in issues if i.get("severity") == "medium"]
        low_issues = [i for i in issues if i.get("severity") == "low"]
        
        # Critical issues first
        if critical_issues:
            lines.extend([
                "### 🚨 Critical Issues (Immediate Action Required)",
                ""
            ])
            for issue in critical_issues:
                lines.append(f"- **Line {issue['line']}** ({issue['type']}): {issue['comment']}")
            lines.append("")
        
        # High priority issues
        if high_issues:
            lines.extend([
                "### 🔴 High Priority Issues",
                ""
            ])
            for issue in high_issues:
                lines.append(f"- **Line {issue['line']}** ({issue['type']}): {issue['comment']}")
            lines.append("")
        
        # Medium priority issues
        if medium_issues:
            lines.extend([
                "### 🟡 Medium Priority Issues", 
                ""
            ])
            for issue in medium_issues:
                lines.append(f"- **Line {issue['line']}** ({issue['type']}): {issue['comment']}")
            lines.append("")
        
        # Low priority issues
        if low_issues:
            lines.extend([
                "### 🟢 Low Priority Issues",
                ""
            ])
            for issue in low_issues:
                lines.append(f"- **Line {issue['line']}** ({issue['type']}): {issue['comment']}")
            lines.append("")
    
    # Analysis metadata
    analysis_summary = review_result.get("analysis_summary", {})
    if analysis_summary:
        lines.extend([
            "---",
            "### 📊 Analysis Details",
            "",
            f"- **AI Detection:** {analysis_summary.get('ai_detected', 0)} issues",
            f"- **Security Rules:** {analysis_summary.get('rule_detected', 0)} issues", 
            f"- **Total Unique:** {analysis_summary.get('total_unique', 0)} issues",
            ""
        ])
    
    # Footer
    lines.extend([
        "---",
        "🔗 **Powered by Secure-PR-Guard** | 🛡️ **OWASP LLM Top 10 Compliant**",
        "",
        "*This is an automated review. Please verify critical security findings manually.*"
    ])
    
    return "\n".join(lines)

def test_comment_formatting():
    """Test function for comment formatting"""
    test_result = {
        "issues": [
            {
                "line": 1,
                "type": "security",
                "severity": "critical",
                "comment": "🔒 [SECURITY] Hardcoded password detected"
            },
            {
                "line": 2,
                "type": "style", 
                "severity": "low",
                "comment": "Line exceeds 120 characters"
            }
        ],
        "summary": {
            "total_issues": 2,
            "security_issues": 1,
            "risk_level": "high"
        },
        "analysis_summary": {
            "ai_detected": 1,
            "rule_detected": 1,
            "total_unique": 2
        }
    }
    
    comment = format_review_comment(test_result, "https://github.com/test/repo/pull/1")
    print("Formatted comment:")
    print(comment)

if __name__ == "__main__":
    test_comment_formatting()