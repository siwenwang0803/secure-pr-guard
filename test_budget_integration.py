#!/usr/bin/env python3
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
        print(f"\n🔍 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Budget Guard is fully integrated")
    else:
        print("⚠️ Some tests failed - check configuration")
        
    print("\n💡 Next steps:")
    print("- Run: python graph_review.py <PR_URL>")
    print("- Monitor: python monitoring/pr_guard_monitor.py") 
    print("- Check budget: python monitoring/budget_guard.py --check")

if __name__ == "__main__":
    main()
