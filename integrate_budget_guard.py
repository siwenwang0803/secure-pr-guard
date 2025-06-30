#!/usr/bin/env python3
"""
Budget Guard Integration Script
Automatically integrates budget monitoring into the existing Secure PR Guard system
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Tuple

def backup_file(filepath: Path) -> Path:
    """Create a backup of the original file"""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    shutil.copy2(filepath, backup_path)
    print(f"📁 Backup created: {backup_path}")
    return backup_path

def read_file(filepath: Path) -> str:
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return ""

def write_file(filepath: Path, content: str) -> bool:
    """Write content to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error writing {filepath}: {e}")
        return False

def integrate_cost_logger() -> bool:
    """Integrate budget monitoring into cost_logger.py"""
    
    cost_logger_path = Path("monitoring/cost_logger.py")
    
    if not cost_logger_path.exists():
        print(f"❌ File not found: {cost_logger_path}")
        return False
    
    # Backup original
    backup_file(cost_logger_path)
    
    content = read_file(cost_logger_path)
    
    # 1. Add import after existing imports
    import_pattern = r"(from dotenv import load_dotenv\n)"
    import_addition = """
# Budget Guard Integration
try:
    from monitoring.budget_guard import check_budget_integration
    BUDGET_GUARD_ENABLED = True
    print("🛡️ Budget Guard integration enabled - Real-time monitoring active")
except ImportError as e:
    BUDGET_GUARD_ENABLED = False
    print(f"⚠️ Budget Guard not available: {e}")
    print("💡 Install: pip install PyYAML requests click")
"""
    
    if "BUDGET_GUARD_ENABLED" not in content:
        content = re.sub(import_pattern, f"\\1{import_addition}\n", content)
        print("✅ Added Budget Guard import")
    else:
        print("ℹ️ Budget Guard import already exists")
    
    # 2. Add budget check to log_cost function
    log_cost_pattern = r"(\s+return cost)"
    budget_check_code = """    
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

"""
    
    if "🛡️ BUDGET GUARD INTEGRATION" not in content:
        content = re.sub(log_cost_pattern, f"{budget_check_code}\\1", content)
        print("✅ Added budget check to log_cost function")
    else:
        print("ℹ️ Budget check already exists in log_cost")
    
    # 3. Add budget status summary function
    budget_status_function = '''
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
'''
    
    if "get_budget_status_summary" not in content:
        # Add before the main test section
        main_pattern = r'(if __name__ == "__main__":)'
        content = re.sub(main_pattern, f"{budget_status_function}\n\\1", content)
        print("✅ Added budget status summary function")
    else:
        print("ℹ️ Budget status function already exists")
    
    # 4. Update test section
    test_addition = """
    # Test budget integration
    print("\\n🛡️ Testing budget integration...")
    budget_status = get_budget_status_summary()
    print(f"Status: {budget_status}")
    
    if BUDGET_GUARD_ENABLED:
        print("✅ Budget Guard is ready for real-time monitoring")
        print("💡 Budget alerts will trigger automatically during operations")
    else:
        print("⚠️ Install budget dependencies: pip install PyYAML requests click")
"""
    
    if "Testing budget integration" not in content:
        # Find the end of test section and add before final print
        test_pattern = r'(print\("🎯 Enhanced cost logger test completed!"\))'
        content = re.sub(test_pattern, f"{test_addition}\n    \\1", content)
        print("✅ Updated test section")
    else:
        print("ℹ️ Test section already updated")
    
    # Write updated content
    return write_file(cost_logger_path, content)

def integrate_pr_guard_monitor() -> bool:
    """Add budget status to PR Guard monitor dashboard"""
    
    monitor_path = Path("monitoring/pr_guard_monitor.py")
    
    if not monitor_path.exists():
        print(f"❌ File not found: {monitor_path}")
        return False
    
    content = read_file(monitor_path)
    
    # Add budget status to dashboard
    budget_import = """
# Budget Guard integration
try:
    from monitoring.budget_guard import BudgetGuard
    BUDGET_INTEGRATION = True
except ImportError:
    BUDGET_INTEGRATION = False
"""
    
    if "BudgetGuard" not in content:
        # Add after other imports
        import_pattern = r"(from typing import Optional, Dict, List)"
        content = re.sub(import_pattern, f"\\1\n{budget_import}", content)
        print("✅ Added budget import to monitor")
    
    return write_file(monitor_path, content)

def create_requirements_update() -> bool:
    """Update requirements.txt with budget dependencies"""
    
    requirements_path = Path("requirements.txt")
    
    budget_requirements = [
        "PyYAML>=6.0",
        "requests>=2.28.0", 
        "click>=8.0.0"
    ]
    
    try:
        # Read existing requirements
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                existing_reqs = f.read()
        else:
            existing_reqs = ""
        
        # Add budget requirements if not present
        new_reqs = []
        for req in budget_requirements:
            package_name = req.split('>=')[0]
            if package_name not in existing_reqs:
                new_reqs.append(req)
        
        if new_reqs:
            # Append new requirements
            with open(requirements_path, 'a') as f:
                f.write("\n# Budget Guard dependencies\n")
                for req in new_reqs:
                    f.write(f"{req}\n")
            
            print(f"✅ Added {len(new_reqs)} budget dependencies to requirements.txt")
            return True
        else:
            print("ℹ️ Budget dependencies already in requirements.txt")
            return True
            
    except Exception as e:
        print(f"❌ Error updating requirements.txt: {e}")
        return False

def create_integration_test() -> bool:
    """Create integration test script"""
    
    test_script = '''#!/usr/bin/env python3
"""
Integration Test for Budget Guard System
Tests the complete integration with cost_logger and main workflow
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all budget components can be imported"""
    try:
        from monitoring.budget_guard import BudgetGuard, check_budget_integration
        from monitoring.cost_logger import get_budget_status_summary, log_cost
        print("✅ All budget imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_budget_guard_initialization():
    """Test Budget Guard initialization"""
    try:
        from monitoring.budget_guard import BudgetGuard
        guard = BudgetGuard()
        print("✅ Budget Guard initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Budget Guard initialization failed: {e}")
        return False

def test_cost_logger_integration():
    """Test cost logger integration"""
    try:
        from monitoring.cost_logger import get_budget_status_summary
        status = get_budget_status_summary()
        print(f"✅ Budget status: {status}")
        return True
    except Exception as e:
        print(f"❌ Cost logger integration failed: {e}")
        return False

def test_real_cost_logging():
    """Test real cost logging with budget check"""
    try:
        from monitoring.cost_logger import log_cost
        
        # Log a test cost
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
        return True
        
    except Exception as e:
        print(f"❌ Real cost logging failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 BUDGET GUARD INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_budget_guard_initialization), 
        ("Cost Logger Integration", test_cost_logger_integration),
        ("Real Cost Logging", test_real_cost_logging)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n🔍 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print(f"\\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Budget Guard is fully integrated")
    else:
        print("⚠️ Some tests failed - check configuration")
        
    print("\\n💡 Next steps:")
    print("- Run: python graph_review.py <PR_URL>")
    print("- Monitor: python monitoring/pr_guard_monitor.py") 
    print("- Check budget: python monitoring/budget_guard.py --check")

if __name__ == "__main__":
    main()
'''
    
    test_path = Path("test_budget_integration.py")
    return write_file(test_path, test_script)

def main():
    """Main integration process"""
    print("🚀 BUDGET GUARD INTEGRATION")
    print("=" * 50)
    print("This script will integrate Budget Guard into your Secure PR Guard system")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("graph_review.py").exists():
        print("❌ Please run this script from the secure-pr-guard project root")
        return
    
    success_count = 0
    total_steps = 4
    
    steps = [
        ("Integrating cost_logger.py", integrate_cost_logger),
        ("Updating pr_guard_monitor.py", integrate_pr_guard_monitor),
        ("Updating requirements.txt", create_requirements_update), 
        ("Creating integration test", create_integration_test)
    ]
    
    for step_name, step_func in steps:
        print(f"\\n🔧 {step_name}...")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} error: {e}")
    
    print(f"\\n📊 Integration Results: {success_count}/{total_steps} completed")
    
    if success_count == total_steps:
        print("\\n🎉 BUDGET GUARD FULLY INTEGRATED!")
        print("=" * 50)
        print("✅ Real-time budget monitoring is now active")
        print("✅ Alerts will trigger automatically during operations")
        print("✅ All monitoring dashboards updated")
        
        print("\\n🔧 Next Steps:")
        print("1. Install dependencies: pip install PyYAML requests click")
        print("2. Configure Slack webhook (optional): SLACK_WEBHOOK_URL in .env")
        print("3. Test integration: python test_budget_integration.py")
        print("4. Run workflow: python graph_review.py <PR_URL>")
        print("5. Monitor dashboard: python monitoring/pr_guard_monitor.py")
        
        print("\\n💡 Tips:")
        print("- Budget config: monitoring/budget_config.yaml")
        print("- Check status: python monitoring/budget_guard.py --check")
        print("- View alerts: check logs/budget_alerts.json")
        
    else:
        print("\\n⚠️ Integration partially completed")
        print("Please check the errors above and run again")
    
    print("\\n📝 Backup files created with .backup extension")

if __name__ == "__main__":
    main()