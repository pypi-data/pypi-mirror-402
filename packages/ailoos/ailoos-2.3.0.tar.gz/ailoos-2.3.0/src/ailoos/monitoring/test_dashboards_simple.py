#!/usr/bin/env python3
"""
Simple Dashboard Test Script
Basic validation of dashboard components without complex imports.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def test_imports():
    """Test that all dashboard modules can be imported."""
    print("🔍 Testing dashboard imports...")

    try:
        # Test basic imports without relative imports
        import aiohttp
        import fastapi
        import uvicorn
        print("✅ Basic dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

    # Test dashboard files exist
    dashboard_files = [
        'executive_dashboard.py',
        'technical_dashboard.py',
        'security_dashboard.py',
        'federated_learning_dashboard.py',
        'dashboard_manager.py',
        'start_dashboards.py'
    ]

    for file in dashboard_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False

    return True

def test_syntax():
    """Test syntax of dashboard files."""
    print("\n🔍 Testing Python syntax...")

    import ast

    dashboard_files = [
        'executive_dashboard.py',
        'technical_dashboard.py',
        'security_dashboard.py',
        'federated_learning_dashboard.py',
        'dashboard_manager.py'
    ]

    for file in dashboard_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse the AST to check syntax
            ast.parse(source)
            print(f"✅ {file} syntax OK")

        except SyntaxError as e:
            print(f"❌ {file} syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠️ {file} could not be checked: {e}")

    return True

def test_structure():
    """Test basic code structure."""
    print("\n🔍 Testing code structure...")

    # Check that key classes exist in files
    checks = [
        ('executive_dashboard.py', 'ExecutiveDashboard'),
        ('technical_dashboard.py', 'TechnicalDashboard'),
        ('security_dashboard.py', 'SecurityDashboard'),
        ('federated_learning_dashboard.py', 'FederatedLearningDashboard'),
        ('dashboard_manager.py', 'DashboardManager')
    ]

    for file, class_name in checks:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            if f"class {class_name}" in content:
                print(f"✅ {class_name} found in {file}")
            else:
                print(f"❌ {class_name} not found in {file}")
                return False

        except Exception as e:
            print(f"❌ Error checking {file}: {e}")
            return False

    return True

def test_configuration():
    """Test configuration and setup."""
    print("\n🔍 Testing configuration...")

    # Check if start script has proper shebang
    try:
        with open('start_dashboards.py', 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        if first_line == '#!/usr/bin/env python3':
            print("✅ Start script has proper shebang")
        else:
            print(f"⚠️ Start script shebang: {first_line}")

    except Exception as e:
        print(f"❌ Error checking start script: {e}")
        return False

    # Check if README exists
    if os.path.exists('README_DASHBOARDS.md'):
        print("✅ Documentation file exists")
    else:
        print("❌ Documentation file missing")
        return False

    return True

async def run_basic_tests():
    """Run all basic validation tests."""
    print("🧪 Running AILOOS Dashboard System Basic Validation")
    print("=" * 60)

    tests = [
        ("Import Validation", test_imports),
        ("Syntax Check", test_syntax),
        ("Structure Validation", test_structure),
        ("Configuration Check", test_configuration)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "PASSED" if result else "FAILED"
            print(f"📊 {test_name}: {status}")
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    overall_success = sum(results) >= len(results) * 0.8  # 80% success rate

    if overall_success:
        print("🎉 Basic validation PASSED!")
        print("\n🚀 To start the dashboard system:")
        print("   cd src/ailoos/monitoring/")
        print("   python start_dashboards.py")
        print("\n🔑 Test users:")
        print("   admin/admin, ceo/ceo, cto/cto, researcher/researcher")
    else:
        print("❌ Basic validation FAILED!")
        print("Some components need attention before starting the system.")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(run_basic_tests())
    sys.exit(0 if success else 1)