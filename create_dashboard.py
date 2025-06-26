#!/usr/bin/env python3
"""
Create Grafana Dashboard with simulated metrics for Secure-PR-Guard
"""

import json
import time
from datetime import datetime, timedelta

def create_dashboard_json():
    """Generate Grafana dashboard JSON with simulated data"""
    
    # Current time for timestamp
    now = datetime.now()
    
    dashboard = {
        "id": None,
        "title": "Secure-PR-Guard Observability",
        "tags": ["secure-pr-guard", "ai", "monitoring"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "AI Analysis Latency (avg, ms)",
                "type": "timeseries",
                "targets": [
                    {
                        "expr": "avg(spanmetrics_latency_seconds{service_name=\"secure-pr-guard\", span_name=\"nitpicker_analysis\"}) * 1000",
                        "legendFormat": "Nitpicker Analysis",
                        "refId": "A"
                    },
                    {
                        "expr": "avg(spanmetrics_latency_seconds{service_name=\"secure-pr-guard\", span_name=\"patch_generation\"}) * 1000",
                        "legendFormat": "Patch Generation", 
                        "refId": "B"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "min": 0
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Token Usage (total)",
                "type": "stat",
                "targets": [
                    {
                        "expr": "sum(spanmetrics_tokens_total{service_name=\"secure-pr-guard\"})",
                        "legendFormat": "Total Tokens",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1000},
                                {"color": "red", "value": 5000}
                            ]
                        }
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Cost Breakdown by Operation",
                "type": "barchart",
                "targets": [
                    {
                        "expr": "sum by (span_name) (spanmetrics_cost_usd_total{service_name=\"secure-pr-guard\"})",
                        "legendFormat": "{{span_name}}",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD"
                    }
                },
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
            }
        ],
        "time": {
            "from": "now-1h",
            "to": "now"
        },
        "refresh": "5s"
    }
    
    return dashboard

def create_sample_metrics():
    """Generate sample metrics data for testing"""
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "secure_pr_guard_latency_nitpicker_ms": 6844,
            "secure_pr_guard_latency_patch_ms": 7957,
            "secure_pr_guard_tokens_nitpicker": 873,
            "secure_pr_guard_tokens_patch": 1427,
            "secure_pr_guard_cost_nitpicker_usd": 0.130950,
            "secure_pr_guard_cost_patch_usd": 0.214050,
            "secure_pr_guard_total_cost_usd": 0.345,
            "secure_pr_guard_total_tokens": 2300,
            "secure_pr_guard_total_latency_ms": 14801
        },
        "summary": {
            "avg_cost_per_review": 0.31,
            "avg_latency_seconds": 14.8,
            "token_efficiency_prompt_pct": 70.3,
            "success_rate_pct": 95
        }
    }
    
    return metrics

def main():
    print("🎨 Creating Grafana Dashboard configuration...")
    
    # Generate dashboard JSON
    dashboard = create_dashboard_json()
    
    # Save dashboard JSON
    with open("docs/dashboard.json", "w") as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Dashboard JSON saved to: docs/dashboard.json")
    
    # Generate sample metrics
    metrics = create_sample_metrics()
    
    # Save sample metrics
    with open("docs/sample_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print("✅ Sample metrics saved to: docs/sample_metrics.json")
    
    print("\n📊 Dashboard Summary:")
    print("=" * 50)
    print(f"Title: {dashboard['title']}")
    print(f"Panels: {len(dashboard['panels'])}")
    print("1. AI Analysis Latency (Time Series)")
    print("2. Token Usage (Stat)")
    print("3. Cost Breakdown (Bar Chart)")
    
    print("\n🎯 Key Metrics:")
    print("=" * 50)
    summary = metrics['summary']
    print(f"• Average Cost: ${summary['avg_cost_per_review']}")
    print(f"• Average Latency: {summary['avg_latency_seconds']}s")
    print(f"• Token Efficiency: {summary['token_efficiency_prompt_pct']}%")
    print(f"• Success Rate: {summary['success_rate_pct']}%")
    
    print("\n📋 Next Steps:")
    print("=" * 50)
    print("1. Import docs/dashboard.json to Grafana Cloud")
    print("2. Configure data sources in Grafana")
    print("3. Take screenshot for documentation")
    print("4. Update README with dashboard link")

if __name__ == "__main__":
    main() 