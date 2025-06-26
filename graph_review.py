from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import sys
import json
from fetch_diff import fetch_pr_diff
from nitpicker import nitpick

# Define state schema for the workflow
class ReviewState(TypedDict):
    pr_url: str
    diff_content: str
    analysis_result: dict
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
            "analysis_result": {},
            "error": ""
        }
    except Exception as e:
        error_msg = f"Failed to fetch diff: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": "",
            "analysis_result": {},
            "error": error_msg
        }

def nitpicker_node(state: ReviewState) -> ReviewState:
    """
    Node 2: Analyze diff with AI nitpicker
    """
    if state.get("error"):
        # Skip if previous node failed
        return state
    
    try:
        print("🤖 Running AI code analysis...")
        result = nitpick(state["diff_content"])
        
        # Show summary
        issues_count = len(result.get("issues", []))
        print(f"📋 Found {issues_count} issues")
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "analysis_result": result,
            "error": ""
        }
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "analysis_result": {},
            "error": error_msg
        }

def create_review_graph():
    """
    Create and compile the review workflow graph
    """
    # Initialize graph with state schema
    graph = StateGraph(ReviewState)
    
    # Add nodes
    graph.add_node("fetch_diff", fetch_diff_node)
    graph.add_node("nitpicker", nitpicker_node)
    
    # Define edges (workflow sequence)
    graph.add_edge(START, "fetch_diff")
    graph.add_edge("fetch_diff", "nitpicker")
    graph.add_edge("nitpicker", END)
    
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
    
    print("🚀 Starting PR Review Workflow")
    print("=" * 50)
    
    # Create and run the workflow
    workflow = create_review_graph()
    
    # Initial state
    initial_state = {
        "pr_url": pr_url,
        "diff_content": "",
        "analysis_result": {},
        "error": ""
    }
    
    # Execute workflow
    try:
        final_state = workflow.invoke(initial_state)
        
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS")
        print("=" * 50)
        
        if final_state["error"]:
            print(f"❌ Workflow failed: {final_state['error']}")
            sys.exit(1)
        else:
            # Pretty print the analysis result
            result = final_state["analysis_result"]
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Summary
            issues = result.get("issues", [])
            if issues:
                print(f"\n✅ Analysis complete! Found {len(issues)} issues to review.")
            else:
                print(f"\n✅ Analysis complete! No issues found - great code!")
                
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()