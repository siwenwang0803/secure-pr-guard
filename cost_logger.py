"""
Cost Logger: Token usage and cost tracking for AI operations
Provides detailed monitoring for OpenAI API usage and costs
"""

import os
import csv
import time
import pathlib
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cost tracking file
COST_CSV = pathlib.Path("logs/cost.csv")

# Model pricing (USD per token)
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

def log_cost(pr_url: str, operation: str, model: str, 
             prompt_tokens: int, completion_tokens: int, 
             total_tokens: int, latency_ms: int) -> float:
    """
    Log API usage and cost to CSV
    
    Args:
        pr_url: GitHub PR URL being processed
        operation: Type of operation (e.g., 'nitpicker', 'patch_generation')
        model: OpenAI model used
        prompt_tokens: Input tokens used
        completion_tokens: Output tokens generated
        total_tokens: Total tokens used
        latency_ms: API call latency in milliseconds
        
    Returns:
        float: Cost in USD
    """
    # Calculate cost
    price_per_token = MODEL_PRICE.get(model, 0.001)  # Default fallback
    cost = total_tokens * price_per_token
    
    # Ensure CSV exists
    initialize_cost_log()
    
    # Log to CSV
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
    
    # 额外记录详细分析数据
    print(f"📊 Token Analysis: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
    prompt_ratio = (prompt_tokens / total_tokens * 100) if total_tokens > 0 else 0
    print(f"📊 Prompt Efficiency: {prompt_ratio:.1f}% prompt tokens")
    
    print(f"💰 {operation}: ${cost:.5f} | {total_tokens} tokens | {latency_ms}ms")
    return cost

def get_total_cost_for_pr(pr_url: str) -> Dict[str, Any]:
    """
    Calculate total cost and stats for a specific PR
    
    Args:
        pr_url: GitHub PR URL
        
    Returns:
        Dict with cost summary
    """
    if not COST_CSV.exists():
        return {"total_cost": 0, "total_tokens": 0, "operations": 0}
    
    total_cost = 0
    total_tokens = 0
    operations = 0
    total_latency = 0
    
    with COST_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["pr_url"] == pr_url:
                total_cost += float(row["cost_usd"])
                total_tokens += int(row["total_tokens"])
                total_latency += int(row["latency_ms"])
                operations += 1
    
    avg_latency = total_latency / operations if operations > 0 else 0
    
    return {
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "operations": operations,
        "avg_latency_ms": avg_latency
    }

def generate_cost_summary() -> str:
    """
    Generate a summary report of all costs
    
    Returns:
        str: Formatted cost summary
    """
    if not COST_CSV.exists():
        return "No cost data available"
    
    total_cost = 0
    total_tokens = 0
    operations = 0
    models_used = set()
    
    with COST_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_cost += float(row["cost_usd"])
            total_tokens += int(row["total_tokens"])
            operations += 1
            models_used.add(row["model"])
    
    avg_cost_per_operation = total_cost / operations if operations > 0 else 0
    avg_tokens_per_operation = total_tokens / operations if operations > 0 else 0
    
    summary = f"""
📊 Cost Summary Report
======================
Total Operations: {operations}
Total Tokens: {total_tokens:,}
Total Cost: ${total_cost:.4f}
Average Cost/Operation: ${avg_cost_per_operation:.4f}
Average Tokens/Operation: {avg_tokens_per_operation:.0f}
Models Used: {', '.join(models_used)}
"""
    return summary

def track_operation_cost(pr_url: str, operation: str):
    """
    Decorator to track cost and latency of OpenAI operations
    
    Usage:
        @track_operation_cost("https://github.com/user/repo/pull/1", "nitpicker")
        def my_ai_function():
            # ... OpenAI API call
            return response
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
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
        return wrapper
    return decorator

# Test functions
if __name__ == "__main__":
    # Test cost logging
    initialize_cost_log()
    
    # Simulate some API calls
    test_cost = log_cost(
        pr_url="https://github.com/test/repo/pull/1",
        operation="test_nitpicker",
        model="gpt-4o-mini",
        prompt_tokens=150,
        completion_tokens=50,
        total_tokens=200,
        latency_ms=1200
    )
    
    print(f"Test cost logged: ${test_cost:.5f}")
    
    # Generate summary
    print(generate_cost_summary())