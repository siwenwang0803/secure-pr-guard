"""
Architect Agent: Security-focused code analysis
Specializes in architectural security concerns and risk prioritization
"""

def architect(review_result: dict) -> dict:
    """
    Process nitpicker results and elevate security concerns
    
    Args:
        review_result: Output from nitpicker containing issues list
        
    Returns:
        Enhanced review with security issues prioritized
    """
    if not review_result or "issues" not in review_result:
        return review_result
    
    issues = review_result["issues"]
    enhanced_issues = []
    
    security_count = 0
    
    for issue in issues:
        enhanced_issue = issue.copy()
        
        # Elevate security issues with special marking
        if issue.get("type") == "security":
            enhanced_issue["comment"] = f"🔒 [SECURITY] {issue['comment']}"
            enhanced_issue["severity"] = "critical"  # Upgrade to critical
            security_count += 1
            
        # Add architectural context for other high-severity issues
        elif issue.get("severity") == "high":
            enhanced_issue["comment"] = f"⚠️ [HIGH PRIORITY] {issue['comment']}"
            
        enhanced_issues.append(enhanced_issue)
    
    # Add summary metadata
    result = {
        "issues": enhanced_issues,
        "summary": {
            "total_issues": len(enhanced_issues),
            "security_issues": security_count,
            "risk_level": "high" if security_count > 0 else "medium" if len(enhanced_issues) > 0 else "low"
        }
    }
    
    # Preserve any error information
    if "error" in review_result:
        result["error"] = review_result["error"]
    
    return result

def validate_architecture_patterns(diff: str) -> list:
    """
    Check for common architectural anti-patterns in code changes
    
    Args:
        diff: Git diff content
        
    Returns:
        List of architectural issues found
    """
    issues = []
    lines = diff.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Skip non-addition lines
        if not line.startswith('+'):
            continue
            
        clean_line = line[1:].strip()  # Remove + prefix
        
        # Check for hardcoded credentials patterns
        if any(pattern in clean_line.lower() for pattern in [
            'password =', 'api_key =', 'secret =', 'token =', 'api_secret'
        ]):
            issues.append({
                "line": i,
                "type": "security",
                "severity": "critical",
                "comment": "Potential hardcoded credentials detected"
            })
            
        # Check for unsafe eval/exec patterns
        if any(pattern in clean_line for pattern in ['eval(', 'exec(', '__import__']):
            issues.append({
                "line": i,
                "type": "security", 
                "severity": "critical",
                "comment": "Dangerous code execution detected - potential code injection risk"
            })
            
        # Check for SQL injection patterns
        if 'execute(' in clean_line and any(op in clean_line for op in ['+', '%', 'format']):
            issues.append({
                "line": i,
                "type": "security",
                "severity": "high", 
                "comment": "Potential SQL injection - use parameterized queries"
            })
    
    return issues

if __name__ == "__main__":
    # Test the architect function
    test_input = {
        "issues": [
            {
                "line": 1,
                "type": "security",
                "severity": "high",
                "comment": "Hardcoded password detected"
            },
            {
                "line": 2, 
                "type": "style",
                "severity": "low",
                "comment": "Line too long"
            }
        ]
    }
    
    result = architect(test_input)
    print("Architect processing result:")
    print(f"Risk level: {result['summary']['risk_level']}")
    print(f"Security issues: {result['summary']['security_issues']}")
    for issue in result["issues"]:
        print(f"  - {issue['comment']}")