#!/usr/bin/env python3
"""
Benchmark Analysis and Reporting Tool
Analyzes benchmark results and generates comprehensive reports
"""

import os
import json
import glob
from datetime import datetime, timezone
import statistics
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

class BenchmarkAnalyzer:
    """Analyzes and reports on benchmark test results"""
    
    def __init__(self, results_dir="test_results/benchmarks"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def load_benchmark_data(self):
        """Load all benchmark data from JSON files"""
        data = []
        
        # Load individual benchmark files
        for json_file in glob.glob(str(self.results_dir / "*.json")):
            try:
                with open(json_file, 'r') as f:
                    benchmark_data = json.load(f)
                    benchmark_data['source_file'] = json_file
                    data.append(benchmark_data)
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
        
        # Load daily summary files (JSONL format)
        for jsonl_file in glob.glob(str(self.results_dir / "daily_benchmarks_*.jsonl")):
            try:
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            benchmark_data = json.loads(line.strip())
                            benchmark_data['source_file'] = jsonl_file
                            data.append(benchmark_data)
            except Exception as e:
                print(f"Warning: Could not load {jsonl_file}: {e}")
        
        print(f"📊 Loaded {len(data)} benchmark data points")
        return data
    
    def analyze_performance_trends(self, data):
        """Analyze performance trends across benchmark runs"""
        analysis = {
            'summary': {
                'total_benchmarks': len(data),
                'test_types': set(),
                'date_range': {'earliest': None, 'latest': None}
            },
            'by_test_type': {},
            'performance_metrics': {},
            'trends': {}
        }
        
        # Group data by test type
        by_test = {}
        timestamps = []
        
        for benchmark in data:
            test_name = benchmark.get('test_name', 'unknown')
            analysis['summary']['test_types'].add(test_name)
            
            if test_name not in by_test:
                by_test[test_name] = []
            by_test[test_name].append(benchmark)
            
            # Track timestamps
            if 'timestamp' in benchmark:
                try:
                    ts = datetime.fromisoformat(benchmark['timestamp'].replace('Z', '+00:00'))
                    timestamps.append(ts)
                except:
                    pass
        
        if timestamps:
            analysis['summary']['date_range']['earliest'] = min(timestamps).isoformat()
            analysis['summary']['date_range']['latest'] = max(timestamps).isoformat()
        
        # Analyze each test type
        for test_name, test_data in by_test.items():
            execution_times = []
            memory_deltas = []
            
            for test in test_data:
                if 'execution_time_seconds' in test:
                    execution_times.append(test['execution_time_seconds'])
                if 'memory_delta_mb' in test:
                    memory_deltas.append(test['memory_delta_mb'])
            
            analysis['by_test_type'][test_name] = {
                'count': len(test_data),
                'execution_times': {
                    'mean': statistics.mean(execution_times) if execution_times else 0,
                    'median': statistics.median(execution_times) if execution_times else 0,
                    'min': min(execution_times) if execution_times else 0,
                    'max': max(execution_times) if execution_times else 0,
                    'stddev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                },
                'memory_usage': {
                    'mean': statistics.mean(memory_deltas) if memory_deltas else 0,
                    'median': statistics.median(memory_deltas) if memory_deltas else 0,
                    'min': min(memory_deltas) if memory_deltas else 0,
                    'max': max(memory_deltas) if memory_deltas else 0,
                    'stddev': statistics.stdev(memory_deltas) if len(memory_deltas) > 1 else 0
                }
            }
        
        return analysis
    
    def generate_performance_report(self, analysis):
        """Generate comprehensive performance report"""
        timestamp = datetime.now(timezone.utc)
        
        report = f"""# Causal Memory Core - Benchmark Analysis Report

**Generated**: {timestamp.strftime('%Y-%m-%d %H:%M UTC')}

## Summary

- **Total Benchmarks**: {analysis['summary']['total_benchmarks']}
- **Test Types**: {len(analysis['summary']['test_types'])}
- **Date Range**: {analysis['summary']['date_range']['earliest']} to {analysis['summary']['date_range']['latest']}

## Performance Analysis by Test Type

"""
        
        for test_name, metrics in analysis['by_test_type'].items():
            report += f"""### {test_name}

**Execution Performance**:
- Runs: {metrics['count']}
- Mean: {metrics['execution_times']['mean']:.3f}s
- Median: {metrics['execution_times']['median']:.3f}s
- Range: {metrics['execution_times']['min']:.3f}s - {metrics['execution_times']['max']:.3f}s
- Std Dev: {metrics['execution_times']['stddev']:.3f}s

**Memory Usage**:
- Mean Delta: {metrics['memory_usage']['mean']:.2f}MB
- Median Delta: {metrics['memory_usage']['median']:.2f}MB
- Range: {metrics['memory_usage']['min']:.2f}MB - {metrics['memory_usage']['max']:.2f}MB
- Std Dev: {metrics['memory_usage']['stddev']:.2f}MB

"""
        
        # Add performance insights
        report += """## Performance Insights

"""
        
        # Find fastest and slowest tests
        if analysis['by_test_type']:
            fastest_test = min(analysis['by_test_type'].items(), 
                             key=lambda x: x[1]['execution_times']['mean'])
            slowest_test = max(analysis['by_test_type'].items(), 
                             key=lambda x: x[1]['execution_times']['mean'])
            
            report += f"- **Fastest Test**: {fastest_test[0]} ({fastest_test[1]['execution_times']['mean']:.3f}s avg)\n"
            report += f"- **Slowest Test**: {slowest_test[0]} ({slowest_test[1]['execution_times']['mean']:.3f}s avg)\n"
            
            # Memory efficiency
            most_memory = max(analysis['by_test_type'].items(), 
                            key=lambda x: x[1]['memory_usage']['mean'])
            least_memory = min(analysis['by_test_type'].items(), 
                             key=lambda x: x[1]['memory_usage']['mean'])
            
            report += f"- **Most Memory**: {most_memory[0]} ({most_memory[1]['memory_usage']['mean']:.2f}MB avg)\n"
            report += f"- **Least Memory**: {least_memory[0]} ({least_memory[1]['memory_usage']['mean']:.2f}MB avg)\n"
        
        # Performance recommendations
        report += """
## Recommendations

"""
        
        slow_threshold = 1.0  # seconds
        memory_threshold = 50.0  # MB
        
        recommendations = []
        
        for test_name, metrics in analysis['by_test_type'].items():
            if metrics['execution_times']['mean'] > slow_threshold:
                recommendations.append(f"- ⚠️  **{test_name}** is running slowly (avg: {metrics['execution_times']['mean']:.3f}s)")
            
            if metrics['memory_usage']['mean'] > memory_threshold:
                recommendations.append(f"- ⚠️  **{test_name}** uses significant memory (avg: {metrics['memory_usage']['mean']:.2f}MB)")
            
            if metrics['execution_times']['stddev'] > 0.5:
                recommendations.append(f"- 📊 **{test_name}** has inconsistent performance (stddev: {metrics['execution_times']['stddev']:.3f}s)")
        
        if not recommendations:
            recommendations.append("- ✅ All tests show good performance characteristics")
            recommendations.append("- ✅ Execution times are within acceptable ranges")
            recommendations.append("- ✅ Memory usage appears efficient")
        
        for rec in recommendations:
            report += rec + "\n"
        
        return report
    
    def save_analysis(self, analysis, report):
        """Save analysis results and report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw analysis data
        analysis_file = self.results_dir.parent / "reports" / f"benchmark_analysis_{timestamp}.json"
        analysis_file.parent.mkdir(exist_ok=True)
        
        with open(analysis_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            analysis_copy = analysis.copy()
            analysis_copy['summary']['test_types'] = list(analysis['summary']['test_types'])
            json.dump(analysis_copy, f, indent=2)
        
        # Save markdown report
        report_file = self.results_dir.parent / "reports" / f"benchmark_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Analysis saved: {analysis_file}")
        print(f"📄 Report saved: {report_file}")
        
        return analysis_file, report_file
    
    def run_analysis(self):
        """Run complete benchmark analysis"""
        print("🔍 Analyzing benchmark results...")
        
        data = self.load_benchmark_data()
        if not data:
            print("⚠️  No benchmark data found")
            return False
        
        analysis = self.analyze_performance_trends(data)
        report = self.generate_performance_report(analysis)
        
        analysis_file, report_file = self.save_analysis(analysis, report)
        
        # Print summary to console
        print("\n" + "="*60)
        print("📈 BENCHMARK ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"Total benchmarks analyzed: {analysis['summary']['total_benchmarks']}")
        print(f"Test types: {len(analysis['summary']['test_types'])}")
        
        if analysis['by_test_type']:
            print("\nPerformance overview:")
            for test_name, metrics in analysis['by_test_type'].items():
                print(f"  {test_name}: {metrics['execution_times']['mean']:.3f}s avg, {metrics['count']} runs")
        
        print(f"\n📄 Full report available at: {report_file}")
        
        return True


def main():
    analyzer = BenchmarkAnalyzer()
    success = analyzer.run_analysis()
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)