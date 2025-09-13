"""
Performance Benchmarking Tests for Causal Memory Core
Tests functionality while collecting detailed performance statistics
"""

import pytest
import tempfile
import os
import time
import sys
import json
import psutil
import gc
from datetime import datetime, timezone
from statistics import mean, median, stdev
from unittest.mock import Mock, patch
from contextlib import contextmanager

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from causal_memory_core import CausalMemoryCore


class PerformanceBenchmarks:
    """Performance benchmarking utilities"""
    
    @contextmanager
    def benchmark_context(self, test_name):
        """Context manager to collect performance metrics during test execution"""
        # Start metrics collection
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu_percent = psutil.cpu_percent()
        
        # Force garbage collection for clean measurement
        gc.collect()
        
        metrics = {
            'test_name': test_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'start_time': start_time,
            'start_memory_mb': start_memory,
            'start_cpu_percent': start_cpu_percent
        }
        
        try:
            yield metrics
        finally:
            # End metrics collection
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu_percent = psutil.cpu_percent()
            
            metrics.update({
                'end_time': end_time,
                'execution_time_seconds': end_time - start_time,
                'end_memory_mb': end_memory,
                'memory_delta_mb': end_memory - start_memory,
                'end_cpu_percent': end_cpu_percent,
                'cpu_delta_percent': end_cpu_percent - start_cpu_percent
            })
            
            # Save benchmark data
            self.save_benchmark_result(metrics)
    
    def save_benchmark_result(self, metrics):
        """Save benchmark results to file"""
        results_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_results', 'benchmarks')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metrics['test_name']}_{timestamp}.json"
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Also append to daily summary
        daily_file = os.path.join(results_dir, f"daily_benchmarks_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(daily_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')


class TestPerformanceBenchmarks:
    """Performance benchmark tests for Causal Memory Core"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db.name
        temp_db.close()
        os.unlink(temp_db_path)  # Let DuckDB create the file
        yield temp_db_path
        # Cleanup - try multiple times if file is locked
        for attempt in range(3):
            try:
                if os.path.exists(temp_db_path):
                    os.unlink(temp_db_path)
                break
            except (PermissionError, OSError):
                time.sleep(0.1)  # Wait briefly and try again
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for consistent performance testing"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The user action caused the system response."
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def mock_embedder(self):
        """Mock sentence transformer for consistent performance testing"""
        import numpy as np
        mock_embedder = Mock()
        mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        return mock_embedder
    
    @pytest.fixture
    def benchmarker(self):
        """Performance benchmarking utilities"""
        return PerformanceBenchmarks()
    
    def test_benchmark_single_event_performance(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark single event addition performance"""
        with benchmarker.benchmark_context('single_event_performance') as metrics:
            memory_core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
            
            # Measure individual operations
            operations = []
            
            # Test adding single event
            start_op = time.time()
            memory_core.add_event("User clicked the save button")
            operations.append({
                'operation': 'add_event',
                'duration': time.time() - start_op
            })
            
            # Test querying
            start_op = time.time()
            context = memory_core.get_context("save button click")
            operations.append({
                'operation': 'get_context', 
                'duration': time.time() - start_op,
                'context_length': len(context)
            })
            
            memory_core.close()
            
            metrics['operations'] = operations
            metrics['total_operations'] = len(operations)
        
        # Verify functionality
        assert context != "No relevant context found in memory."
    
    def test_benchmark_bulk_event_performance(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark bulk event addition performance"""
        event_counts = [10, 50, 100, 500]
        
        for count in event_counts:
            test_name = f'bulk_events_{count}'
            
            with benchmarker.benchmark_context(test_name) as metrics:
                memory_core = CausalMemoryCore(
                    db_path=temp_db_path,
                    llm_client=mock_openai_client,
                    embedding_model=mock_embedder
                )
                
                # Measure bulk addition
                events = [f"User performed action {i} in the workflow" for i in range(count)]
                
                add_times = []
                start_bulk = time.time()
                
                for i, event in enumerate(events):
                    start_single = time.time()
                    memory_core.add_event(event)
                    add_times.append(time.time() - start_single)
                    
                    if i % 10 == 0:  # Small delay every 10 events for realistic timing
                        time.sleep(0.001)
                
                bulk_duration = time.time() - start_bulk
                
                # Test query performance with many events
                query_start = time.time()
                context = memory_core.get_context("workflow actions")
                query_duration = time.time() - query_start
                
                memory_core.close()
                
                # Calculate statistics
                metrics['event_count'] = count
                metrics['bulk_add_duration'] = bulk_duration
                metrics['average_add_time'] = mean(add_times)
                metrics['median_add_time'] = median(add_times)
                metrics['stddev_add_time'] = stdev(add_times) if len(add_times) > 1 else 0
                metrics['min_add_time'] = min(add_times)
                metrics['max_add_time'] = max(add_times)
                metrics['query_duration'] = query_duration
                metrics['context_length'] = len(context)
                metrics['events_per_second'] = count / bulk_duration if bulk_duration > 0 else 0
        
        # Verify functionality
        assert context != "No relevant context found in memory."
    
    def test_benchmark_memory_scaling(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark memory usage scaling with event count"""
        with benchmarker.benchmark_context('memory_scaling') as metrics:
            memory_core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
            
            memory_samples = []
            event_counts = [0, 10, 25, 50, 100, 200]
            
            for count in event_counts:
                # Add events to reach target count
                current_count = len(memory_samples)
                events_to_add = count - current_count
                
                for i in range(events_to_add):
                    memory_core.add_event(f"Scaling test event {current_count + i}")
                
                # Sample memory usage
                gc.collect()  # Force garbage collection for accurate measurement
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                memory_samples.append({
                    'event_count': count,
                    'memory_mb': memory_usage,
                    'db_file_size': os.path.getsize(temp_db_path) if os.path.exists(temp_db_path) else 0
                })
                
                time.sleep(0.1)  # Brief pause between measurements
            
            memory_core.close()
            
            metrics['memory_scaling_data'] = memory_samples
            metrics['max_memory_mb'] = max(sample['memory_mb'] for sample in memory_samples)
            metrics['memory_growth_rate'] = (memory_samples[-1]['memory_mb'] - memory_samples[0]['memory_mb']) / event_counts[-1] if event_counts[-1] > 0 else 0
    
    def test_benchmark_query_performance(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark query performance with different context sizes"""
        with benchmarker.benchmark_context('query_performance') as metrics:
            memory_core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
            
            # Populate with test events
            test_events = [
                "User opened the application",
                "Application loaded successfully", 
                "User clicked on file menu",
                "File menu opened with options",
                "User selected new document",
                "New document was created",
                "User typed document title",
                "Title appeared in document",
                "User saved the document",
                "Document was saved to disk"
            ]
            
            for event in test_events:
                memory_core.add_event(event)
                time.sleep(0.01)  # Small delay for realistic timestamps
            
            # Test different query types
            queries = [
                "application startup",
                "file operations", 
                "document creation",
                "user interactions",
                "very specific query that might not match anything"
            ]
            
            query_results = []
            
            for query in queries:
                start_time = time.time()
                context = memory_core.get_context(query)
                duration = time.time() - start_time
                
                query_results.append({
                    'query': query,
                    'duration': duration,
                    'context_length': len(context),
                    'has_context': context != "No relevant context found in memory."
                })
            
            memory_core.close()
            
            metrics['query_results'] = query_results
            metrics['average_query_time'] = mean(result['duration'] for result in query_results)
            metrics['successful_queries'] = sum(1 for result in query_results if result['has_context'])
            metrics['query_success_rate'] = metrics['successful_queries'] / len(queries)
    
    def test_benchmark_database_operations(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark database operation performance"""
        with benchmarker.benchmark_context('database_operations') as metrics:
            # Test initialization time
            init_start = time.time()
            memory_core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
            init_time = time.time() - init_start
            
            # Test database writing performance
            write_times = []
            for i in range(20):
                start_write = time.time()
                memory_core.add_event(f"Database performance test event {i}")
                write_times.append(time.time() - start_write)
            
            # Test database reading performance
            read_times = []
            for i in range(10):
                start_read = time.time()
                context = memory_core.get_context(f"performance test {i}")
                read_times.append(time.time() - start_read)
            
            # Test close operation
            close_start = time.time()
            memory_core.close()
            close_time = time.time() - close_start
            
            metrics['initialization_time'] = init_time
            metrics['average_write_time'] = mean(write_times)
            metrics['average_read_time'] = mean(read_times)
            metrics['close_time'] = close_time
            metrics['total_write_operations'] = len(write_times)
            metrics['total_read_operations'] = len(read_times)
            metrics['db_file_size_final'] = os.path.getsize(temp_db_path) if os.path.exists(temp_db_path) else 0
    
    def test_benchmark_concurrent_operations(self, temp_db_path, mock_openai_client, mock_embedder, benchmarker):
        """Benchmark concurrent operation handling"""
        with benchmarker.benchmark_context('concurrent_operations') as metrics:
            memory_core = CausalMemoryCore(
                db_path=temp_db_path,
                llm_client=mock_openai_client,
                embedding_model=mock_embedder
            )
            
            # Simulate concurrent-like operations by rapidly adding events and querying
            operations = []
            start_concurrent = time.time()
            
            for i in range(50):
                # Add event
                add_start = time.time()
                memory_core.add_event(f"Concurrent test event {i}")
                add_time = time.time() - add_start
                
                operations.append({'type': 'add', 'duration': add_time, 'index': i})
                
                # Every 5th operation, also do a query
                if i % 5 == 0:
                    query_start = time.time()
                    context = memory_core.get_context(f"concurrent test {i}")
                    query_time = time.time() - query_start
                    
                    operations.append({
                        'type': 'query', 
                        'duration': query_time, 
                        'index': i,
                        'context_found': context != "No relevant context found in memory."
                    })
            
            total_concurrent_time = time.time() - start_concurrent
            memory_core.close()
            
            # Analyze operations
            add_ops = [op for op in operations if op['type'] == 'add']
            query_ops = [op for op in operations if op['type'] == 'query']
            
            metrics['total_concurrent_time'] = total_concurrent_time
            metrics['total_operations'] = len(operations)
            metrics['add_operations'] = len(add_ops)
            metrics['query_operations'] = len(query_ops)
            metrics['operations_per_second'] = len(operations) / total_concurrent_time if total_concurrent_time > 0 else 0
            metrics['average_add_time'] = mean(op['duration'] for op in add_ops) if add_ops else 0
            metrics['average_query_time'] = mean(op['duration'] for op in query_ops) if query_ops else 0
            metrics['successful_queries'] = sum(1 for op in query_ops if op.get('context_found', False))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])