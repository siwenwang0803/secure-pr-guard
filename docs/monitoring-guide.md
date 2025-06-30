# 🚀 Secure PR Guard - Monitoring System Documentation

## Table of Contents
- [Quick Start Guide](#quick-start-guide)
- [Dashboard Overview](#dashboard-overview)
- [Chart Explanations](#chart-explanations)
- [Alert Configuration](#alert-configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Best Practices](#best-practices)
- [API Integration](#api-integration)

---

## 🎯 Quick Start Guide

### Prerequisites
- Python 3.8+ with virtual environment
- Required packages: `pandas`, `plotly`, `numpy`
- Active cost data in `logs/cost.csv`

### 5-Minute Setup

```bash
# 1. Activate your environment
source .venv/bin/activate

# 2. Install dependencies (if not already installed)
pip install pandas plotly numpy

# 3. Launch monitoring dashboard
python monitoring/monitor.py

# 4. Select time range when prompted
# Choose: 24h (default) or 7d

# 5. Dashboard opens automatically in your browser
```

### First Time User Checklist
- ✅ Verify `logs/cost.csv` exists and contains data
- ✅ Check that timestamps are recent (< 24 hours)
- ✅ Confirm all required columns are present
- ✅ Review dashboard for any data quality warnings

---

## 📊 Dashboard Overview

### Layout Structure (3x3 Grid)

```
┌─────────────────┬─────────────────┬─────────────────┐
│  💰 Cost        │  🎯 Token       │  ⚡ Latency     │
│     Trends      │     Usage       │  Distribution   │
├─────────────────┼─────────────────┼─────────────────┤
│  📊 SLA         │  🔥 Cost        │  🚨 System      │
│  Performance    │  Heatmap        │     Health      │
├─────────────────┼─────────────────┼─────────────────┤
│  📈 Percentiles │  🎛️ Live        │  📋 Summary     │
│                 │  Latency        │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

### Key Metrics Tracked
- **💰 Cost Metrics**: Per-operation costs, total spend, efficiency
- **⚡ Performance**: Latency percentiles (P50, P95, P99), SLA compliance
- **🎯 Usage**: Token consumption, operation frequency
- **🚨 Health**: Data quality, system alerts, uptime

### Color Coding Standard
- 🟢 **Green**: Normal operation, within SLA
- 🟡 **Yellow/Orange**: Warning thresholds, attention needed
- 🔴 **Red**: Critical issues, immediate action required
- 🔵 **Blue**: Informational metrics, neutral data

---

## 📈 Chart Explanations

### 1. 💰 Cost Trends
**Purpose**: Track real-time cost patterns and identify spending anomalies

**What to Look For**:
- **Sudden Spikes**: May indicate expensive operations or errors
- **Gradual Increases**: Could signal growing usage or inefficiency
- **Cost per Token**: Efficiency metric - lower is better

**Action Items**:
- If cost > $0.10 per operation → Investigate expensive calls
- If efficiency > $0.20/1K tokens → Review model selection
- Daily costs trending up → Consider optimization

### 2. 🎯 Token Usage
**Purpose**: Understand token consumption patterns across prompt vs completion

**What to Look For**:
- **High Prompt/Completion Ratio**: May indicate inefficient prompting
- **Token Spikes**: Correlate with latency and cost increases
- **Usage Patterns**: Identify peak usage times

**Optimization Tips**:
- Optimize prompts to reduce prompt tokens
- Use streaming for large completions
- Cache common responses

### 3. ⚡ Latency Distribution
**Purpose**: Analyze response time patterns and identify performance bottlenecks

**SLA Thresholds**:
- **Fast**: < 1 second (Excellent)
- **Normal**: 1-5 seconds (Acceptable)
- **Slow**: 5-10 seconds (Review needed)
- **Critical**: > 10 seconds (Action required)

**Common Causes of High Latency**:
- Large token requests
- Network connectivity issues
- API rate limiting
- Model selection (GPT-4 vs GPT-3.5)

### 4. 📊 SLA Performance
**Purpose**: Monitor service level agreement compliance

**Interpretation**:
- **Fast Operations** should be > 60% for good UX
- **Critical Operations** should be < 5% for reliability
- Use for capacity planning and SLA reporting

### 5. 🔥 Cost Heatmap
**Purpose**: Identify peak usage hours and cost concentration

**Usage**:
- **Dark Areas**: High cost periods - plan capacity
- **Light Areas**: Low usage - potential optimization windows
- **Patterns**: Regular vs irregular usage detection

### 6. 🚨 System Health
**Purpose**: Monitor data quality and system alerts

**Status Types**:
- **OK**: All systems functioning normally
- **WARN**: Minor issues, monitoring recommended
- **ERROR**: Active problems requiring attention

### 7. 📈 Percentiles Chart
**Purpose**: Detailed latency analysis for SRE teams

**Key Metrics**:
- **P50 (Median)**: Typical user experience
- **P95**: 95% of users experience this or better
- **P99**: Tail latency - critical for SLA compliance
- **Max**: Worst-case scenario

### 8. 🎛️ Live Latency Gauge
**Purpose**: Real-time performance monitoring

**Gauge Zones**:
- **Green Zone**: 0-1000ms (Excellent)
- **Yellow Zone**: 1000-5000ms (Good)
- **Orange Zone**: 5000-8000ms (Warning)
- **Red Zone**: > 8000ms (Critical)

### 9. 📋 Summary Table
**Purpose**: Executive overview of key metrics

**Includes**:
- Total operational costs
- Average performance metrics
- Data freshness indicators
- System health summary

---

## 🚨 Alert Configuration

### Built-in Alert Thresholds

```json
{
  "sla_thresholds": {
    "fast": 1000,        // < 1s response time
    "normal": 5000,      // < 5s acceptable
    "slow": 10000,       // < 10s needs review
    "critical": 15000    // > 15s requires action
  },
  "alert_thresholds": {
    "latency_p95": 8000, // P95 latency warning
    "latency_p99": 12000 // P99 latency critical
  }
}
```

### Customizing Alerts

1. **Edit Configuration File**:
```bash
# Create custom config
cat > monitoring/dashboard_config.json << 'EOF'
{
  "sla_thresholds": {
    "fast": 500,         // Stricter requirement
    "normal": 3000,      // Tighter SLA
    "critical": 8000     // Lower tolerance
  },
  "refresh_interval": 15 // More frequent updates
}
EOF
```

2. **Restart Dashboard** to apply changes

### Alert Response Procedures

#### High Latency Alert (P95 > 8s)
1. **Immediate**: Check current operations
2. **Investigate**: Review recent deployments
3. **Escalate**: If sustained > 10 minutes
4. **Document**: Log incident and resolution

#### Cost Spike Alert (> $0.10)
1. **Stop**: Halt expensive operations if possible
2. **Identify**: Find root cause operation
3. **Optimize**: Reduce token usage or switch models
4. **Monitor**: Watch for recurrence

#### Data Quality Issues
1. **Verify**: Check CSV file integrity
2. **Refresh**: Restart data collection
3. **Backup**: Switch to alternative data source
4. **Alert**: Notify operations team

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Dashboard Won't Load
```bash
# Check data file
ls -la logs/cost.csv

# Verify file permissions
chmod 644 logs/cost.csv

# Check recent data
tail -5 logs/cost.csv
```

#### No Data Showing
**Possible Causes**:
- Empty CSV file
- Timestamp format issues
- Time range too narrow

**Solutions**:
```bash
# Check data format
head -1 logs/cost.csv
# Should show: timestamp,pr_url,operation,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms

# Verify recent timestamps
python -c "
import pandas as pd
df = pd.read_csv('logs/cost.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
print('Latest data:', df['timestamp'].max())
print('Data count:', len(df))
"
```

#### Charts Display Incorrectly
**Font/Layout Issues**:
- Update Plotly: `pip install --upgrade plotly`
- Clear browser cache
- Try different browser

**Data Issues**:
- Check for null values in critical columns
- Verify numeric columns contain valid numbers
- Ensure timestamp column is properly formatted

#### Performance Issues
**Dashboard Loads Slowly**:
- Reduce time range (use 24h instead of 7d)
- Limit data points (sample large datasets)
- Close other browser tabs

### Debug Mode

Enable detailed logging:
```python
# Add to monitor script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Data Validation Script

```bash
# Create validation script
cat > monitoring/validate_data.py << 'EOF'
import pandas as pd
import sys

def validate_cost_data(csv_path='logs/cost.csv'):
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ File loaded: {len(df)} records")
        
        # Check required columns
        required = ['timestamp', 'cost_usd', 'latency_ms', 'operation']
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
            
        # Check data types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['cost_usd'] = pd.to_numeric(df['cost_usd'])
        df['latency_ms'] = pd.to_numeric(df['latency_ms'])
        
        print(f"✅ Data types valid")
        print(f"📊 Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"💰 Cost range: ${df['cost_usd'].min():.6f} to ${df['cost_usd'].max():.6f}")
        print(f"⚡ Latency range: {df['latency_ms'].min():.0f}ms to {df['latency_ms'].max():.0f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_cost_data()
EOF

# Run validation
python monitoring/validate_data.py
```

---

## ⚙️ Advanced Configuration

### Time Range Customization

```python
# Custom time ranges in dashboard
time_ranges = {
    "1h": 1,
    "6h": 6, 
    "24h": 24,
    "7d": 168,
    "30d": 720
}
```

### Custom Metrics

Add custom metrics to dashboard:

```python
# In dashboard code, add custom calculation
def add_custom_metric(self, fig, row, col):
    # Calculate custom efficiency metric
    self.df['custom_efficiency'] = (
        self.df['cost_usd'] / self.df['latency_ms'] * 1000
    )
    
    fig.add_trace(
        go.Scatter(
            x=self.df['timestamp'],
            y=self.df['custom_efficiency'],
            name='Cost Efficiency'
        ),
        row=row, col=col
    )
```

### Export Options

```python
# Automated reporting
def export_dashboard(self, format='png'):
    fig = self.create_dashboard()
    
    if format == 'png':
        fig.write_image('reports/dashboard.png', width=1920, height=1080)
    elif format == 'pdf':
        fig.write_image('reports/dashboard.pdf')
    elif format == 'html':
        fig.write_html('reports/dashboard.html')
```

### Integration with External Systems

#### Slack Notifications
```python
import requests

def send_slack_alert(message, webhook_url):
    payload = {"text": f"🚨 PR Guard Alert: {message}"}
    requests.post(webhook_url, json=payload)
```

#### Grafana Integration
```python
# Export metrics for Grafana
def export_prometheus_metrics():
    metrics = []
    metrics.append(f"pr_guard_cost_total {self.df['cost_usd'].sum()}")
    metrics.append(f"pr_guard_latency_p95 {self.df['latency_ms'].quantile(0.95)}")
    
    with open('/tmp/pr_guard_metrics.prom', 'w') as f:
        f.write('\n'.join(metrics))
```

---

## 📋 Best Practices

### For Development Teams

#### Daily Monitoring
- **Morning**: Check overnight costs and performance
- **During Development**: Monitor after deployments
- **End of Day**: Review daily summaries

#### Cost Optimization
1. **Model Selection**: Use GPT-3.5 for simpler tasks
2. **Prompt Engineering**: Optimize for conciseness
3. **Caching**: Cache frequent responses
4. **Rate Limiting**: Implement request throttling

#### Performance Monitoring
1. **Set Baselines**: Establish normal performance ranges
2. **Alert Thresholds**: Configure based on SLA requirements
3. **Trending**: Watch for gradual degradation
4. **Capacity Planning**: Use historical data for scaling

### For Operations Teams

#### Incident Response
1. **Triage**: Use dashboard to identify scope
2. **Communicate**: Share dashboard links with stakeholders
3. **Document**: Export charts for post-mortems
4. **Learn**: Update thresholds based on incidents

#### Capacity Planning
- Monitor growth trends in token usage
- Plan for peak usage periods
- Scale infrastructure proactively
- Budget based on usage projections

### For Management Teams

#### Executive Reporting
- Use Summary table for high-level metrics
- Focus on cost trends and SLA compliance
- Monthly/quarterly trend analysis
- ROI calculations for AI investments

#### Budget Management
- Set cost alerts based on budget constraints
- Monitor efficiency metrics for optimization opportunities
- Track spending per feature/team/project
- Plan for scaling costs

---

## 🔌 API Integration

### Webhook Integration

```python
# Add webhook support for real-time alerts
class WebhookAlerts:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert_type, message, severity="INFO"):
        payload = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "dashboard_url": "http://localhost:8080/dashboard"
        }
        
        requests.post(self.webhook_url, json=payload)
```

### REST API for Dashboard Data

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/metrics')
def get_metrics():
    monitor = FixedEnterpriseDashboard()
    monitor.load_data()
    
    return jsonify({
        "total_cost": float(monitor.df['cost_usd'].sum()),
        "avg_latency": float(monitor.df['latency_ms'].mean()),
        "record_count": len(monitor.df),
        "last_update": monitor.last_update.isoformat()
    })

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
```

### Automated Reporting

```python
import schedule
import time

def daily_report():
    monitor = FixedEnterpriseDashboard()
    dashboard = monitor.create_dashboard(24)
    
    # Export report
    dashboard.write_image('reports/daily_report.png')
    
    # Send to stakeholders
    send_email_report('reports/daily_report.png')

# Schedule daily reports
schedule.every().day.at("08:00").do(daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🎓 Training Materials

### New User Onboarding

1. **Overview Session** (30 min):
   - Dashboard layout and navigation
   - Key metrics explanation
   - Basic troubleshooting

2. **Hands-on Workshop** (60 min):
   - Set up monitoring environment
   - Customize alert thresholds
   - Practice incident response

3. **Advanced Training** (90 min):
   - Custom metrics creation
   - Integration with existing tools
   - Performance optimization techniques

### Quick Reference Cards

#### Alert Response Checklist
```
🚨 HIGH LATENCY ALERT
□ Check dashboard immediately
□ Identify affected operations
□ Review recent changes
□ Escalate if > 10 min sustained
□ Document resolution

💰 COST SPIKE ALERT  
□ Stop expensive operations
□ Identify root cause
□ Optimize model/prompts
□ Monitor for recurrence
□ Update budgets if needed
```

#### Dashboard Keyboard Shortcuts
- `Ctrl + R`: Refresh browser
- `F11`: Full screen mode
- `Ctrl + F`: Search in dashboard
- `Ctrl + S`: Save page/export

---

## 📞 Support and Resources

### Getting Help

1. **Documentation**: This guide covers 90% of use cases
2. **Troubleshooting**: Check common issues section first
3. **Community**: Internal Slack channel #pr-guard-monitoring
4. **Escalation**: Contact DevOps team for infrastructure issues

### Additional Resources

- **Plotly Documentation**: https://plotly.com/python/
- **Pandas Guide**: https://pandas.pydata.org/docs/
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **Cost Optimization Guide**: Internal wiki/confluence

### Changelog

- **v2.1**: Added enterprise dashboard with P95/P99 monitoring
- **v2.0**: Introduced real-time monitoring and alerts
- **v1.5**: Added cost heatmap and efficiency tracking
- **v1.0**: Initial dashboard with basic cost and performance metrics

---

**📊 Happy Monitoring! For questions or improvements to this documentation, contact the DevOps team.**