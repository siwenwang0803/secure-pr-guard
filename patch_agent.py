"""
Patch Agent: Automated code fixing for low-risk issues with cost tracking
Generates safe patches for formatting and style problems
"""

import os
import json
import time
import difflib
from openai import OpenAI
from typing import List, Dict, Tuple  # 确保Tuple在这里！
from dotenv import load_dotenv
from cost_logger import log_cost

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define what we consider "safe to fix"
LOW_RISK_TYPES = {"indentation", "length", "style"}

def build_patch(diff_text: str, issues: List[Dict], pr_url: str = "") -> Tuple[str, Dict]:
    """
    Generate patches for low-risk issues only with cost tracking
    
    Args:
        diff_text: Original git diff content
        issues: List of detected issues from analysis
        pr_url: GitHub PR URL for cost tracking
        
    Returns:
        Tuple[str, Dict]: (patch_content, cost_info)
    """
    # Start timing
    start_time = time.time()
    
    # Debug: Print all issue types
    print(f"🔍 Debug: All detected issues:")
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        print(f"   - Type: '{issue_type}', Line: {issue.get('line')}")
    
    # Filter for low-risk issues only
    safe_issues = [issue for issue in issues if issue.get("type") in LOW_RISK_TYPES]
    
    print(f"🔍 Debug: LOW_RISK_TYPES = {LOW_RISK_TYPES}")
    print(f"🔍 Debug: Filtered safe issues: {len(safe_issues)} out of {len(issues)}")
    
    if not safe_issues:
        print("🔒 No safe issues to patch - all issues require manual review")
        cost_info = {
            "model": "gpt-4o-mini",
            "total_tokens": 0,
            "cost_usd": 0,
            "latency_ms": int((time.time() - start_time) * 1000),
            "skipped": True
        }
        return "", cost_info
    
    print(f"🛠️ Found {len(safe_issues)} safe issues to patch:")
    for issue in safe_issues:
        print(f"   - Line {issue.get('line')}: {issue.get('type')} - {issue.get('comment')[:50]}...")
    
    # Create patch generation prompt
    prompt = f"""You are an automated code formatter. Generate a unified diff patch to fix formatting issues.

CRITICAL: You must output ONLY a valid unified diff format starting with --- and +++.

FORMATTING RULES TO FIX:
1. Replace tabs with 4 spaces for indentation
2. Break long lines (keep function names, just improve formatting)
3. Do NOT change any function names, variable names, or logic

EXAMPLE UNIFIED DIFF FORMAT:
--- a/filename.py
+++ b/filename.py
@@ -1,4 +1,4 @@
 def example():
-	print("tab")
+    print("tab")
 
INPUT DIFF TO FIX:
```diff
{diff_text}
```

ISSUES TO ADDRESS:
{json.dumps(safe_issues, indent=2)}

OUTPUT: Generate unified diff patch with --- and +++ headers:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a code formatter. Output only valid unified diff format with --- and +++ headers. Fix only indentation (tabs to spaces) and basic formatting."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent formatting
            max_tokens=1500
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log cost information
        usage = response.usage
        cost = log_cost(
            pr_url=pr_url,
            operation="patch_generation",
            model="gpt-4o-mini",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=latency_ms
        )
        
        patch_content = response.choices[0].message.content.strip()
        
        # Clean up markdown formatting if present
        if patch_content.startswith('```'):
            lines = patch_content.split('\n')
            # Remove first line if it's markdown (```diff or ```)
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Remove last line if it's markdown closing (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            patch_content = '\n'.join(lines).strip()
        
        # Debug: Print generated patch
        print("🔍 Debug: Generated patch content:")
        print("=" * 50)
        print(patch_content[:300] + "..." if len(patch_content) > 300 else patch_content)
        print("=" * 50)
        
        # Validate patch format
        if not patch_content.startswith('---') or '+++' not in patch_content:
            print("⚠️ Generated patch doesn't appear to be valid unified diff")
            print(f"🔍 Debug: Patch starts with: '{patch_content[:20]}'")
            
            cost_info = {
                "model": "gpt-4o-mini",
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": cost,
                "latency_ms": latency_ms,
                "error": "Invalid patch format"
            }
            return "", cost_info
        
        print("✅ Patch generated successfully")
        
        cost_info = {
            "model": "gpt-4o-mini",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms
        }
        
        return patch_content, cost_info
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        print(f"❌ Error generating patch: {str(e)}")
        
        cost_info = {
            "model": "gpt-4o-mini",
            "total_tokens": 0,
            "cost_usd": 0,
            "latency_ms": latency_ms,
            "error": str(e)
        }
        
        return "", cost_info

def validate_patch_safety(patch_content: str) -> bool:
    """
    Validate that the patch only contains safe formatting changes
    
    Args:
        patch_content: Unified diff patch content
        
    Returns:
        bool: True if patch appears safe, False otherwise
    """
    if not patch_content:
        return False
    
    lines = patch_content.split('\n')
    
    # Check for dangerous patterns
    dangerous_patterns = [
        'def ',      # Function definition changes
        'class ',    # Class definition changes
        'import ',   # Import changes
        'from ',     # Import changes
        'return ',   # Return statement changes
        'if ',       # Conditional logic changes
        'for ',      # Loop changes
        'while ',    # Loop changes
        'try:',      # Error handling changes
        'except ',   # Error handling changes
    ]
    
    for line in lines:
        if line.startswith(('+', '-')) and not line.startswith(('+++', '---')):
            # This is a content change line
            clean_line = line[1:].strip()
            
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if pattern in clean_line:
                    print(f"⚠️ Potentially unsafe change detected: {clean_line[:50]}...")
                    return False
    
    return True

def format_patch_summary(issues: List[Dict]) -> str:
    """
    Create a summary of what the patch fixes
    
    Args:
        issues: List of issues being fixed
        
    Returns:
        str: Formatted summary for PR description
    """
    if not issues:
        return "No issues to fix"
    
    summary_lines = ["## 🛠️ Auto-fix Summary\n"]
    
    # Group by type
    by_type = {}
    for issue in issues:
        issue_type = issue.get('type', 'unknown')
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)
    
    for issue_type, type_issues in by_type.items():
        summary_lines.append(f"### {issue_type.title()} Issues ({len(type_issues)} fixes)")
        for issue in type_issues:
            line_num = issue.get('line', '?')
            comment = issue.get('comment', 'No description')[:60]
            summary_lines.append(f"- **Line {line_num}**: {comment}")
        summary_lines.append("")
    
    summary_lines.extend([
        "---",
        "🤖 **Generated by Secure-PR-Guard** | ⚡ **Safe Formatting Only**",
        "",
        "*This patch only contains formatting fixes and preserves all code functionality.*"
    ])
    
    return "\n".join(summary_lines)

# Backward compatibility wrapper
def build_patch_legacy(diff_text: str, issues: List[Dict]) -> str:
    """
    Legacy function signature for backward compatibility
    """
    patch_content, _ = build_patch(diff_text, issues, "")
    return patch_content

# Test function
if __name__ == "__main__":
    # Test with sample data
    test_diff = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def test():
-	print("hello")  # uses tab
+    print("hello")  # uses spaces
"""
    
    test_issues = [
        {
            "line": 2,
            "type": "indentation",
            "severity": "low",
            "comment": "Uses tab instead of spaces for indentation"
        }
    ]
    
    patch = build_patch(test_diff, test_issues)
    print("Generated patch:")
    print(patch)