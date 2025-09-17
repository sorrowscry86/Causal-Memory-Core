#!/usr/bin/env python3
"""
Validate Test Environment for Causal Memory Core
Checks available dependencies and runs basic tests to validate the setup
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor} is supported")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} may have compatibility issues")
        return False

def check_dependencies():
    """Check required dependencies"""
    dependencies = {
        'duckdb': 'Core database engine',
        'openai': 'OpenAI API client', 
        'numpy': 'Numerical computing',
        'sentence_transformers': 'Text embeddings',
        'pydantic': 'Data validation'
    }
    
    print(f"\n📦 Checking Core Dependencies:")
    available = {}
    
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep}: {desc}")
            available[dep] = True
        except ImportError:
            print(f"❌ {dep}: {desc} - NOT AVAILABLE")
            available[dep] = False
    
    return available

def check_test_dependencies():
    """Check testing dependencies"""
    test_deps = {
        'pytest': 'Test framework',
        'coverage': 'Coverage reporting',
        'unittest.mock': 'Mocking framework (built-in)'
    }
    
    print(f"\n🧪 Checking Test Dependencies:")
    available = {}
    
    for dep, desc in test_deps.items():
        try:
            if dep == 'unittest.mock':
                from unittest import mock
            else:
                __import__(dep)
            print(f"✅ {dep}: {desc}")
            available[dep] = True
        except ImportError:
            print(f"❌ {dep}: {desc} - NOT AVAILABLE")
            available[dep] = False
    
    return available

def test_basic_import():
    """Test basic project imports"""
    print(f"\n🔬 Testing Basic Imports:")
    try:
        sys.path.append('src')
        from causal_memory_core import CausalMemoryCore
        print("✅ CausalMemoryCore import successful")
        return True
    except Exception as e:
        print(f"❌ CausalMemoryCore import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with mocks"""
    print(f"\n⚙️  Testing Basic Functionality:")
    try:
        sys.path.append('src')
        from causal_memory_core import CausalMemoryCore
        from unittest.mock import Mock
        import numpy as np
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db.name
        temp_db.close()
        os.unlink(temp_db_path)
        
        # Mock dependencies
        mock_llm = Mock()
        mock_embedder = Mock()
        mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Initialize core
        core = CausalMemoryCore(
            db_path=temp_db_path,
            llm_client=mock_llm,
            embedding_model=mock_embedder
        )
        
        # Test database initialization
        result = core.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
        if result:
            print("✅ Database initialization successful")
        else:
            # Try DuckDB syntax
            result = core.conn.execute("SELECT table_name FROM duckdb_tables() WHERE table_name = 'events'").fetchone()
            if result:
                print("✅ Database initialization successful (DuckDB)")
            else:
                print("❌ Database table creation failed")
                return False
        
        # Cleanup
        core.close()
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
            
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def run_available_tests():
    """Run tests that are available"""
    print(f"\n🚀 Running Available Tests:")
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest available - running pytest tests")
        
        # Try to run unit tests
        cmd = [sys.executable, '-m', 'pytest', 'tests/test_memory_core.py', '-v', '--tb=short']
        result = subprocess.run(cmd, capture_output=True, text=True, env={
            **os.environ,
            'OPENAI_API_KEY': 'sk-test-mock-key-for-testing',
            'PYTHONPATH': os.path.join(os.getcwd(), 'src')
        })
        
        if result.returncode == 0:
            print("✅ Unit tests passed")
            print(result.stdout)
        else:
            print("❌ Unit tests failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except ImportError:
        print("❌ pytest not available - trying unittest")
        
        # Try to run with unittest
        try:
            cmd = [sys.executable, '-m', 'unittest', 'tests.test_memory_core', '-v']
            result = subprocess.run(cmd, capture_output=True, text=True, env={
                **os.environ,
                'OPENAI_API_KEY': 'sk-test-mock-key-for-testing',
                'PYTHONPATH': os.path.join(os.getcwd(), 'src')
            })
            
            if result.returncode == 0:
                print("✅ Unit tests passed (unittest)")
                print(result.stdout)
            else:
                print("❌ Unit tests failed (unittest)")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
        except Exception as e:
            print(f"❌ Could not run tests: {e}")

def main():
    """Main validation function"""
    print("🔍 Causal Memory Core - Test Environment Validation")
    print("=" * 60)
    
    # Change to repo directory
    repo_path = Path(__file__).parent
    os.chdir(repo_path)
    
    results = {}
    
    # Check Python version
    results['python_version'] = check_python_version()
    
    # Check dependencies
    results['core_deps'] = check_dependencies()
    results['test_deps'] = check_test_dependencies()
    
    # Test basic functionality
    results['basic_import'] = test_basic_import()
    results['basic_functionality'] = test_basic_functionality()
    
    # Run available tests
    run_available_tests()
    
    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"{'=' * 60}")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"✅ Passed: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("🎉 Environment validation successful!")
        return True
    else:
        print("⚠️  Some checks failed - see details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)