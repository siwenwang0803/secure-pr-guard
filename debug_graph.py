import sys
print("🔍 Starting debug...")

pr_url = sys.argv[1] if len(sys.argv) > 1 else "test"
print(f"🔍 PR URL: {pr_url}")

print("🔍 Importing modules...")
from graph_review import create_review_graph
print("🔍 Modules imported successfully")

print("🔍 Creating graph...")
raw_graph, workflow = create_review_graph()
print("🔍 Graph created successfully")

print("🔍 Creating initial state...")
initial_state = {
    "pr_url": pr_url,
    "diff_content": "",
    "nitpicker_result": {},
    "nitpicker_cost": {},
    "architect_result": {},
    "patch_content": "",
    "patch_cost": {},
    "patch_pr_url": "",
    "comment_posted": False,
    "total_cost": 0.0,
    "total_tokens": 0,
    "error": ""
}
print("🔍 Initial state created")

print("🔍 About to invoke workflow...")
