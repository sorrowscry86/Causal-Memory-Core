#!/usr/bin/env python3
"""
Comprehensive Test Runner for Causal Memory Core
Runs functionality tests, performance benchmarks, and generates detailed reports
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import argparse

class ComprehensiveTestRunner:
    """Manages comprehensive testing including functionality and performance"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.results_dir = self.project_root / "test_results"
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories for test results"""
        dirs = [
            self.results_dir,
            self.results_dir / "benchmarks",
            self.results_dir / "reports", 
            self.results_dir / "logs",
            self.results_dir / "artifacts"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(exist_ok=True)
    
    def run_command(self, cmd, cwd=None, capture_output=True):
        """Run a command and return result"""
        if cwd is None:
            cwd = self.project_root
            
        print(f"🔧 Running: {' '.join(cmd)}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        duration = time.time() - start_time
        print(f"⏱️  Completed in {duration:.2f}s (exit code: {result.returncode})")
        
        return result, duration
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("\n" + "="*60)
        print("🔍 CHECKING DEPENDENCIES")
        print("="*60)
        
        required_packages = [
            'pytest', 'duckdb', 'numpy', 'psutil', 
            'sentence_transformers', 'openai'
        ]
        
        missing_packages = []
        available_packages = []
        
        for package in required_packages:
            result, _ = self.run_command([sys.executable, '-c', f'import {package}'])
            if result.returncode == 0:
                available_packages.append(package)
                print(f"✅ {package}")
            else:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        return missing_packages, available_packages
    
    def install_dependencies(self, packages):
        """Install missing dependencies"""
        if not packages:
            return True
            
        print(f"\n📦 Installing dependencies: {', '.join(packages)}")
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages + ['--user']
        result, duration = self.run_command(cmd, capture_output=False)
        
        success = result.returncode == 0
        if success:
            print(f"✅ Dependencies installed successfully in {duration:.1f}s")
        else:
            print(f"❌ Failed to install dependencies")
            
        return success
    
    def run_functionality_tests(self):
        """Run all functionality tests"""
        print("\n" + "="*60)
        print("🧪 RUNNING FUNCTIONALITY TESTS")
        print("="*60)
        
        test_suites = [
            ('Unit Tests', ['tests/test_memory_core.py']),
            ('API E2E Tests', ['tests/e2e/test_api_e2e.py']),
            ('CLI E2E Tests', ['tests/e2e/test_cli_e2e.py']),
            ('MCP Server E2E Tests', ['tests/e2e/test_mcp_server_e2e.py']),
            ('Realistic Scenarios', ['tests/e2e/test_realistic_scenarios_e2e.py'])
        ]
        
        functionality_results = {}
        
        for suite_name, test_paths in test_suites:
            print(f"\n🔬 Running {suite_name}...")
            
            for test_path in test_paths:
                cmd = [
                    sys.executable, '-m', 'pytest', 
                    test_path, 
                    '-v', 
                    '--tb=short',
                    f'--junitxml={self.results_dir}/reports/{suite_name.lower().replace(" ", "_")}_results.xml'
                ]
                
                result, duration = self.run_command(cmd)
                
                functionality_results[f"{suite_name}_{test_path}"] = {
                    'suite_name': suite_name,
                    'test_path': test_path,
                    'success': result.returncode == 0,
                    'duration': duration,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                if result.returncode == 0:
                    print(f"✅ {suite_name} passed ({duration:.1f}s)")
                else:
                    print(f"❌ {suite_name} failed ({duration:.1f}s)")
                    print(f"Error output: {result.stderr[:200]}...")
        
        return functionality_results
    
    def run_performance_benchmarks(self):
        """Run performance benchmarking tests"""
        print("\n" + "="*60)
        print("📊 RUNNING PERFORMANCE BENCHMARKS") 
        print("="*60)
        
        benchmark_cmd = [
            sys.executable, '-m', 'pytest',
            'tests/e2e/test_performance_benchmarks.py',
            '-v', '-s',
            '--tb=short',
            f'--junitxml={self.results_dir}/reports/performance_benchmarks.xml'
        ]
        
        result, duration = self.run_command(benchmark_cmd)
        
        benchmark_results = {
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        if result.returncode == 0:
            print(f"✅ Performance benchmarks completed ({duration:.1f}s)")
        else:
            print(f"❌ Performance benchmarks failed ({duration:.1f}s)")
            print(f"Error output: {result.stderr[:200]}...")
        
        return benchmark_results
    
    def analyze_benchmark_results(self):
        """Analyze and summarize benchmark results"""
        print("\n📈 Analyzing benchmark results...")
        
        benchmark_dir = self.results_dir / "benchmarks"
        if not benchmark_dir.exists():
            print("⚠️  No benchmark results found")
            return {}
        
        # Get today's benchmark files
        today = datetime.now().strftime('%Y%m%d')
        daily_file = benchmark_dir / f"daily_benchmarks_{today}.jsonl"
        
        if not daily_file.exists():
            print("⚠️  No benchmark results for today")
            return {}
        
        # Parse benchmark results
        results = []
        with open(daily_file, 'r') as f:
            for line in f:
                results.append(json.loads(line.strip()))
        
        # Generate summary statistics
        summary = {
            'total_benchmarks': len(results),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'benchmarks_by_type': {},
            'performance_summary': {}
        }
        
        # Group by test type
        for result in results:
            test_name = result['test_name']
            if test_name not in summary['benchmarks_by_type']:
                summary['benchmarks_by_type'][test_name] = []
            summary['benchmarks_by_type'][test_name].append(result)
        
        # Calculate performance metrics
        for test_type, test_results in summary['benchmarks_by_type'].items():
            execution_times = [r['execution_time_seconds'] for r in test_results]
            memory_deltas = [r.get('memory_delta_mb', 0) for r in test_results]
            
            summary['performance_summary'][test_type] = {
                'count': len(test_results),
                'avg_execution_time': sum(execution_times) / len(execution_times),
                'max_execution_time': max(execution_times),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'max_memory_delta': max(memory_deltas)
            }
        
        # Save summary
        summary_file = self.results_dir / "reports" / f"benchmark_summary_{today}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Analyzed {len(results)} benchmark results")
        return summary
    
    def generate_test_report(self, functionality_results, benchmark_results, benchmark_summary):
        """Generate comprehensive test report"""
        print("\n📝 Generating comprehensive test report...")
        
        timestamp = datetime.now(timezone.utc)
        
        report = {
            'test_run_info': {
                'timestamp': timestamp.isoformat(),
                'project_root': str(self.project_root),
                'python_version': sys.version,
                'platform': sys.platform
            },
            'functionality_tests': {
                'summary': {
                    'total_suites': len(functionality_results),
                    'passed_suites': sum(1 for r in functionality_results.values() if r['success']),
                    'failed_suites': sum(1 for r in functionality_results.values() if not r['success']),
                    'total_duration': sum(r['duration'] for r in functionality_results.values())
                },
                'detailed_results': functionality_results
            },
            'performance_benchmarks': {
                'summary': {
                    'success': benchmark_results['success'],
                    'duration': benchmark_results['duration']
                },
                'benchmark_analysis': benchmark_summary
            },
            'recommendations': []
        }
        
        # Add recommendations based on results
        if report['functionality_tests']['summary']['failed_suites'] > 0:
            report['recommendations'].append("❌ Some functionality tests failed - review error logs")
        
        if not benchmark_results['success']:
            report['recommendations'].append("❌ Performance benchmarks failed - check system resources")
        
        if benchmark_summary.get('performance_summary'):
            slow_tests = [
                name for name, metrics in benchmark_summary['performance_summary'].items()
                if metrics['avg_execution_time'] > 5.0
            ]
            if slow_tests:
                report['recommendations'].append(f"⚠️  Slow performance detected in: {', '.join(slow_tests)}")
        
        if not report['recommendations']:
            report['recommendations'].append("✅ All tests passed with good performance")
        
        # Save comprehensive report
        report_file = self.results_dir / "reports" / f"comprehensive_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save human-readable summary
        summary_file = self.results_dir / "reports" / f"test_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_file, 'w') as f:
            f.write(self.format_report_markdown(report))
        
        print(f"📄 Report saved: {report_file}")
        print(f"📄 Summary saved: {summary_file}")
        
        return report
    
    def format_report_markdown(self, report):
        """Format test report as markdown"""
        md = f"""# Causal Memory Core - Test Report

## Test Run Information
- **Timestamp**: {report['test_run_info']['timestamp']}
- **Python Version**: {report['test_run_info']['python_version'].split()[0]}
- **Platform**: {report['test_run_info']['platform']}

## Functionality Tests Summary
- **Total Test Suites**: {report['functionality_tests']['summary']['total_suites']}
- **Passed**: {report['functionality_tests']['summary']['passed_suites']}
- **Failed**: {report['functionality_tests']['summary']['failed_suites']}
- **Total Duration**: {report['functionality_tests']['summary']['total_duration']:.2f}s

## Performance Benchmarks Summary
- **Benchmark Success**: {'✅ Passed' if report['performance_benchmarks']['summary']['success'] else '❌ Failed'}
- **Benchmark Duration**: {report['performance_benchmarks']['summary']['duration']:.2f}s

"""
        
        if report['performance_benchmarks']['benchmark_analysis'].get('performance_summary'):
            md += "## Performance Metrics\n\n"
            for test_type, metrics in report['performance_benchmarks']['benchmark_analysis']['performance_summary'].items():
                md += f"### {test_type}\n"
                md += f"- **Runs**: {metrics['count']}\n"
                md += f"- **Avg Execution**: {metrics['avg_execution_time']:.3f}s\n"
                md += f"- **Max Execution**: {metrics['max_execution_time']:.3f}s\n"
                md += f"- **Avg Memory Delta**: {metrics['avg_memory_delta']:.2f}MB\n\n"
        
        md += "## Recommendations\n\n"
        for rec in report['recommendations']:
            md += f"- {rec}\n"
        
        return md
    
    def update_development_journal(self, report):
        """Update the development journal with test results"""
        journal_file = self.results_dir / "benchmarking_journal.md"
        
        timestamp = datetime.now(timezone.utc)
        entry = f"""
---

## {timestamp.strftime('%Y-%m-%d %H:%M UTC')} - Test Run Results

### Test Execution Summary
- **Functionality Tests**: {report['functionality_tests']['summary']['passed_suites']}/{report['functionality_tests']['summary']['total_suites']} passed
- **Performance Benchmarks**: {'✅ Success' if report['performance_benchmarks']['summary']['success'] else '❌ Failed'}
- **Total Test Duration**: {report['functionality_tests']['summary']['total_duration'] + report['performance_benchmarks']['summary']['duration']:.1f}s

"""
        
        if report['performance_benchmarks']['benchmark_analysis'].get('performance_summary'):
            entry += "### Performance Highlights\n"
            for test_type, metrics in report['performance_benchmarks']['benchmark_analysis']['performance_summary'].items():
                entry += f"- **{test_type}**: {metrics['avg_execution_time']:.3f}s avg, {metrics['count']} runs\n"
            entry += "\n"
        
        entry += "### Key Findings\n"
        for rec in report['recommendations']:
            entry += f"- {rec}\n"
        
        entry += "\n"
        
        # Append to journal
        with open(journal_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        print(f"📓 Updated development journal: {journal_file}")
    
    def run_comprehensive_tests(self, install_deps=False, run_functionality=True, run_benchmarks=True):
        """Run all tests and generate comprehensive report"""
        print("🚀 Starting Comprehensive Test Suite")
        print("="*60)
        
        # Check dependencies
        missing_deps, available_deps = self.check_dependencies()
        
        if missing_deps:
            if install_deps:
                if not self.install_dependencies(missing_deps):
                    print("❌ Failed to install dependencies. Aborting.")
                    return False
            else:
                print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
                print("Use --install-deps to install automatically")
                return False
        
        # Run tests
        functionality_results = {}
        benchmark_results = {'success': True, 'duration': 0}
        benchmark_summary = {}
        
        if run_functionality:
            functionality_results = self.run_functionality_tests()
        
        if run_benchmarks:
            benchmark_results = self.run_performance_benchmarks()
            benchmark_summary = self.analyze_benchmark_results()
        
        # Generate comprehensive report
        report = self.generate_test_report(functionality_results, benchmark_results, benchmark_summary)
        
        # Update development journal
        self.update_development_journal(report)
        
        # Print final summary
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE TEST RESULTS")
        print("="*60)
        
        total_passed = functionality_results and report['functionality_tests']['summary']['failed_suites'] == 0
        benchmarks_passed = benchmark_results['success']
        
        if total_passed and benchmarks_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests need attention:")
            if not total_passed:
                print(f"   - {report['functionality_tests']['summary']['failed_suites']} functionality test suites failed")
            if not benchmarks_passed:
                print("   - Performance benchmarks failed")
        
        print(f"\n📊 Results saved in: {self.results_dir}")
        return total_passed and benchmarks_passed


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner for Causal Memory Core")
    parser.add_argument('--install-deps', action='store_true', help='Install missing dependencies')
    parser.add_argument('--no-functionality', action='store_true', help='Skip functionality tests')
    parser.add_argument('--no-benchmarks', action='store_true', help='Skip performance benchmarks')
    parser.add_argument('--benchmarks-only', action='store_true', help='Run only performance benchmarks')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    run_functionality = not args.no_functionality and not args.benchmarks_only
    run_benchmarks = not args.no_benchmarks
    
    success = runner.run_comprehensive_tests(
        install_deps=args.install_deps,
        run_functionality=run_functionality,
        run_benchmarks=run_benchmarks
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()