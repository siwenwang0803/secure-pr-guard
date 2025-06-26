from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import sys
import json
from fetch_diff import fetch_pr_diff
from nitpicker import nitpick
from architect import architect
from post_comment import post_comment, format_review_comment
from patch_agent import build_patch, format_patch_summary
from create_patch_pr import create_patch_pr_workflow

# Define state schema for the multi-agent workflow with patch capability
class ReviewState(TypedDict):
    pr_url: str
    diff_content: str
    nitpicker_result: dict
    architect_result: dict
    patch_content: str
    patch_pr_url: str
    comment_posted: bool
    error: str

def fetch_diff_node(state: ReviewState) -> ReviewState:
    """
    Node 1: Fetch PR diff from GitHub
    """
    try:
        print(f"🔍 Fetching diff from: {state['pr_url']}")
        diff = fetch_pr_diff(state['pr_url'])
        
        # Preview diff length for debugging
        print(f"📄 Diff length: {len(diff)} characters")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": diff,
            "nitpicker_result": {},
            "architect_result": {},
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": ""
        }
    except Exception as e:
        error_msg = f"Failed to fetch diff: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": "",
            "nitpicker_result": {},
            "architect_result": {},
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": error_msg
        }

def patch_node(state: ReviewState) -> ReviewState:
    """
    Node 4: Generate and apply patches for low-risk issues
    """
    if state.get("error"):
        return state
    
    try:
        print("🛠️ Generating patches for safe formatting issues...")
        
        # Generate patch for low-risk issues
        issues = state["architect_result"].get("issues", [])
        patch_content = build_patch(state["diff_content"], issues)
        
        if not patch_content:
            print("⏭️ No safe issues to patch - skipping patch creation")
            return {
                "pr_url": state["pr_url"],
                "diff_content": state["diff_content"],
                "nitpicker_result": state["nitpicker_result"],
                "architect_result": state["architect_result"],
                "patch_content": "",
                "patch_pr_url": "",
                "comment_posted": False,
                "error": ""
            }
        
        # Extract repository info from PR URL
        parts = state["pr_url"].rstrip('/').split('/')
        owner = parts[3]
        repo = parts[4]
        pr_number = parts[6]
        
        # Generate patch summary
        low_risk_issues = [i for i in issues if i.get("type") in {"indentation", "length", "style"}]
        patch_summary = format_patch_summary(low_risk_issues)
        
        # Create patch PR
        print("📝 Creating Draft PR with patches...")
        patch_pr_url = create_patch_pr_workflow(owner, repo, pr_number, patch_content, patch_summary)
        
        if patch_pr_url:
            print(f"✅ Patch PR created successfully: {patch_pr_url}")
        else:
            print("⚠️ Patch PR creation failed, but analysis completed")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": state["architect_result"],
            "patch_content": patch_content,
            "patch_pr_url": patch_pr_url or "",
            "comment_posted": False,
            "error": ""
        }
        
    except Exception as e:
        error_msg = f"Patch generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": state["architect_result"],
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": error_msg
        }

def nitpicker_node(state: ReviewState) -> ReviewState:
    """
    Node 2: Analyze diff with AI nitpicker + security rules
    """
    if state.get("error"):
        # Skip if previous node failed
        return state
    
    try:
        print("🤖 Running AI code analysis + OWASP security checks...")
        result = nitpick(state["diff_content"])
        
        # Show summary
        issues_count = len(result.get("issues", []))
        analysis_summary = result.get("analysis_summary", {})
        ai_detected = analysis_summary.get("ai_detected", 0)
        rule_detected = analysis_summary.get("rule_detected", 0)
        
        print(f"📋 Analysis complete:")
        print(f"   - AI detected: {ai_detected} issues")
        print(f"   - Security rules: {rule_detected} issues") 
        print(f"   - Total unique: {issues_count} issues")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": result,
            "architect_result": {},
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": ""
        }
    except Exception as e:
        error_msg = f"Nitpicker analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": {},
            "architect_result": {},
            "comment_posted": False,
            "error": error_msg
        }

def architect_node(state: ReviewState) -> ReviewState:
    """
    Node 3: Architectural analysis and security prioritization
    """
    if state.get("error"):
        return state
    
    try:
        print("🏗️ Running architectural security analysis...")
        result = architect(state["nitpicker_result"])
        
        # Show security summary
        summary = result.get("summary", {})
        risk_level = summary.get("risk_level", "unknown")
        security_issues = summary.get("security_issues", 0)
        
        print(f"🔍 Architecture analysis complete:")
        print(f"   - Risk level: {risk_level.upper()}")
        print(f"   - Security issues: {security_issues}")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": result,
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": ""
        }
    except Exception as e:
        error_msg = f"Architect analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": {},
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": error_msg
        }

def comment_node(state: ReviewState) -> ReviewState:
    """
    Node 4: Post formatted comment to GitHub PR
    """
    if state.get("error"):
        return state
    
    try:
        print("💬 Formatting and posting GitHub comment...")
        
        # Format the comment
        comment_body = format_review_comment(
            state["architect_result"], 
            state["pr_url"]
        )
        
        # Post to GitHub
        success = post_comment(state["pr_url"], comment_body)
        
        if success:
            print("✅ Comment posted successfully!")
        else:
            print("⚠️ Comment posting failed, but analysis completed")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": state["architect_result"],
            "comment_posted": success,
            "error": "" if success else "Comment posting failed"
        }
    except Exception as e:
        error_msg = f"Comment posting failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "architect_result": state["architect_result"],
            "patch_content": "",
            "patch_pr_url": "",
            "comment_posted": False,
            "error": error_msg
        }

def create_review_graph():
    """
    Create and compile the multi-agent review workflow graph with patch capability
    """
    # Initialize graph with state schema
    graph = StateGraph(ReviewState)
    
    # Add nodes in execution order
    graph.add_node("fetch_diff", fetch_diff_node)
    graph.add_node("nitpicker", nitpicker_node)
    graph.add_node("architect", architect_node)
    graph.add_node("patch", patch_node)
    graph.add_node("comment", comment_node)
    
    # Define edges (workflow sequence)
    graph.add_edge(START, "fetch_diff")
    graph.add_edge("fetch_diff", "nitpicker")
    graph.add_edge("nitpicker", "architect")
    graph.add_edge("architect", "patch")
    graph.add_edge("patch", "comment")
    graph.add_edge("comment", END)
    
    # Compile the graph
    return graph.compile()

def main():
    """
    Main execution function
    """
    if len(sys.argv) != 2:
        print("Usage: python graph_review.py <PR_URL>")
        print("Example: python graph_review.py https://github.com/owner/repo/pull/123")
        sys.exit(1)
    
    pr_url = sys.argv[1]
    
    # Validate URL format
    if not pr_url.startswith("https://github.com/") or "/pull/" not in pr_url:
        print("❌ Error: Invalid GitHub PR URL format")
        print("Expected: https://github.com/owner/repo/pull/number")
        sys.exit(1)
    
    print("🚀 Starting Multi-Agent PR Review Workflow with Auto-Patch")
    print("=" * 70)
    print("📋 Workflow: Fetch → Nitpicker → Architect → Patch → Comment")
    print("=" * 70)
    
    # Create and run the workflow
    workflow = create_review_graph()
    
    # Initial state
    initial_state = {
        "pr_url": pr_url,
        "diff_content": "",
        "nitpicker_result": {},
        "architect_result": {},
        "patch_content": "",
        "patch_pr_url": "",
        "comment_posted": False,
        "error": ""
    }
    
    # Execute workflow
    try:
        final_state = workflow.invoke(initial_state)
        
        print("\n" + "=" * 70)
        print("📊 WORKFLOW RESULTS")
        print("=" * 70)
        
        if final_state["error"]:
            print(f"❌ Workflow failed: {final_state['error']}")
            sys.exit(1)
        else:
            # Show detailed results
            architect_result = final_state["architect_result"]
            summary = architect_result.get("summary", {})
            
            print(f"✅ Analysis Complete!")
            print(f"   - Risk Level: {summary.get('risk_level', 'unknown').upper()}")
            print(f"   - Total Issues: {summary.get('total_issues', 0)}")
            print(f"   - Security Issues: {summary.get('security_issues', 0)}")
            print(f"   - Comment Posted: {'✅ Yes' if final_state['comment_posted'] else '❌ Failed'}")
            print(f"   - Patch PR Created: {'✅ Yes' if final_state.get('patch_pr_url') else '⏭️ Skipped'}")
            
            if final_state.get('patch_pr_url'):
                print(f"   - Patch PR URL: {final_state['patch_pr_url']}")
            
            # Show issues breakdown
            issues = architect_result.get("issues", [])
            if issues:
                print(f"\n📋 Issues Found:")
                for issue in issues:
                    severity_emoji = {
                        "critical": "🚨",
                        "high": "🔴", 
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(issue.get("severity"), "⚪")
                    
                    print(f"   {severity_emoji} Line {issue['line']} ({issue['type']}): {issue['comment']}")
            
            # Pretty print full JSON for debugging
            print(f"\n🔍 Full Analysis Results:")
            print(json.dumps(architect_result, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()