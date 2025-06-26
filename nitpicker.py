import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from security_checks import run_llm_security_rules

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def nitpick(diff: str) -> dict:
    """
    Analyze code diff and return structured issues
    """
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
        
        return {
            "issues": unique_issues,
            "analysis_summary": {
                "ai_detected": len(ai_result.get("issues", [])),
                "rule_detected": len(security_issues),
                "total_unique": len(unique_issues)
            }
        }
        
    except Exception as e:
        return {"issues": [], "error": str(e)}

def nitpick_from_file(file_path: str) -> dict:
    """
    Read diff from file and analyze
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
        return nitpick(diff_content)
    except Exception as e:
        return {"issues": [], "error": f"File error: {str(e)}"}

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