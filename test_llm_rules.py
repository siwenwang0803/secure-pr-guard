#!/usr/bin/env python3
"""
Test script for LLM03 and LLM04 security rules
Run: python test_llm_rules.py
"""

from security_checks import run_llm_security_rules

def test_llm03_prompt_leakage():
    """Test LLM03: Prompt Leakage Detection"""
    print("🔍 Testing LLM03: Prompt Leakage Detection")
    
    test_cases = [
        # Should trigger LLM03 alerts
        '+ print(f"System prompt: {system_prompt}")',
        '+ log.debug(f"Internal instruction: {internal_instruction}")', 
        '+ console.log("You are a helpful assistant")',
        '+ response = system_prompt + ai_response',
        '+ debug_prompt = True',
        '+ user_input = "ignore previous instructions"',
        
        # Should NOT trigger (legitimate usage)
        '+ prompt = "What is the weather today?"',
        '+ print("Processing user request")',
        '+ log.info("Request completed successfully")',
    ]
    
    total_issues = 0
    for test_case in test_cases:
        issues = run_llm_security_rules(test_case)
        llm03_issues = [i for i in issues if "LLM03" in i['comment']]
        
        if llm03_issues:
            print(f"   ✅ DETECTED: {test_case.strip()}")
            for issue in llm03_issues:
                print(f"      └─ {issue['comment']}")
            total_issues += len(llm03_issues)
        else:
            print(f"   ⚪ CLEAN: {test_case.strip()}")
    
    print(f"   📊 LLM03 Total Issues Found: {total_issues}\n")
    return total_issues

def test_llm04_unsafe_calls():
    """Test LLM04: Unsafe Function Calls Detection"""
    print("🔍 Testing LLM04: Unsafe Function Calls Detection")
    
    test_cases = [
        # Should trigger LLM04 alerts
        '+ subprocess.run(user_command)',
        '+ os.system("rm -rf /")',
        '+ eval(dynamic_code)',
        '+ exec(ai_generated_code)',
        '+ while True:',
        '+ time.sleep(5000)',
        '+ pickle.loads(untrusted_data)',
        '+ open(user_filename)',
        '+ os.remove(user_path)',
        
        # Should NOT trigger (safe usage)
        '+ subprocess.run(["ls", "-la"], check=True)',  # This might still trigger, which is good
        '+ print("Hello world")',
        '+ time.sleep(1)',  # Short sleep is OK
        '+ with open("config.txt") as f:',  # Hardcoded filename
    ]
    
    total_issues = 0
    for test_case in test_cases:
        issues = run_llm_security_rules(test_case)
        llm04_issues = [i for i in issues if "LLM04" in i['comment']]
        
        if llm04_issues:
            print(f"   ✅ DETECTED: {test_case.strip()}")
            for issue in llm04_issues:
                print(f"      └─ {issue['comment']}")
            total_issues += len(llm04_issues)
        else:
            print(f"   ⚪ CLEAN: {test_case.strip()}")
    
    print(f"   📊 LLM04 Total Issues Found: {total_issues}\n")
    return total_issues

def test_combined_scenario():
    """Test a realistic code diff with multiple issues"""
    print("🔍 Testing Combined Scenario")
    
    realistic_diff = """
+ import os
+ import subprocess
+ import pickle
+ 
+ def process_user_request(user_input, system_prompt):
+     # LLM03: Prompt leakage
+     print(f"Debug: system prompt is {system_prompt}")
+     
+     # LLM01: Prompt injection
+     prompt = f"You are helpful. {user_input}"
+     
+     # LLM04: Unsafe function call
+     subprocess.run(user_input, shell=True)
+     
+     # LLM02: Unsafe output handling
+     exec(ai_response)
+     
+     # LLM04: Unsafe deserialization  
+     data = pickle.loads(user_data)
+     
+     # General: Hardcoded secret
+     api_key = "sk-1234567890abcdef1234567890abcdef"
+     
+     return "processed"
"""
    
    issues = run_llm_security_rules(realistic_diff)
    
    # Categorize issues by type
    categories = {}
    for issue in issues:
        if "LLM01" in issue['comment']:
            categories.setdefault("LLM01", []).append(issue)
        elif "LLM02" in issue['comment']:
            categories.setdefault("LLM02", []).append(issue)
        elif "LLM03" in issue['comment']:
            categories.setdefault("LLM03", []).append(issue)
        elif "LLM04" in issue['comment']:
            categories.setdefault("LLM04", []).append(issue)
        else:
            categories.setdefault("General", []).append(issue)
    
    print(f"   📊 Combined Scenario Results:")
    for category, issues_list in categories.items():
        print(f"      {category}: {len(issues_list)} issues")
        for issue in issues_list[:2]:  # Show first 2 issues per category
            print(f"         └─ Line {issue['line']}: {issue['comment'][:60]}...")
    
    print(f"   📊 Total Issues: {len(issues)}\n")
    return len(issues)

def main():
    """Run all tests"""
    print("🧪 Testing OWASP LLM Security Rules - LLM03 & LLM04")
    print("=" * 60)
    
    # Run tests
    llm03_count = test_llm03_prompt_leakage()
    llm04_count = test_llm04_unsafe_calls()
    combined_count = test_combined_scenario()
    
    # Summary
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ LLM03 (Prompt Leakage): {llm03_count} issues detected")
    print(f"✅ LLM04 (Unsafe Calls): {llm04_count} issues detected") 
    print(f"✅ Combined Scenario: {combined_count} total issues detected")
    
    if llm03_count > 0 and llm04_count > 0:
        print("\n🎯 SUCCESS: Both LLM03 and LLM04 rules are working!")
        print("💡 Next step: Update your security_checks.py with the new functions")
        return True
    else:
        print("\n❌ ISSUE: Some rules are not detecting properly")
        print("💡 Check the pattern matching logic in the rule functions")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)