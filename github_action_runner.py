#!/usr/bin/env python3
"""
GitHub Action Runner for Secure PR Guard
Simplified version of the main analysis pipeline for GitHub Actions
"""

import argparse
import json
import os
import sys
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

# Mock classes for GitHub Action (simplified versions)
class GitHubActionResult:
    def __init__(self):
        self.analysis_cost = 0.0
        self.security_issues_found = 0
        self.owasp_compliance_score = 100
        self.analysis_summary = ""
        self.issues = []

class SimpleBudgetGuard:
    def __init__(self, cost_limit: float):
        self.cost_limit = cost_limit
        self.current_cost = 0.0
    
    def check_budget(self, estimated_cost: float):
        if self.current_cost + estimated_cost > self.cost_limit:
            raise Exception(f"Budget exceeded: {self.current_cost + estimated_cost:.3f} > {self.cost_limit:.3f}")
    
    def record_cost(self, actual_cost: float):
        self.current_cost += actual_cost

class SimpleOWASPScanner:
    def __init__(self):
        self.risk_patterns = {
            'LLM01_PROMPT_INJECTION': [
                r'ignore previous instructions',
                r'you are now',
                r'system prompt',
                r'roleplay as'
            ],
            'LLM06_SENSITIVE_INFO': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
                r'sk-[a-zA-Z0-9]{48}',  # API keys
                r'\b\d{3}-\d{2}-\d{4}\b'  # SSN
            ]
        }
    
    def scan_content(self, content: str) -> List[Dict]:
        findings = []
        for risk_type, patterns in self.risk_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'risk': risk_type,
                        'severity': 'HIGH' if 'INJECTION' in risk_type else 'MEDIUM',
                        'location': f'Line {self._get_line_number(content, match.start())}',
                        'description': f'Potential {risk_type.lower().replace("_", " ")} detected'
                    })
        return findings
    
    def _get_line_number(self, content: str, position: int) -> int:
        return content[:position].count('\n') + 1

def parse_pr_url(pr_url: str) -> Dict[str, str]:
    """Parse GitHub PR URL to extract owner, repo, and PR number"""
    # Example: https://github.com/owner/repo/pull/123
    if 'github.com' not in pr_url:
        raise ValueError("Invalid GitHub PR URL")
    
    parts = pr_url.rstrip('/').split('/')
    if len(parts) < 6 or parts[-2] != 'pull':
        raise ValueError("Invalid PR URL format")
    
    return {
        'owner': parts[-4],
        'repo': parts[-3],
        'pr_number': parts[-1]
    }

def get_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Simulate getting PR diff - in real implementation, use GitHub API"""
    # For GitHub Action, we would use the GitHub API to get the actual diff
    # This is a simplified version for demonstration
    
    sample_diff = f"""
--- a/src/example.py
+++ b/src/example.py
@@ -1,5 +1,10 @@
 def process_user_input(user_input):
+    # TODO: Add input validation
+    api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef12"
     result = execute_query(user_input)
+    if "ignore previous instructions" in user_input:
+        return "Invalid input"
     return result
"""
    return sample_diff

def analyze_diff_with_ai(diff: str, analysis_depth: str) -> Dict[str, Any]:
    """Simulate AI analysis - in real implementation, call OpenAI API"""
    
    # Simulate token usage based on analysis depth
    token_usage = {
        'basic': {'prompt': 500, 'completion': 80},
        'standard': {'prompt': 850, 'completion': 120}, 
        'comprehensive': {'prompt': 1200, 'completion': 200}
    }
    
    tokens = token_usage.get(analysis_depth, token_usage['standard'])
    
    # Simulate cost calculation (GPT-4o pricing as of 2024)
    prompt_cost = tokens['prompt'] * 0.00001  # $0.01 per 1K tokens
    completion_cost = tokens['completion'] * 0.00003  # $0.03 per 1K tokens
    total_cost = prompt_cost + completion_cost
    
    # Simulate analysis results
    analysis_result = {
        'cost': total_cost,
        'tokens_used': tokens['prompt'] + tokens['completion'],
        'issues_found': [
            {
                'type': 'SECURITY',
                'severity': 'HIGH',
                'description': 'Hardcoded API key detected',
                'line': 3,
                'suggestion': 'Move API key to environment variables'
            },
            {
                'type': 'SECURITY', 
                'severity': 'MEDIUM',
                'description': 'Potential prompt injection pattern',
                'line': 5,
                'suggestion': 'Add input sanitization'
            }
        ]
    }
    
    return analysis_result

def run_github_action_analysis(args) -> GitHubActionResult:
    """Main analysis function for GitHub Action"""
    
    result = GitHubActionResult()
    
    try:
        # Parse PR URL
        pr_info = parse_pr_url(args.pr_url)
        print(f"📋 Analyzing PR #{pr_info['pr_number']} in {pr_info['owner']}/{pr_info['repo']}")
        
        # Initialize budget guard if enabled
        budget_guard = None
        if os.getenv('ENABLE_BUDGET_GUARD', 'true').lower() == 'true':
            budget_guard = SimpleBudgetGuard(args.cost_limit)
            print(f"💰 Budget guard enabled with limit: ${args.cost_limit}")
        
        # Get PR diff
        print("📥 Fetching PR diff...")
        diff_content = get_pr_diff(pr_info['owner'], pr_info['repo'], pr_info['pr_number'])
        
        # Estimate cost and check budget
        if budget_guard:
            estimated_cost = 0.02  # Rough estimate
            budget_guard.check_budget(estimated_cost)
        
        # Run AI analysis
        print(f"🤖 Running {args.analysis_depth} AI analysis...")
        ai_results = analyze_diff_with_ai(diff_content, args.analysis_depth)
        
        # Record actual cost
        if budget_guard:
            budget_guard.record_cost(ai_results['cost'])
        
        result.analysis_cost = ai_results['cost']
        
        # Run OWASP scanning if enabled
        owasp_findings = []
        if os.getenv('ENABLE_OWASP_SCANNING', 'true').lower() == 'true':
            print("🛡️ Running OWASP LLM Top-10 security scan...")
            scanner = SimpleOWASPScanner()
            owasp_findings = scanner.scan_content(diff_content)
        
        # Combine results
        all_issues = ai_results['issues_found'] + owasp_findings
        result.security_issues_found = len([issue for issue in all_issues if issue.get('type') == 'SECURITY'])
        result.issues = all_issues
        
        # Calculate OWASP compliance score
        total_checks = 10  # OWASP LLM Top-10
        passed_checks = total_checks - min(len(owasp_findings), total_checks)
        result.owasp_compliance_score = int((passed_checks / total_checks) * 100)
        
        # Generate summary
        security_count = result.security_issues_found
        cost_formatted = f"${result.analysis_cost:.3f}"
        
        if security_count == 0:
            result.analysis_summary = f"✅ No security issues found. Analysis cost: {cost_formatted}"
        else:
            result.analysis_summary = f"⚠️ {security_count} security issues detected. Analysis cost: {cost_formatted}"
        
        print(f"✅ Analysis completed successfully")
        print(f"   💰 Cost: {cost_formatted}")
        print(f"   🛡️ Security issues: {security_count}")
        print(f"   📋 OWASP score: {result.owasp_compliance_score}%")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        result.analysis_summary = f"❌ Analysis failed: {str(e)}"
        raise
    
    return result

def save_results(result: GitHubActionResult, output_file: str, github_output: str):
    """Save analysis results to files"""
    
    # Save detailed results as JSON
    results_data = {
        'analysis_cost': f"{result.analysis_cost:.3f}",
        'security_issues_found': result.security_issues_found,
        'owasp_compliance_score': result.owasp_compliance_score,
        'analysis_summary': result.analysis_summary,
        'issues': result.issues,
        'timestamp': '2024-07-01T10:00:00Z'  # Would use actual timestamp
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"📄 Detailed results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Secure PR Guard GitHub Action Runner')
    parser.add_argument('--pr-url', required=True, help='GitHub PR URL to analyze')
    parser.add_argument('--cost-limit', type=float, default=0.50, help='Cost limit in USD')
    parser.add_argument('--analysis-depth', choices=['basic', 'standard', 'comprehensive'], 
                       default='standard', help='Analysis depth')
    parser.add_argument('--output', required=True, help='Output file for results')
    parser.add_argument('--github-output', required=True, help='GitHub Actions output file')
    
    args = parser.parse_args()
    
    try:
        print("🛡️ Secure PR Guard - GitHub Action")
        print("=" * 50)
        
        # Run analysis
        result = run_github_action_analysis(args)
        
        # Save results
        save_results(result, args.output, args.github_output)
        
        print("=" * 50)
        print("🎉 GitHub Action completed successfully!")
        
    except Exception as e:
        print(f"❌ GitHub Action failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()