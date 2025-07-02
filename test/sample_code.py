# Test file for Secure PR Guard Action
import os

def process_user_input(user_input):
    # This contains potential security issues for testing
    api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef12"  # Hardcoded API key
    
    if "ignore previous instructions" in user_input:  # Potential prompt injection
        return "Invalid input"
    
    # Email in code (PII)
    admin_email = "admin@company.com"
    
    result = execute_query(user_input)
    return result

def execute_query(query):
    # Unsafe query execution
    return eval(query)  # Code injection vulnerability
