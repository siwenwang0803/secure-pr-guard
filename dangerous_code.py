import os
import pickle
import subprocess

# LLM01 Prompt Injection vulnerabilities
def create_prompt(user_input):
    system_prompt = "You are a helpful assistant. " + user_input  # Direct concatenation
    return f"{{user_query: {user_input}}}"  # Template injection

# LLM02 Insecure Output Handling
def process_ai_response(ai_output):
    exec(ai_output)  # Critical: Direct execution
    result = pickle.loads(ai_output)  # Unsafe deserialization
    subprocess.run(ai_output, shell=True)  # Command injection

# Traditional security issues
API_KEY = "sk-1234567890abcdef1234567890abcdef"  # Hardcoded API key
password = "super_secret_123"  # Hardcoded password

def unsafe_sql_query(ai_generated_where_clause):
    query = "SELECT * FROM users WHERE " + ai_generated_where_clause  # SQL injection
    return query

# Code quality issues
def extremely_long_function_name_that_definitely_exceeds_one_hundred_twenty_characters_and_should_trigger_length_warning():
	print("This line uses tabs instead of spaces")  # Tab indentation
    return "mixed indentation issue"

class UnsafeAIHandler:
    def __init__(self):
        self.secret_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # GitHub token
    
    def handle_llm_output(self, response):
        # Multiple LLM02 violations
        eval(response)  # Code execution
        os.system(response)  # System command execution
        with open(response, 'w') as f:  # File operation with untrusted input
            f.write("data")
