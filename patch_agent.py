# patch_agent.py
import difflib, json, os
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LOW_RISK_TYPES = {"indentation", "length", "style"}

def build_patch(diff_text: str, issues: List[Dict]) -> str:
    """仅选择低风险 issue，生成 unified diff 补丁"""
    # 过滤
    lines_to_fix = [i for i in issues if i["type"] in LOW_RISK_TYPES]
    if not lines_to_fix:
        return ""

    prompt = f"""
You are an automated code fixer. 
Given the original diff (git style) below, modify ONLY the lines mentioned.
Return **full unified diff** starting with --- / +++.

### ORIGINAL DIFF
{diff_text}

### LINT ISSUES
{json.dumps(lines_to_fix, indent=2)}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )
        
        # 记录token使用情况
        usage = response.usage
        total_tokens = usage.total_tokens
        cost_estimate = total_tokens * 0.00015 / 1000  # gpt-4o-mini pricing
        print(f"💰 Token usage: {total_tokens} tokens (~${cost_estimate:.4f})")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return ""
