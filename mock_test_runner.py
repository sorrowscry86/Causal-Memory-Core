#!/usr/bin/env python3
"""
Mock Test Runner for Causal Memory Core
Runs basic tests when pytest is not available, simulating the comprehensive test suite
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

class MockTestRunner:
    """Runs tests using unittest when pytest is unavailable"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': 'unittest-based',
            'tests': {}
        }
        
    def run_unit_tests(self):
        """Run unit tests using unittest"""
        print("🧪 Running Unit Tests (unittest framework)")
        
        env = {
            **os.environ,
            'OPENAI_API_KEY': 'sk-test-mock-key',
            'PYTHONPATH': os.path.join(os.getcwd(), 'src')
        }
        
        cmd = [sys.executable, '-m', 'unittest', 'tests.test_memory_core', '-v']
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
            duration = time.time() - start_time
            
            self.results['tests']['unit'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': duration,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ Unit tests passed ({duration:.2f}s)")
                # Parse output for test count
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Ran ' in line and ' tests in ' in line:
                        print(f"📊 {line}")
            else:
                print(f"❌ Unit tests failed ({duration:.2f}s)")
                print("STDERR:", result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏱️ Unit tests timed out")
            self.results['tests']['unit'] = {
                'status': 'timeout',
                'duration': 300,
                'error': 'Test execution timed out'
            }
        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            self.results['tests']['unit'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def run_basic_e2e_simulation(self):
        """Simulate E2E tests by testing core functionality"""
        print("\n🔗 Simulating E2E Tests (core functionality)")
        
        start_time = time.time()
        
        try:
            sys.path.append('src')
            from causal_memory_core import CausalMemoryCore
            from unittest.mock import Mock
            import tempfile
            import numpy as np
            
            # Create temp database
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db_path = temp_db.name
            temp_db.close()
            os.unlink(temp_db_path)
            
            # Mock dependencies
            mock_llm = Mock()
            mock_embedder = Mock()
            mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
            
            # Mock LLM response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test causal relationship"
            mock_llm.chat.completions.create.return_value = mock_response
            
            # Test scenario: add events and query
            core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_llm,
                embedding_model=mock_embedder
            )
            
            # Add test events
            core.add_event("User clicked login button")
            core.add_event("Login form appeared")
            core.add_event("User entered credentials")
            
            # Query for context
            context = core.get_context("login process")
            
            # Cleanup
            core.close()
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
            
            duration = time.time() - start_time
            
            self.results['tests']['e2e_simulation'] = {
                'status': 'passed',
                'duration': duration,
                'events_added': 3,
                'context_length': len(context) if context else 0
            }
            
            print(f"✅ E2E simulation passed ({duration:.2f}s)")
            print(f"📊 Added 3 events, retrieved context: {len(context) if context else 0} chars")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ E2E simulation failed: {e}")
            self.results['tests']['e2e_simulation'] = {
                'status': 'failed',
                'duration': duration,
                'error': str(e)
            }
    
    def run_config_tests(self):
        """Test configuration loading"""
        print("\n🔧 Testing Configuration")
        
        start_time = time.time()
        
        try:
            sys.path.append('src')
            import config
            
            # Test basic config access
            test_checks = [
                hasattr(config.Config, 'DB_PATH'),
                hasattr(config.Config, 'LLM_MODEL'),
                hasattr(config.Config, 'SIMILARITY_THRESHOLD'),
                hasattr(config.Config, 'OPENAI_API_KEY')
            ]
            
            duration = time.time() - start_time
            
            if all(test_checks):
                print(f"✅ Configuration tests passed ({duration:.2f}s)")
                print(f"📊 All required config attributes present")
                self.results['tests']['config'] = {
                    'status': 'passed',
                    'duration': duration,
                    'checks_passed': len(test_checks)
                }
            else:
                print(f"❌ Configuration tests failed - missing attributes")
                self.results['tests']['config'] = {
                    'status': 'failed',
                    'duration': duration,
                    'error': 'Missing required configuration attributes'
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Configuration tests failed: {e}")
            self.results['tests']['config'] = {
                'status': 'failed',
                'duration': duration,
                'error': str(e)
            }
    
    def generate_report(self):
        """Generate a test report"""
        print("\n📊 Test Summary Report")
        print("=" * 50)
        
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for test in self.results['tests'].values() if test.get('status') == 'passed')
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Total Test Suites: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        total_duration = sum(test.get('duration', 0) for test in self.results['tests'].values())
        print(f"⏱️ Total Duration: {total_duration:.2f}s")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, test_result in self.results['tests'].items():
            status_icon = "✅" if test_result.get('status') == 'passed' else "❌"
            duration = test_result.get('duration', 0)
            print(f"  {status_icon} {test_name}: {test_result.get('status', 'unknown')} ({duration:.2f}s)")
            
            if test_result.get('error'):
                print(f"    Error: {test_result['error']}")
        
        # Save results to file
        results_file = Path('test_results') / 'mock_test_results.json'
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return success_rate >= 75  # Consider 75%+ as success

def main():
    """Main test runner"""
    print("🚀 Causal Memory Core - Mock Test Runner")
    print("=" * 50)
    print("Note: This runner uses unittest instead of pytest")
    print()
    
    runner = MockTestRunner()
    
    # Run test suites
    runner.run_unit_tests()
    runner.run_basic_e2e_simulation()
    runner.run_config_tests()
    
    # Generate report
    success = runner.generate_report()
    
    if success:
        print("\n🎉 Overall test execution successful!")
    else:
        print("\n⚠️ Some tests failed - see details above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)