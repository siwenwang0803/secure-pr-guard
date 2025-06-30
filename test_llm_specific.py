+ # This should trigger LLM03 (prompt leakage)
+ print(f"System prompt: {system_prompt}")
+ log.debug(f"Internal instruction: {internal_instruction}")
+ 
+ # This should trigger LLM04 (unsafe calls)  
+ subprocess.run(user_command)
+ eval(dynamic_code)
+ os.system("rm -rf /")
+ 
+ # Also some existing patterns
+ password = "hardcoded123"
