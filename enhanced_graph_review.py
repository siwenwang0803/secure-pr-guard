import logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import sys
import json
import os
import time
from datetime import datetime, timezone
from contextlib import nullcontext
from fetch_diff import fetch_pr_diff
from nitpicker import nitpick
from architect import architect
from post_comment import post_comment, format_review_comment
from patch_agent import build_patch, format_patch_summary
from create_patch_pr import create_patch_pr_workflow
from cost_logger import get_total_cost_for_pr, generate_cost_summary

# OpenTelemetry setup for Grafana Cloud
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize tracer only if OTLP_ENDPOINT is configured
    if os.getenv("OTLP_ENDPOINT"):
        resource = Resource(attributes={
            "service.name": "secure-pr-guard",
            "service.version": "v2.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "production"),
            "service.namespace": "pr-automation"
        })
        
        provider = TracerProvider(resource=resource)
        
        # Grafana Cloud uses Basic Auth
        import base64
        username = os.getenv("OTLP_USERNAME", "1299868")  # Updated to match your actual username
        password = os.getenv("OTLP_API_KEY")
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_ENDPOINT") + "/v1/traces",
            headers={
                "Authorization": f"Basic {credentials}",
                "X-Scope-OrgID": username,
            }
        )
        
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("secure-pr-guard")
        print("📊 Observability: Connected to Grafana Cloud")
    else:
        tracer = None
        
except ImportError:
    tracer = None
    print("⚠️ OpenTelemetry not installed - observability disabled")

# Define state schema for the multi-agent workflow with patch capability and cost tracking
class ReviewState(TypedDict):
    pr_url: str
    diff_content: str
    nitpicker_result: dict
    nitpicker_cost: dict
    architect_result: dict
    patch_content: str
    patch_cost: dict
    patch_pr_url: str
    comment_posted: bool
    total_cost: float
    total_tokens: int
    error: str

def extract_pr_metadata(pr_url: str) -> dict:
    """Extract standardized PR metadata from GitHub URL"""
    metadata = {}
    if pr_url and pr_url.startswith("https://github.com/"):
        try:
            parts = pr_url.rstrip('/').split('/')
            metadata = {
                "pr.url": pr_url,
                "pr.repository": f"{parts[3]}/{parts[4]}",
                "pr.owner": parts[3],
                "pr.repo": parts[4],
                "pr.number": int(parts[6])
            }
        except (IndexError, ValueError):
            metadata = {"pr.url": pr_url}
    return metadata

def fetch_diff_node(state: ReviewState) -> ReviewState:
    """
    Node 1: Fetch PR diff from GitHub
    """
    try:
        with tracer.start_as_current_span("fetch.diff") if tracer else nullcontext() as span:
            print(f"🔍 Fetching diff from: {state['pr_url']}")
            
            if span:
                span.set_attributes({
                    "operation.type": "fetch",
                    "operation.name": "fetch_pr_diff",
                    **extract_pr_metadata(state['pr_url'])
                })
            
            start_time = time.time()
            diff = fetch_pr_diff(state['pr_url'])
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Preview diff length for debugging
            print(f"📄 Diff length: {len(diff)} characters")
            
            if span:
                span.set_attributes({
                    "diff.size_chars": len(diff),
                    "latency.ms": latency_ms
                })
            
            return {
                "pr_url": state["pr_url"],
                "diff_content": diff,
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
    except Exception as e:
        error_msg = f"Failed to fetch diff: {str(e)}"
        print(f"❌ {error_msg}")
        
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
        
        return {
            "pr_url": state["pr_url"],
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
        
        # Add observability span with standardized attributes
        with tracer.start_as_current_span("nitpicker.analyze") if tracer else nullcontext() as span:
            start_time = time.time()
            result, cost_info = nitpick(state["diff_content"], state["pr_url"])
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract analysis summary
            issues_count = len(result.get("issues", []))
            analysis_summary = result.get("analysis_summary", {})
            ai_detected = analysis_summary.get("ai_detected", 0)
            rule_detected = analysis_summary.get("rule_detected", 0)
            
            # Record standardized metrics in span
            if span:
                span.set_attributes({
                    # Operation classification (for drill-down)
                    "operation.type": "nitpicker",
                    "operation.name": "analyze_code_security",
                    
                    # Cost metrics (for cost governance)
                    "cost.usd": cost_info.get("cost_usd", 0.0),
                    "cost.model": cost_info.get("model", "gpt-4o-mini"),
                    "cost.tokens.prompt": cost_info.get("prompt_tokens", 0),
                    "cost.tokens.completion": cost_info.get("completion_tokens", 0),
                    "cost.tokens.total": cost_info.get("total_tokens", 0),
                    
                    # Performance metrics (for SLO)
                    "latency.ms": latency_ms,
                    "latency.api_ms": cost_info.get("latency_ms", 0),
                    
                    # Business context
                    **extract_pr_metadata(state["pr_url"]),
                    
                    # Result metrics
                    "issues.found": issues_count,
                    "issues.ai_detected": ai_detected,
                    "issues.rule_detected": rule_detected,
                    "issues.security": len([i for i in result.get("issues", []) 
                                          if i.get("type") == "security"]),
                    
                    # Efficiency metrics
                    "tokens.prompt_ratio": round(
                        cost_info.get("prompt_tokens", 0) / cost_info.get("total_tokens", 1), 3
                    ) if cost_info.get("total_tokens", 0) > 0 else 0
                })
            
            # Show summary
            print(f"📋 Analysis complete:")
            print(f"   - AI detected: {ai_detected} issues")
            print(f"   - Security rules: {rule_detected} issues") 
            print(f"   - Total unique: {issues_count} issues")
            
            return {
                "pr_url": state["pr_url"],
                "diff_content": state["diff_content"],
                "nitpicker_result": result,
                "nitpicker_cost": cost_info,
                "architect_result": {},
                "patch_content": "",
                "patch_cost": {},
                "patch_pr_url": "",
                "comment_posted": False,
                "total_cost": cost_info.get("cost_usd", 0.0),
                "total_tokens": cost_info.get("total_tokens", 0),
                "error": ""
            }
    except Exception as e:
        error_msg = f"Nitpicker analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": {},
            "nitpicker_cost": {},
            "architect_result": {},
            "patch_content": "",
            "patch_cost": {},
            "patch_pr_url": "",
            "comment_posted": False,
            "total_cost": state.get("total_cost", 0.0),
            "total_tokens": state.get("total_tokens", 0),
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
        
        with tracer.start_as_current_span("architect.analyze") if tracer else nullcontext() as span:
            start_time = time.time()
            result = architect(state["nitpicker_result"])
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Show security summary
            summary = result.get("summary", {})
            risk_level = summary.get("risk_level", "unknown")
            security_issues = summary.get("security_issues", 0)
            
            if span:
                span.set_attributes({
                    # Operation classification
                    "operation.type": "architect",
                    "operation.name": "prioritize_security_issues",
                    
                    # Performance metrics
                    "latency.ms": latency_ms,
                    
                    # Risk assessment
                    "risk.level": risk_level,
                    "risk.score": {"critical": 10, "high": 7, "medium": 4, "low": 1}
                                 .get(risk_level, 0),
                    
                    # Issue categorization
                    "issues.security": security_issues,
                    "issues.critical": len([i for i in result.get("issues", [])
                                          if i.get("severity") == "critical"]),
                    "issues.high": len([i for i in result.get("issues", [])
                                      if i.get("severity") == "high"]),
                    
                    # Business context
                    **extract_pr_metadata(state["pr_url"])
                })
            
            print(f"🔍 Architecture analysis complete:")
            print(f"   - Risk level: {risk_level.upper()}")
            print(f"   - Security issues: {security_issues}")
            
            return {
                "pr_url": state["pr_url"],
                "diff_content": state["diff_content"],
                "nitpicker_result": state["nitpicker_result"],
                "nitpicker_cost": state["nitpicker_cost"],
                "architect_result": result,
                "patch_content": "",
                "patch_cost": {},
                "patch_pr_url": "",
                "comment_posted": False,
                "total_cost": state["total_cost"],
                "total_tokens": state["total_tokens"],
                "error": ""
            }
    except Exception as e:
        error_msg = f"Architect analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "nitpicker_cost": state["nitpicker_cost"],
            "architect_result": {},
            "patch_content": "",
            "patch_cost": {},
            "patch_pr_url": "",
            "comment_posted": False,
            "total_cost": state["total_cost"],
            "total_tokens": state["total_tokens"],
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
        
        with tracer.start_as_current_span("patch.generate") if tracer else nullcontext() as span:
            # Generate patch for low-risk issues
            start_time = time.time()
            issues = state["architect_result"].get("issues", [])
            
            # Count patchable issues
            safe_issues = [i for i in issues if i.get("type") in {"indentation", "length", "style"}]
            
            if span:
                span.set_attributes({
                    "operation.type": "patch",
                    "operation.name": "generate_safe_patches",
                    "patch.issues_total": len(issues),
                    "patch.issues_safe": len(safe_issues),
                    **extract_pr_metadata(state["pr_url"])
                })
            
            patch_content, patch_cost_info = build_patch(state["diff_content"], issues, state["pr_url"])
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Record standardized metrics
            if span:
                span.set_attributes({
                    # Cost metrics
                    "cost.usd": patch_cost_info.get("cost_usd", 0.0),
                    "cost.model": patch_cost_info.get("model", "gpt-4o-mini"),
                    "cost.tokens.prompt": patch_cost_info.get("prompt_tokens", 0),
                    "cost.tokens.completion": patch_cost_info.get("completion_tokens", 0),
                    "cost.tokens.total": patch_cost_info.get("total_tokens", 0),
                    
                    # Performance metrics
                    "latency.ms": latency_ms,
                    "latency.api_ms": patch_cost_info.get("latency_ms", 0),
                    
                    # Patch metrics
                    "patch.generated": bool(patch_content),
                    "patch.issues_patched": len(safe_issues) if patch_content else 0,
                    
                    # Efficiency metrics
                    "tokens.prompt_ratio": round(
                        patch_cost_info.get("prompt_tokens", 0) / patch_cost_info.get("total_tokens", 1), 3
                    ) if patch_cost_info.get("total_tokens", 0) > 0 else 0
                })
            
            if not patch_content:
                print("⏭️ No safe issues to patch - skipping patch creation")
                total_cost = state["total_cost"] + patch_cost_info.get("cost_usd", 0.0)
                total_tokens = state["total_tokens"] + patch_cost_info.get("total_tokens", 0)
                
                return {
                    "pr_url": state["pr_url"],
                    "diff_content": state["diff_content"],
                    "nitpicker_result": state["nitpicker_result"],
                    "nitpicker_cost": state["nitpicker_cost"],
                    "architect_result": state["architect_result"],
                    "patch_content": "",
                    "patch_cost": patch_cost_info,
                    "patch_pr_url": "",
                    "comment_posted": False,
                    "total_cost": total_cost,
                    "total_tokens": total_tokens,
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
                if span:
                    span.set_attribute("patch.pr_created", True)
                    span.set_attribute("patch.pr_url", patch_pr_url)
            else:
                print("⚠️ Patch PR creation failed, but analysis completed")
                if span:
                    span.set_attribute("patch.pr_created", False)
            
            # Calculate total cost
            total_cost = state["total_cost"] + patch_cost_info.get("cost_usd", 0.0)
            total_tokens = state["total_tokens"] + patch_cost_info.get("total_tokens", 0)
            
            return {
                "pr_url": state["pr_url"],
                "diff_content": state["diff_content"],
                "nitpicker_result": state["nitpicker_result"],
                "nitpicker_cost": state["nitpicker_cost"],
                "architect_result": state["architect_result"],
                "patch_content": patch_content,
                "patch_cost": patch_cost_info,
                "patch_pr_url": patch_pr_url or "",
                "comment_posted": False,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "error": ""
            }
        
    except Exception as e:
        error_msg = f"Patch generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "nitpicker_cost": state["nitpicker_cost"],
            "architect_result": state["architect_result"],
            "patch_content": "",
            "patch_cost": {},
            "patch_pr_url": "",
            "comment_posted": False,
            "total_cost": state["total_cost"],
            "total_tokens": state["total_tokens"],
            "error": error_msg
        }

def comment_node(state: ReviewState) -> ReviewState:
    """
    Node 5: Post formatted comment to GitHub PR
    """
    if state.get("error"):
        return state
    
    try:
        print("💬 Formatting and posting GitHub comment...")
        
        with tracer.start_as_current_span("comment.post") if tracer else nullcontext() as span:
            start_time = time.time()
            
            if span:
                span.set_attributes({
                    "operation.type": "comment",
                    "operation.name": "post_pr_comment",
                    **extract_pr_metadata(state["pr_url"])
                })
            
            # Format the comment
            comment_body = format_review_comment(
                state["architect_result"], 
                state["pr_url"]
            )
            
            # Post to GitHub
            success = post_comment(state["pr_url"], comment_body)
            latency_ms = int((time.time() - start_time) * 1000)
            
            if span:
                span.set_attributes({
                    "comment.posted": success,
                    "comment.length": len(comment_body),
                    "latency.ms": latency_ms
                })
            
            if success:
                print("✅ Comment posted successfully!")
            else:
                print("⚠️ Comment posting failed, but analysis completed")
            
            return {
                "pr_url": state["pr_url"],
                "diff_content": state["diff_content"],
                "nitpicker_result": state["nitpicker_result"],
                "nitpicker_cost": state["nitpicker_cost"],
                "architect_result": state["architect_result"],
                "patch_content": state["patch_content"],
                "patch_cost": state["patch_cost"],
                "patch_pr_url": state["patch_pr_url"],
                "comment_posted": success,
                "total_cost": state["total_cost"],
                "total_tokens": state["total_tokens"],
                "error": "" if success else "Comment posting failed"
            }
    except Exception as e:
        error_msg = f"Comment posting failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
        
        return {
            "pr_url": state["pr_url"],
            "diff_content": state["diff_content"],
            "nitpicker_result": state["nitpicker_result"],
            "nitpicker_cost": state["nitpicker_cost"],
            "architect_result": state["architect_result"],
            "patch_content": state["patch_content"],
            "patch_cost": state["patch_cost"],
            "patch_pr_url": state["patch_pr_url"],
            "comment_posted": False,
            "total_cost": state["total_cost"],
            "total_tokens": state["total_tokens"],
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
    
    # Return both raw graph for visualization and compiled graph for execution
    return graph, graph.compile()

def main():
    """
    Main execution function with observability
    
    """
    # Add CLI argument parsing
    import argparse
    parser = argparse.ArgumentParser(description='Secure PR Guard - AI-powered PR review')
    parser.add_argument('pr_url', help='GitHub PR URL to review')
    parser.add_argument('--profile', action='store_true', help='Output trace URL for profiling')
    args = parser.parse_args()
    
    pr_url = args.pr_url
    # Flowchart generation (run once with GEN_GRAPH=1)
    if os.getenv("GEN_GRAPH"):
        print("🎨 Generating workflow flowchart...")
        
        # Create docs directory
        os.makedirs("docs", exist_ok=True)
        
        # Create raw graph for visualization
        raw_graph, _ = create_review_graph()
        
        try:
            # Generate flowchart
            graph_image = raw_graph.get_graph().draw_mermaid()
            
            # Save as text file first (Mermaid format)
            with open("docs/flowchart.mmd", "w") as f:
                f.write(graph_image)
            
            print("✅ Mermaid flowchart generated: docs/flowchart.mmd")
            print("📝 To convert to PNG, visit: https://mermaid.live/ and paste the content")
            print("🔗 Or use: npx @mermaid-js/mermaid-cli -i docs/flowchart.mmd -o docs/flowchart.png")
            
            # Also try direct PNG generation if dependencies available
            try:
                png_data = raw_graph.get_graph().draw_png()
                with open("docs/flowchart.png", "wb") as f:
                    f.write(png_data)
                print("✅ PNG flowchart generated: docs/flowchart.png")
            except Exception as png_error:
                print(f"⚠️ PNG generation failed: {png_error}")
                print("📝 Manual conversion recommended using Mermaid Live Editor")
                
        except Exception as e:
            print(f"❌ Flowchart generation failed: {str(e)}")
            print("💡 Try: pip install graphviz and ensure Graphviz is installed on system")
        
        sys.exit(0)
    
    # Main workflow execution
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
    raw_graph, workflow = create_review_graph()
    
    # Initial state
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
    
    # Execute workflow with observability
    try:
        with tracer.start_as_current_span("pr_review.workflow") if tracer else nullcontext() as span:
            trace_id = None
            if span and args.profile:
                trace_context = span.get_span_context()
                trace_id = format(trace_context.trace_id, '032x')
                print(f"\n🔍 Trace ID: {trace_id}")
            if span:
                # Extract PR metadata
                pr_metadata = extract_pr_metadata(pr_url)
                span.set_attributes({
                    # Service identification
                    "workflow.name": "secure_pr_guard",
                    "workflow.version": "2.0",
                    
                    # PR context
                    **pr_metadata,
                    
                    # Workflow metadata
                    "workflow.start_time": datetime.now(timezone.utc).isoformat()
                })
            
            final_state = workflow.invoke(initial_state)

            # Output trace URL if profile flag is set
            if args.profile and trace_id:
                grafana_url = "https://siwenwang0803.grafana.net"
                trace_url = f"{grafana_url}/explore?orgId=1&left=%7B%22datasource%22:%22grafanacloud-siwenwang0803-traces%22,%22queries%22:%5B%7B%22query%22:%22{trace_id}%22,%22queryType%22:%22traceql%22%7D%5D%7D"
                
                print(f"\n📊 View trace in Grafana:")
                print(f"   {trace_url}")
                print(f"\n💡 Or search in Grafana Explore with:")
                print(f"   Trace ID: {trace_id}")
            
            # Record final summary metrics
            if span:
                summary = final_state["architect_result"].get("summary", {})
                issues = final_state["architect_result"].get("issues", [])
                
                span.set_attributes({
                    # Workflow results
                    "workflow.status": "success" if not final_state.get("error") else "error",
                    "workflow.error": final_state.get("error", ""),
                    
                    # Issue summary
                    "issues.total": summary.get("total_issues", 0),
                    "issues.security": summary.get("security_issues", 0),
                    "issues.critical": len([i for i in issues if i.get("severity") == "critical"]),
                    "issues.high": len([i for i in issues if i.get("severity") == "high"]),
                    "issues.medium": len([i for i in issues if i.get("severity") == "medium"]),
                    "issues.low": len([i for i in issues if i.get("severity") == "low"]),
                    
                    # Risk assessment
                    "risk.level": summary.get("risk_level", "unknown"),
                    "risk.score": {"critical": 10, "high": 7, "medium": 4, "low": 1}
                                 .get(summary.get("risk_level", "low"), 0),
                    
                    # Cost summary
                    "cost.total_usd": final_state.get("total_cost", 0.0),
                    "cost.tokens.total": final_state.get("total_tokens", 0),
                    
                    # Performance summary
                    "latency.total_ms": (
                        final_state.get("nitpicker_cost", {}).get("latency_ms", 0) +
                        final_state.get("patch_cost", {}).get("latency_ms", 0)
                    ),
                    
                    # Workflow outcomes
                    "patch.created": bool(final_state.get("patch_pr_url")),
                    "patch.pr_url": final_state.get("patch_pr_url", ""),
                    "comment.posted": final_state.get("comment_posted", False)
                })
        
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
                
                # Cost summary
                total_cost = final_state.get('total_cost', 0.0)
                total_tokens = final_state.get('total_tokens', 0)
                nitpicker_cost = final_state.get('nitpicker_cost', {})
                patch_cost = final_state.get('patch_cost', {})
                
                print(f"\n💰 COST ANALYSIS")
                print(f"   - Total Cost: ${total_cost:.6f}")
                print(f"   - Total Tokens: {total_tokens:,}")
                print(f"   - Nitpicker: ${nitpicker_cost.get('cost_usd', 0.0):.6f} ({nitpicker_cost.get('total_tokens', 0)} tokens)")
                if patch_cost.get('total_tokens', 0) > 0:
                    print(f"   - Patch Gen: ${patch_cost.get('cost_usd', 0.0):.6f} ({patch_cost.get('total_tokens', 0)} tokens)")
                
                # Performance metrics
                nitpicker_latency = nitpicker_cost.get('latency_ms', 0)
                patch_latency = patch_cost.get('latency_ms', 0)
                total_latency = nitpicker_latency + patch_latency
                
                print(f"\n⚡ PERFORMANCE METRICS")
                print(f"   - Total Latency: {total_latency:,}ms ({total_latency/1000:.2f}s)")
                print(f"   - AI Analysis: {nitpicker_latency:,}ms")
                if patch_latency > 0:
                    print(f"   - Patch Generation: {patch_latency:,}ms")
                
                if final_state.get('patch_pr_url'):
                    print(f"\n🔗 Patch PR URL: {final_state['patch_pr_url']}")
                
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
                
                # Generate cost summary for logs
                cost_summary = get_total_cost_for_pr(pr_url)
                if cost_summary['operations'] > 0:
                    print(f"\n📊 SESSION SUMMARY")
                    print(f"   - Average Cost/Operation: ${cost_summary['total_cost']/cost_summary['operations']:.6f}")
                    print(f"   - Average Latency: {cost_summary['avg_latency_ms']:.0f}ms")
                
                # Print abbreviated JSON for debugging (without cost details to avoid clutter)
                print(f"\n🔍 Analysis Results Summary:")
                summary_json = {
                    "total_issues": summary.get("total_issues", 0),
                    "risk_level": summary.get("risk_level", "unknown"),
                    "security_issues": summary.get("security_issues", 0),
                    "cost_usd": total_cost,
                    "tokens": total_tokens,
                    "latency_ms": total_latency
                }
                print(json.dumps(summary_json, indent=2))
                
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        if tracer:
            span = trace.get_current_span()
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
        sys.exit(1)

if __name__ == "__main__":
    main()