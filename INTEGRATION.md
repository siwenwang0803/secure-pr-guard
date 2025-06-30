# 🛡️ Budget Guard Manual Integration Guide

This guide shows how to manually integrate Budget Guard into your existing Secure PR Guard system.

## 📋 Prerequisites

```bash
# Install budget dependencies
pip install PyYAML requests click
```

## 🔧 Integration Steps

### 1. Update `monitoring/cost_logger.py`

Add these changes to enable real-time budget monitoring:

#### A. Add Import (after existing imports)
```python
# Budget Guard Integration
try:
    from monitoring.budget_guard import check_budget_integration
    BUDGET_GUARD_ENABLED = True
    print("🛡️ Budget Guard integration enabled - Real-time monitoring active")
except ImportError as e:
    BUDGET_GUARD_ENABLED = False
    print(f"⚠️ Budget Guard not available: {e}")
    print("💡 Install: pip install PyYAML requests click")
```

#### B. Update `log_cost()` Function
Add this code **just before** `return cost`:

```python
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
```

#### C. Add Budget Status Function
Add this function **before** the `if __name__ == "__main__":` section:

```python
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
```

### 2. Update `graph_review.py` (Main Workflow)

Add budget monitoring to your main workflow:

#### A. Add Imports (after existing imports)
```python
# Budget monitoring integration
try:
    from monitoring.budget_guard import BudgetGuard
    from monitoring.cost_logger import get_budget_status_summary
    BUDGET_MONITORING_ENABLED = True
except ImportError:
    BUDGET_MONITORING_ENABLED = False
```

#### B. Add Budget Functions
```python
def initialize_budget_monitoring() -> Optional[BudgetGuard]:
    """Initialize budget monitoring for the workflow"""
    if not BUDGET_MONITORING_ENABLED:
        print("⚠️ Budget monitoring disabled - install dependencies")
        return None
    
    try:
        guard = BudgetGuard()
        print("🛡️ Budget monitoring initialized")
        
        # Show initial budget status
        status = get_budget_status_summary()
        print(f"📊 Initial budget status: {status}")
        
        return guard
        
    except Exception as e:
        print(f"❌ Budget monitoring initialization failed: {e}")
        return None

def check_budget_before_operation(guard: Optional[BudgetGuard], 
                                 operation: str, pr_url: str) -> bool:
    """Check budget status before expensive operations"""
    if not guard:
        return True  # Proceed if monitoring disabled
    
    try:
        status = guard.get_budget_status()
        
        if status["status"] != "active":
            return True
        
        # Check if we're near limits
        hourly_pct = status['hourly_usage']['percentage']
        daily_pct = status['daily_usage']['percentage']
        
        # Warning at 85%, block at 95%
        if hourly_pct > 95 or daily_pct > 95:
            print(f"🚨 BUDGET LIMIT EXCEEDED - Blocking {operation}")
            print(f"   Hourly: {hourly_pct:.1f}% | Daily: {daily_pct:.1f}%")
            return False
            
        elif hourly_pct > 85 or daily_pct > 85:
            print(f"⚠️ Budget warning - {operation} will proceed with monitoring")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Budget check error: {e}")
        return True  # Proceed on error

def show_workflow_budget_summary(guard: Optional[BudgetGuard], pr_url: str) -> None:
    """Show final budget summary for the workflow"""
    if not guard:
        return
    
    try:
        print("\n" + "="*60)
        print("💰 WORKFLOW BUDGET SUMMARY")
        print("="*60)
        
        status = guard.get_budget_status()
        
        if status["status"] == "active":
            print(f"📊 Final Usage:")
            print(f"   Hourly: ${status['hourly_usage']['current']:.4f} / ${status['hourly_usage']['limit']:.2f} ({status['hourly_usage']['percentage']:.1f}%)")
            print(f"   Daily:  ${status['daily_usage']['current']:.4f} / ${status['daily_usage']['limit']:.2f} ({status['daily_usage']['percentage']:.1f}%)")
            
            if status['recent_alerts'] > 0:
                print(f"\n🚨 Alerts triggered: {status['recent_alerts']}")
            else:
                print("\n✅ No budget alerts triggered")
            
            # Get PR-specific cost summary
            from monitoring.cost_logger import get_total_cost_for_pr
            pr_summary = get_total_cost_for_pr(pr_url)
            
            print(f"\n📋 This PR Cost Analysis:")
            print(f"   Total Cost: ${pr_summary['total_cost']:.6f}")
            print(f"   Total Operations: {pr_summary['operations']}")
            print(f"   Efficiency Score: {pr_summary.get('efficiency_score', 0):.2f}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Budget summary error: {e}")
```

#### C. Update Main Function
Modify your `main()` function to include budget checks:

```python
def main():
    # ... existing initialization code ...
    
    # Initialize budget monitoring
    budget_guard = initialize_budget_monitoring()
    
    # Before each agent, add budget check:
    
    # Before nitpicker agent
    if not check_budget_before_operation(budget_guard, "nitpicker_analysis", pr_url):
        print("❌ Operation cancelled due to budget limits")
        return
    
    # ... run nitpicker agent ...
    
    # Before architect agent  
    if not check_budget_before_operation(budget_guard, "architect_analysis", pr_url):
        print("❌ Operation cancelled due to budget limits")
        return
    
    # ... run architect agent ...
    
    # Before patch agent
    if not check_budget_before_operation(budget_guard, "patch_generation", pr_url):
        print("❌ Operation cancelled due to budget limits")
        return
    
    # ... run patch agent ...
    
    # Before comment agent
    if not check_budget_before_operation(budget_guard, "comment_generation", pr_url):
        print("❌ Operation cancelled due to budget limits")
        return
    
    # ... run comment agent ...
    
    # Show final budget summary
    show_workflow_budget_summary(budget_guard, pr_url)
    
    # Final status
    if BUDGET_MONITORING_ENABLED:
        final_status = get_budget_status_summary()
        print(f"🛡️ Final budget status: {final_status}")
```

### 3. Update `requirements.txt`

Add these dependencies:

```txt
# Budget Guard dependencies
PyYAML>=6.0
requests>=2.28.0
click>=8.0.0
```

## 🧪 Testing Integration

Create and run this test script (`test_integration.py`):

```python
#!/usr/bin/env python3
"""Test Budget Guard integration"""

def test_integration():
    try:
        # Test imports
        from monitoring.budget_guard import BudgetGuard, check_budget_integration
        from monitoring.cost_logger import get_budget_status_summary, log_cost
        print("✅ All imports successful")
        
        # Test initialization
        guard = BudgetGuard()
        print("✅ Budget Guard initialized")
        
        # Test status
        status = get_budget_status_summary()
        print(f"✅ Budget status: {status}")
        
        # Test cost logging with budget check
        cost = log_cost(
            pr_url="https://github.com/test/integration/pull/1",
            operation="integration_test",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=2000
        )
        print(f"✅ Cost logged with budget check: ${cost:.6f}")
        
        print("\n🎉 Integration test passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

if __name__ == "__main__":
    test_integration()
```

## 🚀 Usage

Once integrated, Budget Guard will:

1. **Automatically monitor** every AI operation cost
2. **Trigger alerts** when limits are approached
3. **Show budget status** in console output
4. **Block operations** if critical limits exceeded
5. **Generate reports** in the monitoring dashboard

### Check Budget Status
```bash
python monitoring/budget_guard.py --check
```

### View Monitoring Dashboard
```bash
python monitoring/pr_guard_monitor.py
```

### Configure Budget Limits
Edit `monitoring/budget_config.yaml`:
```yaml
daily_limit: 10.0      # USD
hourly_limit: 2.0      # USD
spike_threshold: 5.0   # 5x baseline
efficiency_min: 0.15   # $0.15/1K tokens
```

### Configure Slack Alerts (Optional)
Add to `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## 🎯 Verification

After integration, you should see:

1. **Console output**: "🛡️ Budget Guard integration enabled"
2. **Budget status**: Displayed before/after operations
3. **Real-time alerts**: When limits are exceeded
4. **Enhanced monitoring**: Budget data in dashboards

## 🔧 Troubleshooting

**Import Errors**: Install dependencies with `pip install PyYAML requests click`

**Config Errors**: Default config will be created automatically

**Slack 404 Errors**: Normal if webhook URL not configured

**Permission Errors**: Ensure write access to `logs/` directory

## 💡 Tips

- Start with low budget limits for testing/demo
- Use `BUDGET_EMERGENCY_OVERRIDE=true` to bypass limits
- Check `logs/budget_alerts.json` for alert history
- Monitor `logs/cost.csv` for cost tracking data

---

✅ **Integration Complete!** Your Secure PR Guard now has enterprise-grade budget monitoring!