"""
Cost Logger with Enhanced OpenTelemetry Integration
Tracks API usage costs and exports telemetry data via OTLP/HTTP with Grafana-optimized attributes
"""

import os
import csv
import time
import pathlib
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import get_current_span, Status, StatusCode
from monitoring.budget_guard import check_budget_integration
# Load environment variables
load_dotenv()
# Add this import at the top of cost_logger.py
try:
    from monitoring.budget_guard import check_budget_integration
    BUDGET_GUARD_ENABLED = True
    print("🛡️ Budget Guard integration enabled")
except ImportError:
    BUDGET_GUARD_ENABLED = False
    print("⚠️ Budget Guard not available - install dependencies")

# Add this call at the end of the log_cost function, just before returning cost:
    
    # 🛡️ BUDGET GUARD INTEGRATION - Real-time budget monitoring
    if BUDGET_GUARD_ENABLED:
        try:
            check_budget_integration(
                pr_url=pr_url,
                operation=operation,
                cost=cost,
                latency_ms=latency_ms,
                tokens=total_tokens
            )
        except Exception as e:
            print(f"⚠️ Budget check failed: {e}")
            # Don't fail the main operation due to budget check errors
try:
    from monitoring.budget_guard import check_budget_integration
    BUDGET_GUARD_ENABLED = True
    print("🛡️ Budget Guard integration enabled - Real-time monitoring active")
except ImportError as e:
    BUDGET_GUARD_ENABLED = False
    print(f"⚠️ Budget Guard not available: {e}")
    print("💡 Install: pip install PyYAML requests click")    
   
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

# 在 cost_logger.py 的 log_cost 函数中，标准化所有 OTEL 属性

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
    
    # 🔭 STANDARDIZED OpenTelemetry attributes
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
        
        # 🔭 SET ALL STANDARDIZED ATTRIBUTES AT ONCE
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
            "efficiency.score": efficiency_attrs["efficiency.score"]
        })
        
        # 🎯 SET SPAN STATUS WITH COST CONTEXT
        if cost > 0.50:  # High cost threshold
            span.set_status(Status(StatusCode.OK, f"High cost operation: ${cost:.4f}"))
        elif latency_ms > 10000:  # High latency threshold  
            span.set_status(Status(StatusCode.OK, f"Slow operation: {latency_ms}ms"))
        else:
            span.set_status(Status(StatusCode.OK, f"Normal: ${cost:.4f}, {latency_ms}ms"))

    
    # Calculate efficiency metrics
    efficiency_metrics = calculate_efficiency_metrics(
        prompt_tokens, completion_tokens, total_tokens, latency_ms, cost
    )
    
    # 🔭 Enhanced OpenTelemetry span attributes
    span = get_current_span()
    if span and span.is_recording():
        # Core operation attributes
        operation_attrs = {
            "operation.type": operation,
            "operation.name": f"{operation}_analysis",
            "operation.timestamp": int(time.time()),
            "service.operation": f"secure_pr_guard.{operation}",
        }
        
        # 💰 Cost governance attributes (KEY for executive dashboards)
        cost_attrs = {
            "cost.usd": round(cost, 6),
            "cost.model": model,
            "cost.model.pricing": price_per_token,
            "cost.tokens.prompt": prompt_tokens,
            "cost.tokens.completion": completion_tokens,
            "cost.tokens.total": total_tokens,
            "cost.operation": operation,  # For cost breakdown by operation type
        }
        
        # ⚡ Performance & SLO attributes  
        performance_attrs = {
            "latency.ms": latency_ms,
            "latency.seconds": round(latency_ms / 1000, 3),
            "latency.api_ms": latency_ms,  # Assuming most latency is API
            "performance.tokens_per_second": efficiency_metrics.get("efficiency.tokens_per_second", 0),
        }
        
        # 📊 Business intelligence attributes
        business_attrs = {
            **pr_metadata,
            "ai.model": model,
            "ai.provider": "openai",
            "ai.tokens.input": prompt_tokens,
            "ai.tokens.output": completion_tokens,
            "ai.tokens.total": total_tokens,
        }
        
        # 🎯 Efficiency & optimization attributes
        efficiency_attrs = efficiency_metrics
        
        # Combine all attributes
        all_attributes = {
            **operation_attrs,
            **cost_attrs, 
            **performance_attrs,
            **business_attrs,
            **efficiency_attrs
        }
        
        # Set all attributes at once
        span.set_attributes(all_attributes)
        
        # Add operation-specific event for detailed tracing
        span.add_event("cost_tracked", {
            "cost.usd": cost,
            "tokens.total": total_tokens,
            "latency.ms": latency_ms,
            "operation": operation
        })
        
        # Set span status based on cost thresholds
        if cost > 0.01:  # High cost threshold
            span.set_status(Status(StatusCode.OK, f"High cost operation: ${cost:.4f}"))
        else:
            span.set_status(Status(StatusCode.OK, f"Normal cost: ${cost:.6f}"))
    
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
        print(f"🔭 Telemetry: Span {trace_id} | {len(all_attributes)} attributes | Event logged")
    
    check_budget_integration(pr_url, operation, cost, latency_ms, total_tokens)
    return cost

def log_cost_with_error(pr_url: str, operation: str, error: Exception, 
                       partial_tokens: int = 0, latency_ms: int = 0) -> float:
    """
    Enhanced error logging with comprehensive OTEL error tracking
    
    Args:
        pr_url: GitHub PR URL being processed
        operation: Type of operation that failed
        error: Exception that occurred
        partial_tokens: Any tokens consumed before failure
        latency_ms: Time elapsed before failure
        
    Returns:
        float: Partial cost if any
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

      # 🛡️ BUDGET GUARD INTEGRATION - Real-time budget monitoring
    if BUDGET_GUARD_ENABLED:
        try:
            # Perform real-time budget check after cost logging
            check_budget_integration(
                pr_url=pr_url,
                operation=operation,
                cost=cost,
                latency_ms=latency_ms,
                tokens=total_tokens
            )
            
            # Add budget status to OpenTelemetry span
            span = get_current_span()
            if span and span.is_recording():
                span.set_attributes({
                    "budget.monitoring.enabled": True,
                    "budget.integration.status": "active",
                    "budget.check.completed": True
                })
                
        except Exception as e:
            print(f"⚠️ Budget monitoring failed: {e}")
            
            # Record budget check failure in telemetry
            span = get_current_span()
            if span and span.is_recording():
                span.set_attributes({
                    "budget.monitoring.enabled": False,
                    "budget.integration.error": str(e),
                    "budget.check.completed": False
                })
                span.add_event("budget_check_failed", {
                    "error": str(e),
                    "operation": operation
                })
            
            # Don't fail the main operation due to budget check errors
            pass
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
            check_budget_integration(
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
    Enhanced with efficiency metrics for dashboards
    
    Args:
        pr_url: GitHub PR URL
        
    Returns:
        Dict with enhanced cost and performance summary
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
    """
    Generate an enhanced cost summary report with efficiency insights
    
    Returns:
        str: Formatted cost summary with optimization recommendations
    """
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

🤖 Model Breakdown:"""
    
    for model, stats in models_used.items():
        avg_cost = stats["cost"] / stats["operations"] if stats["operations"] > 0 else 0
        avg_tokens = stats["tokens"] / stats["operations"] if stats["operations"] > 0 else 0
        efficiency = stats["tokens"] / stats["cost"] if stats["cost"] > 0 else 0
        
        summary += f"""
   {model}:
     Operations: {stats["operations"]}
     Total Cost: ${stats["cost"]:.4f}
     Avg Cost: ${avg_cost:.4f}
     Avg Tokens: {avg_tokens:.0f}
     Efficiency: {efficiency:.0f} tokens/$
"""

    summary += f"""
📈 Operation Type Breakdown:"""
    
    for op_type, stats in operations_by_type.items():
        avg_cost = stats["cost"] / stats["count"] if stats["count"] > 0 else 0
        avg_tokens = stats["tokens"] / stats["count"] if stats["count"] > 0 else 0
        avg_latency = stats["latency"] / stats["count"] if stats["count"] > 0 else 0
        
        summary += f"""
   {op_type}:
     Count: {stats["count"]}
     Total Cost: ${stats["cost"]:.4f}
     Avg Cost: ${avg_cost:.4f}
     Avg Tokens: {avg_tokens:.0f}
     Avg Latency: {avg_latency:.0f}ms
"""
    
    # Add optimization recommendations
    if operations > 10:  # Only show recommendations with sufficient data
        highest_cost_op = max(operations_by_type.items(), 
                             key=lambda x: x[1]["cost"])[0]
        slowest_op = max(operations_by_type.items(), 
                        key=lambda x: x[1]["latency"] / x[1]["count"])[0]
        
        summary += f"""
💡 Optimization Recommendations:
   - Highest cost operation: {highest_cost_op}
   - Slowest operation: {slowest_op}
   - Consider optimizing prompts for {highest_cost_op}
   - Monitor latency for {slowest_op}
"""
    
    return summary

# Enhanced decorator for automatic cost tracking
def track_operation_cost(pr_url: str, operation: str):
    """
    Enhanced decorator to track cost and latency of OpenAI operations with full OTEL
    
    Usage:
        @track_operation_cost("https://github.com/user/repo/pull/1", "nitpicker")
        def my_ai_function():
            # ... OpenAI API call
            return response
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Create a new span for this operation with enhanced attributes
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(f"cost_tracking.{operation}") as span:
                # Set initial attributes
                span.set_attributes({
                    "operation.type": operation,
                    "operation.name": f"tracked_{operation}",
                    "operation.start_time": start_time,
                    **extract_pr_metadata(pr_url)
                })
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Extract usage info if available
                    if hasattr(result, 'usage') and result.usage:
                        usage = result.usage
                        log_cost(
                            pr_url=pr_url,
                            operation=operation,
                            model=kwargs.get('model', 'gpt-4o-mini'),
                            prompt_tokens=usage.prompt_tokens,
                            completion_tokens=usage.completion_tokens,
                            total_tokens=usage.total_tokens,
                            latency_ms=latency_ms
                        )
                    
                    return result
                    
                except Exception as e:
                    # Log error case with enhanced tracking
                    latency_ms = int((time.time() - start_time) * 1000)
                    log_cost_with_error(pr_url, operation, e, latency_ms=latency_ms)
                    raise
                    
        return wrapper
    return decorator

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


def get_budget_status_summary() -> str:
    """
    Get a quick budget status summary for console output
    Integration function for main workflow
    """
    if not BUDGET_GUARD_ENABLED:
        return "🛡️ Budget monitoring: Disabled"
    
    try:
        from monitoring.budget_guard import BudgetGuard
        guard = BudgetGuard()
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
