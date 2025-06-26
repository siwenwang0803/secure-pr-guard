"""
OWASP LLM Top 10 Security Checks
Implements detection patterns for AI-specific security vulnerabilities
"""

import re
from typing import List, Dict

def run_llm_security_rules(diff: str) -> List[Dict]:
    """
    Run OWASP LLM security checks on git diff
    
    Args:
        diff: Git diff content to analyze
        
    Returns:
        List of security issues found
    """
    issues = []
    lines = diff.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Only check added lines (lines starting with +)
        if not line.startswith('+'):
            continue
            
        clean_line = line[1:].strip()  # Remove + prefix and whitespace
        
        # Skip empty lines and comments
        if not clean_line or clean_line.startswith('#') or clean_line.startswith('//'):
            continue
            
        # LLM01: Prompt Injection Detection
        llm01_issues = check_llm01_prompt_injection(clean_line, line_num)
        issues.extend(llm01_issues)
        
        # LLM02: Insecure Output Handling Detection  
        llm02_issues = check_llm02_insecure_output(clean_line, line_num)
        issues.extend(llm02_issues)
        
        # Additional security patterns
        general_issues = check_general_security_patterns(clean_line, line_num)
        issues.extend(general_issues)
    
    return issues

def check_llm01_prompt_injection(line: str, line_num: int) -> List[Dict]:
    """
    LLM01: Detect potential prompt injection vulnerabilities
    """
    issues = []
    
    # Pattern 1: Template injection markers
    template_patterns = [
        r'\{\{.*\}\}',      # Jinja2-style: {{user_input}}
        r'\$\{.*\}',        # Shell-style: ${user_input}
        r'<.*>',            # XML-style: <user_input>
        r'\[\[.*\]\]',      # Wiki-style: [[user_input]]
    ]
    
    for pattern in template_patterns:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": f"LLM01: Potential prompt injection vector detected - template pattern '{pattern}' may allow user input manipulation"
            })
    
    # Pattern 2: Direct string concatenation with user input
    concat_patterns = [
        r'["\'].*\+.*user.*["\']',
        r'["\'].*\+.*input.*["\']',
        r'["\'].*\+.*request.*["\']',
        r'f["\'].*\{.*user.*\}.*["\']',  # f-string with user input
    ]
    
    for pattern in concat_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security", 
                "severity": "high",
                "comment": "LLM01: Direct user input concatenation in prompt - vulnerable to injection attacks"
            })
    
    # Pattern 3: System prompt modification
    system_prompt_patterns = [
        r'system.*=.*\+',
        r'role.*["\']system["\'].*\+',
        r'prompt.*=.*user',
    ]
    
    for pattern in system_prompt_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical", 
                "comment": "LLM01: System prompt modification with user input - critical injection risk"
            })
    
    return issues

def check_llm02_insecure_output(line: str, line_num: int) -> List[Dict]:
    """
    LLM02: Detect insecure handling of LLM outputs
    """
    issues = []
    
    # Pattern 1: Direct execution of LLM output
    exec_patterns = [
        r'exec\s*\(\s*.*response.*\)',
        r'eval\s*\(\s*.*response.*\)',
        r'exec\s*\(\s*.*output.*\)',
        r'eval\s*\(\s*.*output.*\)',
        r'subprocess.*\(.*response.*\)',
        r'os\.system\s*\(\s*.*response.*\)',
    ]
    
    for pattern in exec_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM02: Direct execution of LLM output - extreme code injection risk"
            })
    
    # Pattern 2: Unsafe deserialization of LLM output
    deserial_patterns = [
        r'pickle\.loads\s*\(\s*.*response.*\)',
        r'json\.loads\s*\(\s*.*response.*\)',
        r'yaml\.load\s*\(\s*.*response.*\)',
        r'marshal\.loads\s*\(\s*.*response.*\)',
    ]
    
    for pattern in deserial_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM02: Unsafe deserialization of LLM output - potential remote code execution"
            })
    
    # Pattern 3: SQL query construction with LLM output
    sql_patterns = [
        r'execute\s*\(\s*.*response.*\)',
        r'query\s*=.*response',
        r'SELECT.*\+.*response',
        r'INSERT.*\+.*response',
        r'UPDATE.*\+.*response',
        r'DELETE.*\+.*response',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM02: SQL query construction with LLM output - SQL injection risk"
            })
    
    # Pattern 4: File operations with LLM output
    file_patterns = [
        r'open\s*\(\s*.*response.*\)',
        r'write\s*\(\s*.*response.*\)',
        r'os\.path\.join\s*\(\s*.*response.*\)',
        r'pathlib.*\(.*response.*\)',
    ]
    
    for pattern in file_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "medium",
                "comment": "LLM02: File operations with LLM output - path traversal risk"
            })
    
    return issues

def check_general_security_patterns(line: str, line_num: int) -> List[Dict]:
    """
    Additional security patterns beyond OWASP LLM Top 10
    """
    issues = []
    
    # Hardcoded secrets
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token detected"),
        (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API key detected"),
    ]
    
    for pattern, message in secret_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": f"Security: {message} - use environment variables instead"
            })
    
    # Unsafe imports
    unsafe_imports = [
        (r'import\s+pickle', "Pickle module can execute arbitrary code"),
        (r'from\s+pickle\s+import', "Pickle module can execute arbitrary code"),
        (r'import\s+marshal', "Marshal module can execute arbitrary code"),
        (r'__import__\s*\(', "Dynamic imports can be dangerous"),
    ]
    
    for pattern, message in unsafe_imports:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "medium",
                "comment": f"Security: {message}"
            })
    
    return issues

# Test function
if __name__ == "__main__":
    test_diff = """
+ password = "hardcoded123"
+ user_prompt = f"You are helpful. {user_input}"
+ exec(ai_response)
+ query = "SELECT * FROM users WHERE name = " + ai_output
+ import pickle
"""
    
    issues = run_llm_security_rules(test_diff)
    print(f"Found {len(issues)} security issues:")
    for issue in issues:
        print(f"  Line {issue['line']}: {issue['comment']}")