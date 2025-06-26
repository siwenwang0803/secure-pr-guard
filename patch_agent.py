# patch_agent.py
import difflib, json, openai, os
from typing import List, Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    rsp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return rsp.choices[0].message.content.strip()
