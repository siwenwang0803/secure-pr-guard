#!/usr/bin/env python3
"""
Monthly Cost Report Generator
Generate cost analysis charts from logs/cost.csv using pandas + matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_cost_data():
    """Load cost data from CSV log"""
    csv_path = "logs/cost.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Cost log not found: {csv_path}")
        print("💡 Run some PR analyses first to generate cost data")
        return None
    
    # Load data
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['timestamp'].dt.date
    
    print(f"📊 Loaded {len(df)} cost records from {df['timestamp'].min()} to {df['timestamp'].max()}")
    return df

def generate_monthly_summary(df):
    """Generate monthly cost summary"""
    # Monthly aggregation
    monthly = df.groupby(df['timestamp'].dt.to_period('M')).agg({
        'cost_usd': ['sum', 'count', 'mean'],
        'total_tokens': 'sum',
        'latency_ms': 'mean'
    }).round(6)
    
    monthly.columns = ['total_cost', 'operations', 'avg_cost', 'total_tokens', 'avg_latency']
    
    print("\n📅 Monthly Summary:")
    print(monthly.to_string())
    
    return monthly

def create_cost_charts(df):
    """Create comprehensive cost analysis charts"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Secure PR Guard - Monthly Cost Analysis', fontsize=16, fontweight='bold')
    
    # 1. Daily cost trends
    daily_cost = df.groupby('date')['cost_usd'].sum()
    axes[0, 0].plot(daily_cost.index, daily_cost.values, marker='o', linewidth=2, markersize=4)
    axes[0, 0].set_title('Daily Cost Trends')
    axes[0, 0].set_ylabel('Cost (USD)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Format y-axis as currency
    axes[0, 0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))
    
    # 2. Cost by operation type
    op_cost = df.groupby('operation')['cost_usd'].sum().sort_values(ascending=False)
    colors = sns.color_palette("husl", len(op_cost))
    axes[0, 1].pie(op_cost.values, labels=op_cost.index, autopct='%1.1f%%', colors=colors)
    axes[0, 1].set_title('Cost Distribution by Operation')
    
    # 3. Token usage over time
    daily_tokens = df.groupby('date')['total_tokens'].sum()
    axes[1, 0].bar(daily_tokens.index, daily_tokens.values, alpha=0.7)
    axes[1, 0].set_title('Daily Token Usage')
    axes[1, 0].set_ylabel('Total Tokens')
    axes[1, 0].tick_params(axis='x', rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Cost efficiency (tokens per dollar)
    df['tokens_per_dollar'] = df['total_tokens'] / df['cost_usd']
    df_clean = df[df['tokens_per_dollar'].notna() & (df['tokens_per_dollar'] != float('inf'))]
    
    if len(df_clean) > 0:
        efficiency_by_op = df_clean.groupby('operation')['tokens_per_dollar'].mean().sort_values(ascending=False)
        axes[1, 1].bar(range(len(efficiency_by_op)), efficiency_by_op.values, alpha=0.7)
        axes[1, 1].set_title('Cost Efficiency by Operation')
        axes[1, 1].set_ylabel('Tokens per Dollar')
        axes[1, 1].set_xticks(range(len(efficiency_by_op)))
        axes[1, 1].set_xticklabels(efficiency_by_op.index, rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, 'No efficiency data available', 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Cost Efficiency by Operation')
    
    plt.tight_layout()
    
    # Save chart
    chart_path = f"docs/monthly-cost-report-{datetime.now().strftime('%Y-%m')}.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved: {chart_path}")
    
    return chart_path

def create_detailed_analysis(df):
    """Create detailed cost analysis"""
    print("\n" + "="*70)
    print("📈 DETAILED COST ANALYSIS")
    print("="*70)
    
    # Overall stats
    total_cost = df['cost_usd'].sum()
    total_operations = len(df)
    avg_cost_per_op = total_cost / total_operations if total_operations > 0 else 0
    total_tokens = df['total_tokens'].sum()
    avg_latency = df['latency_ms'].mean()
    
    print(f"💰 Total Cost: ${total_cost:.6f}")
    print(f"🔢 Total Operations: {total_operations}")
    print(f"📊 Average Cost/Operation: ${avg_cost_per_op:.6f}")
    print(f"🎯 Total Tokens: {total_tokens:,}")
    print(f"⚡ Average Latency: {avg_latency:.0f}ms")
    
    # Cost by model
    print(f"\n💻 Cost by Model:")
    model_cost = df.groupby('model')['cost_usd'].agg(['sum', 'count', 'mean']).round(6)
    model_cost.columns = ['Total Cost', 'Operations', 'Avg Cost']
    print(model_cost.to_string())
    
    # Cost by operation
    print(f"\n🔧 Cost by Operation Type:")
    op_analysis = df.groupby('operation').agg({
        'cost_usd': ['sum', 'count', 'mean'],
        'total_tokens': ['sum', 'mean'],
        'latency_ms': 'mean'
    }).round(6)
    op_analysis.columns = ['Total Cost', 'Count', 'Avg Cost', 'Total Tokens', 'Avg Tokens', 'Avg Latency']
    print(op_analysis.to_string())
    
    # Most expensive operations
    print(f"\n💸 Most Expensive Single Operations:")
    expensive = df.nlargest(5, 'cost_usd')[['timestamp', 'operation', 'cost_usd', 'total_tokens', 'pr_url']]
    print(expensive.to_string(index=False))
    
    # Recent trend (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent = df[df['timestamp'] >= week_ago]
    if len(recent) > 0:
        print(f"\n📅 Last 7 Days Trend:")
        print(f"   Operations: {len(recent)}")
        print(f"   Total Cost: ${recent['cost_usd'].sum():.6f}")
        print(f"   Daily Average: ${recent['cost_usd'].sum() / 7:.6f}")

def generate_readme_section():
    """Generate README observability section"""
    return """
## 📊 Observability & Cost Monitoring

### Real-time Metrics (Grafana Cloud)
Our system sends detailed telemetry to Grafana Cloud via OpenTelemetry:

- **Cost Tracking**: Real-time spend per operation (GPT-4o-mini/GPT-4o)
- **Performance Monitoring**: P95 latency, token efficiency  
- **Security Metrics**: Issues detected, patch success rate

### Key Dashboard Panels
1. **Average/P95 Latency by Operation** - SLO monitoring
2. **Total Cost by Model** - Budget tracking  
3. **Token Usage Split** - Prompt vs Completion efficiency

### TraceQL Queries
```traceql
# Cost analysis
{service.name="secure-pr-guard"} | select(cost.usd) | group_by(cost.model)

# Performance monitoring  
{service.name="secure-pr-guard"} | select(latency.ms) | group_by(operation.type)

# Token efficiency
{service.name="secure-pr-guard"} | select(cost.tokens.prompt, cost.tokens.completion)
```

### Local Cost Reports
Generate monthly cost reports with detailed analytics:
```bash
python monthly_cost_report.py
```

Includes trend analysis, efficiency metrics, and cost breakdowns by operation/model.
"""

def main():
    """Generate monthly cost report"""
    print("📊 Generating Monthly Cost Report for Secure PR Guard")
    print("=" * 60)
    
    # Load data
    df = load_cost_data()
    if df is None:
        return
    
    # Generate monthly summary
    monthly_summary = generate_monthly_summary(df)
    
    # Create charts
    chart_path = create_cost_charts(df)
    
    # Detailed analysis
    create_detailed_analysis(df)
    
    # Generate README section
    readme_section = generate_readme_section()
    
    # Save README section
    with open("docs/observability-readme-section.md", "w") as f:
        f.write(readme_section)
    
    print(f"\n✅ Monthly report completed!")
    print(f"📊 Chart: {chart_path}")
    print(f"📝 README section: docs/observability-readme-section.md")
    print(f"\n💡 Add the chart to your README for visual cost tracking!")

if __name__ == "__main__":
    main() 