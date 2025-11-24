#!/usr/bin/env python3
"""
E2E Test Runner for Causal Memory Core
Demonstrates the E2E testing capabilities and provides a convenient test runner
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    if cwd is None:
        cwd = Path(__file__).parent
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['pytest', 'duckdb', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        result = run_command([sys.executable, '-c', f'import {package}'])
        if result.returncode != 0:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies"""
    if not packages:
        return True
    
    print(f"Installing missing dependencies: {', '.join(packages)}")
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages
    result = run_command(cmd)
    
    if result.returncode != 0:
        print(f"Failed to install dependencies: {result.stderr}")
        return False
    
    print("Dependencies installed successfully")
    return True

def run_unit_tests():
    """Run unit tests"""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_memory_core.py', '-v']
    result = run_command(cmd)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_e2e_tests(test_type=None):
    """Run E2E tests"""
    print("\n" + "="*60)
    print("RUNNING E2E TESTS")
    print("="*60)
    
    if test_type:
        test_path = f"tests/e2e/test_{test_type}_e2e.py"
        print(f"Running {test_type} E2E tests only")
    else:
        test_path = "tests/e2e/"
        print("Running all E2E tests")
    
    cmd = [sys.executable, '-m', 'pytest', test_path, '-v']
    result = run_command(cmd)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def demonstrate_scenarios():
    """Demonstrate the test scenarios we've created"""
    print("\n" + "="*60)
    print("E2E TEST SCENARIOS DEMONSTRATION")
    print("="*60)
    
    scenarios = {
        "API E2E Tests": [
            "Single event workflow (Initialize → Add Event → Query → Cleanup)",
            "Causal chain workflow (Multiple related events with causal relationships)",
            "Memory persistence across sessions",
            "Handling of special characters and unicode",
            "Large context queries with many events",
            "Error handling with invalid paths"
        ],
        "CLI E2E Tests": [
            "Adding events via command-line arguments",
            "Querying memory via command-line",
            "Interactive mode workflow simulation",
            "Error handling and validation",
            "Special characters in CLI arguments",
            "Help system verification"
        ],
        "MCP Server E2E Tests": [
            "MCP tool discovery (list_tools)",
            "add_event tool workflow",
            "query tool workflow", 
            "Tool parameter validation",
            "Error handling for unknown tools",
            "Concurrent tool calls"
        ],
        "Realistic Scenarios": [
            "Document editing workflow (17 steps)",
            "Software debugging session (17 steps)",
            "Data analysis workflow (20 steps)",
            "User onboarding process (21 steps)",
            "Error recovery scenario (20 steps)",
            "Multi-session memory continuity"
        ]
    }
    
    for category, tests in scenarios.items():
        print(f"\n{category}:")
        for i, test in enumerate(tests, 1):
            print(f"  {i}. {test}")
    
    print(f"\nTotal E2E test scenarios: {sum(len(tests) for tests in scenarios.values())}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="E2E Test Runner for Causal Memory Core")
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--install-deps', action='store_true', help='Install missing dependencies')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests')
    parser.add_argument('--type', choices=['api', 'cli', 'mcp_server', 'realistic_scenarios'], 
                       help='Run specific type of E2E tests')
    parser.add_argument('--demo', action='store_true', help='Demonstrate available test scenarios')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Show demonstration if requested
    if args.demo:
        demonstrate_scenarios()
        return
    
    # Check dependencies
    if args.check_deps or args.install_deps:
        missing = check_dependencies()
        if missing:
            print(f"Missing dependencies: {', '.join(missing)}")
            if args.install_deps:
                install_dependencies(missing)
            else:
                print("Use --install-deps to install them")
                return
        else:
            print("All dependencies are available")
    
    success = True
    
    # Run tests based on arguments
    if args.all or args.unit:
        success &= run_unit_tests()
    
    if args.all or args.e2e:
        success &= run_e2e_tests(args.type)
    
    # If no specific action requested, show help
    if not any([args.check_deps, args.install_deps, args.unit, args.e2e, args.all, args.demo]):
        parser.print_help()
        print("\nQuick start:")
        print("  python run_e2e_tests.py --demo       # Show available test scenarios")
        print("  python run_e2e_tests.py --check-deps # Check if dependencies are installed")
        print("  python run_e2e_tests.py --all        # Run all tests")
        print("  python run_e2e_tests.py --e2e --type api  # Run only API E2E tests")
        return
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main()