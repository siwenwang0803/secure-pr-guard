import os
import json
import time
from openai import OpenAI
from typing import Dict, Tuple  # 确保Tuple在这里！
from dotenv import load_dotenv
from security_checks import run_llm_security_rules
from cost_logger import log_cost
# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def nitpick(diff: str, pr_url: str = "") -> Tuple[Dict, Dict]:
    """
    Analyze code diff and return structured issues with cost tracking
    
    Args:
        diff: Git diff content to analyze
        pr_url: GitHub PR URL for cost tracking
        
    Returns:
        Tuple[Dict, Dict]: (analysis_result, cost_info)
    """
    # Start timing
    start_time = time.time()
    
    system_prompt = """You are a senior code reviewer specializing in security and code quality.
    
    Analyze the provided git diff and identify issues in these categories:
    1. Lines longer than 120 characters
    2. Use of tabs instead of spaces for indentation
    3. Basic security vulnerabilities
    4. Code style violations
    
    Focus only on the ADDED lines (lines starting with +) in the diff.
    
    Return a JSON object with an 'issues' array. Each issue should have:
    - line: line number where the issue occurs
    - type: category of issue (length, indentation, security, style)
    - severity: low, medium, high
    - comment: descriptive explanation of the issue
    """
    
    user_prompt = f"""Review this git diff and identify code quality issues:

```diff
{diff}
```

Please analyze only the added lines (+ prefix) and provide specific feedback."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            functions=[
                {
                    "name": "code_review",
                    "description": "Structure code review findings",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "line": {"type": "integer", "description": "Line number"},
                                        "type": {"type": "string", "description": "Issue category"},
                                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                        "comment": {"type": "string", "description": "Issue description"}
                                    },
                                    "required": ["line", "type", "severity", "comment"]
                                }
                            }
                        },
                        "required": ["issues"]
                    }
                }
            ],
            function_call={"name": "code_review"}
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log cost information
        usage = response.usage
        cost = log_cost(
            pr_url=pr_url,
            operation="nitpicker_analysis",
            model="gpt-4o-mini",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=latency_ms
        )
        
        # Parse the function call result
        function_call = response.choices[0].message.function_call
        ai_result = json.loads(function_call.arguments)
        
        # Add OWASP LLM security rule checks
        print("🔒 Running OWASP LLM security checks...")
        security_issues = run_llm_security_rules(diff)
        
        # Combine AI analysis with rule-based security checks
        all_issues = ai_result.get("issues", []) + security_issues
        
        # Remove duplicates (keep the more detailed one)
        unique_issues = []
        seen_lines = set()
        
        # Prioritize security issues from rules (more specific)
        for issue in security_issues:
            line_key = f"{issue['line']}_{issue['type']}"
            if line_key not in seen_lines:
                unique_issues.append(issue)
                seen_lines.add(line_key)
        
        # Add AI issues that don't duplicate rule findings
        for issue in ai_result.get("issues", []):
            line_key = f"{issue['line']}_{issue['type']}"
            if line_key not in seen_lines:
                unique_issues.append(issue)
                seen_lines.add(line_key)
        
        analysis_result = {
            "issues": unique_issues,
            "analysis_summary": {
                "ai_detected": len(ai_result.get("issues", [])),
                "rule_detected": len(security_issues),
                "total_unique": len(unique_issues)
            }
        }
        
        cost_info = {
            "model": "gpt-4o-mini",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms
        }
        
        return analysis_result, cost_info
        
    except Exception as e:
        # Log error but still track partial cost
        latency_ms = int((time.time() - start_time) * 1000)
        
        error_result = {"issues": [], "error": str(e)}
        cost_info = {
            "model": "gpt-4o-mini",
            "total_tokens": 0,
            "cost_usd": 0,
            "latency_ms": latency_ms,
            "error": str(e)
        }
        
        return error_result, cost_info

def nitpick_from_file(file_path: str, pr_url: str = "") -> Tuple[Dict, Dict]:
    """
    Read diff from file and analyze with cost tracking
    
    Args:
        file_path: Path to diff file
        pr_url: GitHub PR URL for cost tracking
        
    Returns:
        Tuple[Dict, Dict]: (analysis_result, cost_info)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
        return nitpick(diff_content, pr_url)
    except Exception as e:
        error_result = {"issues": [], "error": f"File error: {str(e)}"}
        cost_info = {"total_tokens": 0, "cost_usd": 0, "latency_ms": 0, "error": str(e)}
        return error_result, cost_info

# Backward compatibility wrapper
def nitpick_legacy(diff: str) -> Dict:
    """
    Legacy function signature for backward compatibility
    """
    result, _ = nitpick(diff, "")
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python nitpicker.py <diff_file_or_content>")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Check if it's a file path or direct content
    if os.path.isfile(input_arg):
        result = nitpick_from_file(input_arg)
    else:
        result = nitpick(input_arg)
    
    print(json.dumps(result, indent=2))