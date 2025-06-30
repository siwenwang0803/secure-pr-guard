#!/usr/bin/env python3
"""
Demo Script for Budget Guard System
Demonstrates real-time budget monitoring and alerting capabilities
"""

import os
import time
import csv
from datetime import datetime
from pathlib import Path
from monitoring.budget_guard import BudgetGuard, AlertConfig

def create_demo_data():
    """Create sample cost data to trigger budget alerts"""
    
    print("🧪 Creating demo cost data...")
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create cost.csv with demo data
    csv_file = logs_dir / "cost.csv"
    
    # Demo data that will trigger alerts
    demo_operations = [
        # Normal operations
        (datetime.now().timestamp() - 3600, "https://github.com/demo/repo/pull/1", "nitpicker_analysis", "gpt-4o-mini", 500, 100, 600, 0.0009, 3200),
        (datetime.now().timestamp() - 3500, "https://github.com/demo/repo/pull/1", "patch_generation", "gpt-4o-mini", 800, 150, 950, 0.0014, 4100),
        
        # Expensive operations (will trigger cost alerts)
        (datetime.now().timestamp() - 1800, "https://github.com/demo/repo/pull/2", "nitpicker_analysis", "gpt-4o", 2000, 500, 2500, 0.0125, 8500),
        (datetime.now().timestamp() - 1700, "https://github.com/demo/repo/pull/2", "architect_analysis", "gpt-4o", 1800, 400, 2200, 0.0110, 7200),
        
        # Recent spike operations (will trigger spike alerts)
        (datetime.now().timestamp() - 300, "https://github.com/demo/repo/pull/3", "nitpicker_analysis", "gpt-4o", 3000, 800, 3800, 0.0190, 12000),
        (datetime.now().timestamp() - 250, "https://github.com/demo/repo/pull/3", "patch_generation", "gpt-4o", 2500, 600, 3100, 0.0155, 9800),
        (datetime.now().timestamp() - 200, "https://github.com/demo/repo/pull/3", "comment_generation", "gpt-4o", 2200, 550, 2750, 0.0138, 8900),
        
        # Very recent high-cost operations (will trigger hourly limit)
        (datetime.now().timestamp() - 120, "https://github.com/demo/repo/pull/4", "nitpicker_analysis", "gpt-4o", 4000, 1000, 5000, 0.0250, 15000),
        (datetime.now().timestamp() - 60, "https://github.com/demo/repo/pull/4", "patch_generation", "gpt-4o", 3500, 900, 4400, 0.0220, 13500),
    ]
    
    # Write to CSV
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            "timestamp", "pr_url", "operation", "model", 
            "prompt_tokens", "completion_tokens", "total_tokens", 
            "cost_usd", "latency_ms"
        ])
        
        # Write demo data
        for row in demo_operations:
            writer.writerow(row)
    
    print(f"✅ Created demo data: {len(demo_operations)} operations")
    print(f"📁 File: {csv_file}")
    
    # Calculate total costs for demo
    total_cost = sum(row[7] for row in demo_operations)
    recent_cost = sum(row[7] for row in demo_operations[-5:])  # Last 5 operations
    
    print(f"💰 Total demo cost: ${total_cost:.4f}")
    print(f"💰 Recent cost (trigger alerts): ${recent_cost:.4f}")

def configure_demo_budget():
    """Configure budget limits for demo (low thresholds to trigger alerts)"""
    
    print("⚙️ Configuring demo budget settings...")
    
    # Create restrictive budget config for demo
    demo_config = AlertConfig(
        daily_limit=0.20,       # Very low daily limit ($0.20)
        hourly_limit=0.08,      # Very low hourly limit ($0.08)
        spike_threshold=2.0,    # Low spike threshold (2x baseline)
        efficiency_min=0.08,    # Low efficiency threshold
        cooldown_minutes=1,     # Short cooldown for demo
        slack_enabled=True,
        email_enabled=True,
        console_enabled=True
    )
    
    # Save demo config
    config_path = Path("monitoring/budget_config.yaml")
    config_path.parent.mkdir(exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump({
            'daily_limit': demo_config.daily_limit,
            'hourly_limit': demo_config.hourly_limit,
            'spike_threshold': demo_config.spike_threshold,
            'efficiency_min': demo_config.efficiency_min,
            'cooldown_minutes': demo_config.cooldown_minutes,
            'slack_enabled': demo_config.slack_enabled,
            'email_enabled': demo_config.email_enabled,
            'console_enabled': demo_config.console_enabled,
            'warning_threshold': 0.7,
            'critical_threshold': 0.9
        }, f, default_flow_style=False, indent=2)
    
    print(f"✅ Demo config saved: {config_path}")
    print(f"🎯 Daily limit: ${demo_config.daily_limit}")
    print(f"🎯 Hourly limit: ${demo_config.hourly_limit}")

def run_budget_demo():
    """Run the complete budget guard demo"""
    
    print("🚀 BUDGET GUARD SYSTEM DEMO")
    print("=" * 50)
    print("This demo will:")
    print("1. Create sample cost data that exceeds budget limits")
    print("2. Configure restrictive budget thresholds")
    print("3. Trigger budget alerts in real-time")
    print("4. Display alert system capabilities")
    print("=" * 50)
    
    # Step 1: Create demo data
    create_demo_data()
    print()
    
    # Step 2: Configure budget
    configure_demo_budget()
    print()
    
    # Step 3: Initialize Budget Guard
    print("🛡️ Initializing Budget Guard...")
    guard = BudgetGuard()
    print()
    
    # Step 4: Show current status
    print("📊 Current Budget Status:")
    status = guard.get_budget_status()
    
    if status["status"] == "active":
        print(f"   Hourly: ${status['hourly_usage']['current']:.4f} / ${status['hourly_usage']['limit']:.2f} ({status['hourly_usage']['percentage']:.1f}%)")
        print(f"   Daily:  ${status['daily_usage']['current']:.4f} / ${status['daily_usage']['limit']:.2f} ({status['daily_usage']['percentage']:.1f}%)")
    print()
    
    # Step 5: Trigger alerts by checking budget
    print("🚨 Checking budget limits (this will trigger alerts)...")
    alerts = guard.check_budget_limits(
        pr_url="https://github.com/demo/repo/pull/999",
        operation="demo_check"
    )
    
    print(f"✅ Generated {len(alerts)} alerts")
    print()
    
    # Step 6: Show budget report
    print("📋 FINAL BUDGET REPORT:")
    print(guard.generate_budget_report())
    
    # Step 7: Demo summary
    print("\n🎯 DEMO COMPLETE!")
    print("=" * 50)
    print("What happened:")
    print("✅ Created high-cost operations that exceed budget limits")
    print("✅ Triggered real-time budget alerts")
    print("✅ Demonstrated multi-channel alerting (Console/Slack/Email)")
    print("✅ Showed enterprise monitoring capabilities")
    print()
    print("🔧 Next steps:")
    print("- Configure real Slack webhook in .env file")
    print("- Set up email credentials for production alerts")
    print("- Adjust budget limits in monitoring/budget_config.yaml")
    print("- Integrate with existing graph_review.py workflow")
    print()
    print("📊 View the monitoring dashboard:")
    print("python monitoring/pr_guard_monitor.py")

def test_slack_integration():
    """Test Slack integration with sample alert"""
    
    print("📱 Testing Slack Integration...")
    
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not configured")
        print("💡 Set SLACK_WEBHOOK_URL in your .env file to test Slack alerts")
        return False
    
    # Create test Budget Guard and send test alert
    guard = BudgetGuard()
    
    # Send test alert
    print("🧪 Sending test alert to Slack...")
    import sys
    sys.argv = ['budget_guard.py', '--test-alerts']
    
    try:
        from monitoring.budget_guard import Alert
        test_alert = Alert(
            timestamp=datetime.now(),
            alert_type='demo_test',
            severity='warning',
            message='🎭 Demo alert: Budget Guard is working!',
            current_value=0.15,
            threshold=0.10,
            pr_url='https://github.com/demo/repo/pull/999',
            operation='slack_test'
        )
        
        guard._send_slack_alert(test_alert)
        print("✅ Test alert sent to Slack!")
        return True
        
    except Exception as e:
        print(f"❌ Slack test failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🛡️ Budget Guard Demo System")
    parser.add_argument('--full-demo', action='store_true', help='Run complete demo')
    parser.add_argument('--test-slack', action='store_true', help='Test Slack integration only')
    parser.add_argument('--create-data', action='store_true', help='Create demo data only')
    
    args = parser.parse_args()
    
    try:
        if args.test_slack:
            test_slack_integration()
        elif args.create_data:
            create_demo_data()
        elif args.full_demo:
            run_budget_demo()
        else:
            print("🛡️ Budget Guard Demo")
            print("Options:")
            print("  --full-demo    Run complete demonstration")
            print("  --test-slack   Test Slack integration")
            print("  --create-data  Create sample data")
            print()
            print("💡 Tip: Start with --full-demo to see all features")
            
    except KeyboardInterrupt:
        print("\n✅ Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        raise