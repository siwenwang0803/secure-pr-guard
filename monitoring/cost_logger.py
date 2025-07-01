"""
Cost Logger with Enhanced OpenTelemetry Integration
Tracks API usage costs and exports telemetry data via OTLP/HTTP with Grafana-optimized attributes
"""

import os
import csv
import time
import pathlib
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import get_current_span, Status, StatusCode

# Add project root to Python path for proper imports
project_root = pathlib.Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Safe budget guard integration with proper error handling
BUDGET_GUARD_ENABLED = False
_budget_guard = None

def _get_budget_guard():
    """Safely initialize budget guard to avoid circular imports"""
    global _budget_guard, BUDGET_GUARD_ENABLED
    if _budget_guard is None:
        try:
            # Use absolute import path
            from monitoring.budget_guard import BudgetGuard
            _budget_guard = BudgetGuard()
            BUDGET_GUARD_ENABLED = True
            print("🛡️ Budget Guard integration enabled")
        except ImportError as e:
            BUDGET_GUARD_ENABLED = False
            _budget_guard = None
            print(f"⚠️ Budget Guard not available: {e}")
        except Exception as e:
            BUDGET_GUARD_ENABLED = False
            _budget_guard = None
            print(f"⚠️ Budget Guard initialization failed: {e}")
    return _budget_guard

def check_budget_integration_safe(pr_url: str, operation: str, cost: float, 
                                 latency_ms: int, tokens: int) -> None:
    """
    安全的 budget 检查函数，避免循环导入
    """
    try:
        guard = _get_budget_guard()
        if guard and BUDGET_GUARD_ENABLED:
            alerts = guard.check_budget_limits(pr_url=pr_url, operation=operation)
            
            # 添加到 OpenTelemetry span
            span = get_current_span()
            if span and span.is_recording():
                span.set_attributes({
                    "budget.monitoring.enabled": True,
                    "budget.check.alerts_triggered": len(alerts),
                    "budget.check.operation": operation
                })
                
                if alerts:
                    span.add_event("budget_check_completed", {
                        "alerts_count": len(alerts),
                        "highest_severity": max(alert.severity for alert in alerts) if alerts else "none"
                    })
        else:
            # Don't spam console in normal operation
            pass
            
    except Exception as e:
        print(f"⚠️ Budget integration error: {e}")
        
        # 记录错误到 span
        span = get_current_span()
        if span and span.is_recording():
            span.set_attributes({
                "budget.integration.error": str(e),
                "budget.integration.enabled": False
            })
   
# Cost tracking file
COST_CSV = pathlib.Path("logs/cost.csv")

# Model pricing (USD per token) - updated for accuracy
MODEL_PRICE = {
    "gpt-4o-mini": float(os.getenv("OPENAI_PRICE_GPT4O_MINI", "0.000150")),  # $0.15 per 1K tokens
    "gpt-4o": float(os.getenv("OPENAI_PRICE_GPT4O", "0.005000")),  # $5.00 per 1K tokens  
    "gpt-3.5-turbo": float(os.getenv("OPENAI_PRICE_GPT35", "0.001000")),  # $1.00 per 1K tokens
}

def initialize_cost_log():
    """Initialize the cost tracking CSV file with headers"""
    if not COST_CSV.exists():
        COST_CSV.parent.mkdir(exist_ok=True)
        with COST_CSV.open("w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "pr_url", 
                "operation",
                "model",
                "prompt_tokens",
                "completion_tokens", 
                "total_tokens",
                "cost_usd",
                "latency_ms"
            ])
        print(f"📊 Initialized cost tracking: {COST_CSV}")

def extract_pr_metadata(pr_url: str) -> Dict[str, Any]:
    """Extract standardized PR metadata from GitHub URL for OTEL attributes"""
    metadata = {}
    if pr_url and pr_url.startswith("https://github.com/"):
        try:
            parts = pr_url.rstrip('/').split('/')
            metadata = {
                "pr.url": pr_url,
                "pr.repository": f"{parts[3]}/{parts[4]}",
                "pr.owner": parts[3],
                "pr.repo": parts[4],
                "pr.number": int(parts[6]),
                "git.repository": f"{parts[3]}/{parts[4]}",  # Alternative naming for Grafana
                "github.pr.number": int(parts[6])
            }
        except (IndexError, ValueError):
            metadata = {"pr.url": pr_url}
    return metadata

def calculate_efficiency_metrics(prompt_tokens: int, completion_tokens: int, 
                                total_tokens: int, latency_ms: int, cost: float) -> Dict[str, float]:
    """Calculate efficiency metrics for monitoring and optimization"""
    if total_tokens == 0 or latency_ms == 0:
        return {}
    
    return {
        # Token efficiency
        "efficiency.prompt_ratio": round(prompt_tokens / total_tokens, 3),
        "efficiency.completion_ratio": round(completion_tokens / total_tokens, 3),
        
        # Performance efficiency  
        "efficiency.tokens_per_second": round((total_tokens / latency_ms) * 1000, 2),
        "efficiency.tokens_per_ms": round(total_tokens / latency_ms, 2),
        
        # Cost efficiency
        "efficiency.cost_per_token": round(cost / total_tokens, 6),
        "efficiency.cost_per_second": round((cost / latency_ms) * 1000, 6),
        
        # Composite efficiency score (higher is better)
        "efficiency.score": round((total_tokens / latency_ms) / (cost * 1000), 2)
    }

def log_cost(pr_url: str, operation: str, model: str, 
             prompt_tokens: int, completion_tokens: int, 
             total_tokens: int, latency_ms: int) -> float:
    """
    Enhanced cost logging with STANDARDIZED OpenTelemetry attributes
    """
    # Calculate cost
    price_per_token = MODEL_PRICE.get(model, 0.001)
    cost = total_tokens * price_per_token
    
    # Extract PR metadata
    pr_metadata = extract_pr_metadata(pr_url)
    
    # Calculate efficiency metrics
    efficiency_metrics = calculate_efficiency_metrics(
        prompt_tokens, completion_tokens, total_tokens, latency_ms, cost
    )
    
    # 🔭 Enhanced OpenTelemetry span attributes (FIXED - only set once)
    span = get_current_span()
    if span and span.is_recording():
        # 💰 COST GOVERNANCE ATTRIBUTES (Executive Dashboard)
        cost_attrs = {
            "cost.usd": round(cost, 6),                    # Total cost in USD
            "cost.model": model,                           # AI model used
            "cost.model.pricing": price_per_token,         # Price per token
            "cost.operation": operation,                   # Operation type for cost breakdown
            "cost.per_token": round(cost / total_tokens, 6) if total_tokens > 0 else 0,
        }
        
        # 🔤 TOKEN USAGE ATTRIBUTES (Resource Management)
        tokens_attrs = {
            "tokens.prompt": prompt_tokens,                # Input tokens
            "tokens.completion": completion_tokens,        # Output tokens  
            "tokens.total": total_tokens,                  # Total tokens
            "tokens.prompt_ratio": round(prompt_tokens / total_tokens, 3) if total_tokens > 0 else 0,
            "tokens.completion_ratio": round(completion_tokens / total_tokens, 3) if total_tokens > 0 else 0,
            "tokens.per_second": round((total_tokens / latency_ms) * 1000, 2) if latency_ms > 0 else 0,
        }
        
        # ⚡ LATENCY & PERFORMANCE ATTRIBUTES (SLO Monitoring)
        latency_attrs = {
            "latency.ms": latency_ms,                      # Latency in milliseconds
            "latency.seconds": round(latency_ms / 1000, 3), # Latency in seconds
            "latency.api_ms": latency_ms,                  # API call latency
            "latency.category": (                          # Performance category
                "fast" if latency_ms < 2000 else 
                "medium" if latency_ms < 5000 else "slow"
            ),
        }
        
        # 🔧 OPERATION ATTRIBUTES (Business Logic)
        operation_attrs = {
            "operation.type": operation,                   # Operation type
            "operation.name": f"{operation}_analysis",     # Detailed operation name
            "operation.timestamp": int(time.time()),       # Unix timestamp
            "operation.success": True,                     # Operation success status
            "operation.source": "secure_pr_guard",        # Service identifier
        }
        
        # 🤖 AI MODEL ATTRIBUTES (AI Governance)
        ai_attrs = {
            "ai.model": model,                            # AI model identifier
            "ai.provider": "openai",                      # AI provider
            "ai.operation": operation,                    # AI operation type
            "ai.tokens.input": prompt_tokens,             # AI input tokens
            "ai.tokens.output": completion_tokens,        # AI output tokens
            "ai.cost.per_request": round(cost, 6),        # Cost per AI request
        }
        
        # 📊 BUSINESS INTELLIGENCE ATTRIBUTES
        business_attrs = {
            **pr_metadata,                                # PR context (pr.url, pr.repository, etc.)
            "service.name": "secure_pr_guard",           # Service name
            "service.version": "v1.0-security",          # Service version
            "service.operation": f"secure_pr_guard.{operation}", # Namespaced operation
        }
        
        # 📈 EFFICIENCY & OPTIMIZATION ATTRIBUTES
        efficiency_attrs = {
            "efficiency.cost_per_token": round(cost / total_tokens, 6) if total_tokens > 0 else 0,
            "efficiency.tokens_per_ms": round(total_tokens / latency_ms, 3) if latency_ms > 0 else 0,
            "efficiency.cost_per_second": round((cost / latency_ms) * 1000, 6) if latency_ms > 0 else 0,
            "efficiency.score": round(                    # Composite efficiency score
                (total_tokens / (latency_ms / 1000)) / (cost + 0.001), 2
            ) if latency_ms > 0 else 0,
        }
        
        # 🏷️ CATEGORIZATION ATTRIBUTES (Filtering & Grouping)
        category_attrs = {
            "category.cost_tier": (                       # Cost categorization
                "low" if cost < 0.01 else 
                "medium" if cost < 0.10 else "high"
            ),
            "category.latency_tier": (                    # Latency categorization
                "fast" if latency_ms < 2000 else 
                "medium" if latency_ms < 5000 else "slow"
            ),
            "category.token_tier": (                      # Token usage categorization
                "small" if total_tokens < 500 else 
                "medium" if total_tokens < 2000 else "large"
            ),
        }
        
        # 🔭 SET ALL STANDARDIZED ATTRIBUTES AT ONCE (FIXED)
        all_standardized_attrs = {
            **cost_attrs,
            **tokens_attrs, 
            **latency_attrs,
            **operation_attrs,
            **ai_attrs,
            **business_attrs,
            **efficiency_attrs,
            **category_attrs
        }
        
        span.set_attributes(all_standardized_attrs)
        
        # 📝 ADD STRUCTURED EVENT
        span.add_event("cost_tracking.completed", {
            "cost.usd": cost,
            "tokens.total": total_tokens,
            "latency.ms": latency_ms,
            "operation.type": operation,
            "efficiency.score": efficiency_attrs.get("efficiency.score", 0)
        })
        
        # 🎯 SET SPAN STATUS WITH COST CONTEXT
        if cost > 0.50:  # High cost threshold
            span.set_status(Status(StatusCode.OK, f"High cost operation: ${cost:.4f}"))
        elif latency_ms > 10000:  # High latency threshold  
            span.set_status(Status(StatusCode.OK, f"Slow operation: {latency_ms}ms"))
        else:
            span.set_status(Status(StatusCode.OK, f"Normal: ${cost:.4f}, {latency_ms}ms"))
    
    # 📝 Ensure CSV exists and log to file
    initialize_cost_log()
    
    with COST_CSV.open("a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            int(time.time()),
            pr_url,
            operation,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            f"{cost:.6f}",
            latency_ms
        ])
    
    # 📊 Enhanced console output with efficiency metrics
    print(f"📊 Token Analysis: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
    
    if total_tokens > 0:
        prompt_ratio = (prompt_tokens / total_tokens * 100)
        tokens_per_sec = efficiency_metrics.get("efficiency.tokens_per_second", 0)
        cost_per_token = efficiency_metrics.get("efficiency.cost_per_token", 0)
        
        print(f"📊 Efficiency: {prompt_ratio:.1f}% prompt | {tokens_per_sec:.1f} tok/sec | ${cost_per_token:.6f}/tok")
    
    print(f"💰 {operation}: ${cost:.6f} | {total_tokens} tokens | {latency_ms}ms")
    
    # 🔭 Observability status
    if span and span.is_recording():
        span_context = span.get_span_context()
        trace_id = format(span_context.trace_id, '032x')[:8]  # Short trace ID for logs
        print(f"🔭 Telemetry: Span {trace_id} | {len(all_standardized_attrs)} attributes | Event logged")
    
    # 🛡️ BUDGET GUARD INTEGRATION - Real-time budget monitoring (FIXED)
    check_budget_integration_safe(pr_url, operation, cost, latency_ms, total_tokens)

    return cost

def log_cost_with_error(pr_url: str, operation: str, error: Exception, 
                       partial_tokens: int = 0, latency_ms: int = 0) -> float:
    """
    Enhanced error logging with comprehensive OTEL error tracking
    """
    # Record error in current span with enhanced attributes
    span = get_current_span()
    if span and span.is_recording():
        # Record the exception
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))
        
        # Enhanced error attributes
        error_attrs = {
            "operation.type": operation,
            "operation.failed": True,
            "error.type": type(error).__name__,
            "error.message": str(error),
            "error.operation": operation,
            "latency.ms": latency_ms,
            "tokens.partial": partial_tokens,
            **extract_pr_metadata(pr_url)
        }
        
        span.set_attributes(error_attrs)
        
        # Add error event
        span.add_event("operation_failed", {
            "error.type": type(error).__name__,
            "error.message": str(error)[:100],  # Truncate long messages
            "operation": operation,
            "latency.ms": latency_ms
        })
    
    # Still log partial cost if tokens were consumed
    if partial_tokens > 0:
        cost = log_cost(
            pr_url=pr_url,
            operation=f"{operation}_failed",
            model="gpt-4o-mini",  # Default assumption
            prompt_tokens=partial_tokens,
            completion_tokens=0,
            total_tokens=partial_tokens,
            latency_ms=latency_ms
        )
        return cost
    
    # Log zero-cost error entry
    initialize_cost_log()
    with COST_CSV.open("a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            int(time.time()),
            pr_url,
            f"{operation}_error",
            "unknown",
            0, 0, 0,
            "0.000000",
            latency_ms
        ])
    
    print(f"❌ {operation} failed: {error} | {latency_ms}ms | $0.000000")
    
    # 🛡️ Budget check for error cases (partial costs)
    if BUDGET_GUARD_ENABLED and partial_tokens > 0:
        try:
            # Check budget even for failed operations with partial costs
            partial_cost = partial_tokens * 0.00015  # Estimate using GPT-4o-mini price
            check_budget_integration_safe(
                pr_url=pr_url,
                operation=f"{operation}_error",
                cost=partial_cost,
                latency_ms=latency_ms,
                tokens=partial_tokens
            )
        except Exception as e:
            print(f"⚠️ Budget check failed for error case: {e}")
    
    return 0.0

def get_total_cost_for_pr(pr_url: str) -> Dict[str, Any]:
    """
    Calculate comprehensive cost and performance stats for a specific PR
    """
    if not COST_CSV.exists():
        return {
            "total_cost": 0, "total_tokens": 0, "operations": 0,
            "avg_latency_ms": 0, "efficiency_score": 0
        }
    
    total_cost = 0
    total_tokens = 0
    operations = 0
    total_latency = 0
    operations_by_type = {}
    models_used = set()
    
    with COST_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["pr_url"] == pr_url:
                cost = float(row["cost_usd"])
                tokens = int(row["total_tokens"])
                latency = int(row["latency_ms"])
                
                total_cost += cost
                total_tokens += tokens
                total_latency += latency
                operations += 1
                models_used.add(row["model"])
                
                # Track by operation type
                op_type = row["operation"]
                if op_type not in operations_by_type:
                    operations_by_type[op_type] = {
                        "count": 0, "cost": 0, "tokens": 0, "latency": 0
                    }
                operations_by_type[op_type]["count"] += 1
                operations_by_type[op_type]["cost"] += cost
                operations_by_type[op_type]["tokens"] += tokens
                operations_by_type[op_type]["latency"] += latency
    
    # Calculate summary metrics
    avg_latency = total_latency / operations if operations > 0 else 0
    avg_cost_per_op = total_cost / operations if operations > 0 else 0
    avg_tokens_per_op = total_tokens / operations if operations > 0 else 0
    
    # Calculate composite efficiency score
    efficiency_score = 0
    if total_latency > 0 and total_cost > 0:
        efficiency_score = round((total_tokens / (total_latency / 1000)) / total_cost, 2)
    
    # Update current span with PR summary
    span = get_current_span()
    if span and span.is_recording():
        summary_attrs = {
            "pr.total_cost_usd": round(total_cost, 6),
            "pr.total_tokens": total_tokens,
            "pr.total_operations": operations,
            "pr.avg_latency_ms": round(avg_latency, 0),
            "pr.avg_cost_per_operation": round(avg_cost_per_op, 6),
            "pr.avg_tokens_per_operation": round(avg_tokens_per_op, 0),
            "pr.efficiency_score": efficiency_score,
            "pr.models_used": list(models_used),
            "pr.operations_count": len(operations_by_type)
        }
        span.set_attributes(summary_attrs)
    
    return {
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "operations": operations,
        "avg_latency_ms": avg_latency,
        "avg_cost_per_operation": avg_cost_per_op,
        "avg_tokens_per_operation": avg_tokens_per_op,
        "efficiency_score": efficiency_score,
        "models_used": list(models_used),
        "operations_by_type": operations_by_type
    }

def generate_cost_summary() -> str:
    """Generate an enhanced cost summary report with efficiency insights"""
    if not COST_CSV.exists():
        return "No cost data available"
    
    total_cost = 0
    total_tokens = 0
    operations = 0
    total_latency = 0
    models_used = {}
    operations_by_type = {}
    
    with COST_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cost = float(row["cost_usd"])
            tokens = int(row["total_tokens"])
            latency = int(row["latency_ms"])
            model = row["model"]
            op_type = row["operation"]
            
            total_cost += cost
            total_tokens += tokens
            total_latency += latency
            operations += 1
            
            # Track models
            if model not in models_used:
                models_used[model] = {"cost": 0, "tokens": 0, "operations": 0}
            models_used[model]["cost"] += cost
            models_used[model]["tokens"] += tokens
            models_used[model]["operations"] += 1
            
            # Track operations
            if op_type not in operations_by_type:
                operations_by_type[op_type] = {
                    "count": 0, "cost": 0, "tokens": 0, "latency": 0
                }
            operations_by_type[op_type]["count"] += 1
            operations_by_type[op_type]["cost"] += cost
            operations_by_type[op_type]["tokens"] += tokens
            operations_by_type[op_type]["latency"] += latency
    
    # Calculate metrics
    avg_cost_per_operation = total_cost / operations if operations > 0 else 0
    avg_tokens_per_operation = total_tokens / operations if operations > 0 else 0
    avg_latency = total_latency / operations if operations > 0 else 0
    
    # Efficiency calculations
    tokens_per_second = (total_tokens / (total_latency / 1000)) if total_latency > 0 else 0
    cost_per_second = (total_cost / (total_latency / 1000)) if total_latency > 0 else 0
    
    summary = f"""
📊 Enhanced Cost Summary Report
================================
💰 Financial Metrics:
   Total Operations: {operations}
   Total Cost: ${total_cost:.4f}
   Average Cost/Operation: ${avg_cost_per_operation:.4f}
   
🔤 Token Metrics:
   Total Tokens: {total_tokens:,}
   Average Tokens/Operation: {avg_tokens_per_operation:.0f}
   
⚡ Performance Metrics:
   Average Latency: {avg_latency:.0f}ms
   Tokens/Second: {tokens_per_second:.1f}
   Cost/Second: ${cost_per_second:.6f}
"""
    
    return summary

def get_budget_status_summary() -> str:
    """
    Get a quick budget status summary for console output
    Integration function for main workflow
    """
    if not BUDGET_GUARD_ENABLED:
        return "🛡️ Budget monitoring: Disabled"
    
    try:
        guard = _get_budget_guard()
        if not guard:
            return "🛡️ Budget monitoring: Not available"
            
        status = guard.get_budget_status()
        
        if status["status"] != "active":
            return f"🛡️ Budget monitoring: {status.get('message', 'Unknown')}"
        
        hourly_pct = status['hourly_usage']['percentage']
        daily_pct = status['daily_usage']['percentage']
        alerts = status['recent_alerts']
        
        # Color coding for status
        if hourly_pct > 90 or daily_pct > 90:
            status_emoji = "🚨"
            level = "CRITICAL"
        elif hourly_pct > 70 or daily_pct > 70:
            status_emoji = "⚠️"
            level = "WARNING"
        else:
            status_emoji = "✅"
            level = "OK"
        
        return (f"{status_emoji} Budget: {level} | "
                f"Hourly: {hourly_pct:.1f}% | "
                f"Daily: {daily_pct:.1f}% | "
                f"Alerts: {alerts}")
                
    except Exception as e:
        return f"🛡️ Budget monitoring: Error ({e})"

# Test and validation functions
if __name__ == "__main__":
    print("🧪 Testing Enhanced Cost Logger with OTEL Integration")
    print("=" * 60)
    
    # Initialize cost logging
    initialize_cost_log()
    
    # Test normal cost logging
    print("\n📊 Testing normal cost logging...")
    test_cost = log_cost(
        pr_url="https://github.com/test/repo/pull/42",
        operation="test_nitpicker",
        model="gpt-4o-mini",
        prompt_tokens=150,
        completion_tokens=50,
        total_tokens=200,
        latency_ms=1200
    )
    
    print(f"✅ Test cost logged: ${test_cost:.6f}")
    
    # Test error logging
    print("\n❌ Testing error logging...")
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        error_cost = log_cost_with_error(
            pr_url="https://github.com/test/repo/pull/42",
            operation="test_error",
            error=e,
            partial_tokens=100,
            latency_ms=500
        )
    
    print(f"✅ Error cost logged: ${error_cost:.6f}")
    
    # Test PR summary
    print("\n📋 Testing PR cost summary...")
    summary = get_total_cost_for_pr("https://github.com/test/repo/pull/42")
    print(f"✅ PR Summary: {summary['operations']} ops, ${summary['total_cost']:.6f}, {summary['total_tokens']} tokens")
    
    # Generate full summary
    print("\n📊 Full cost summary:")
    print(generate_cost_summary())
    
    print("\n🎯 Enhanced cost logger test completed!")
    print("💡 Next: Run 'python graph_review.py <PR_URL>' to see enhanced telemetry in action")
