"""
Example 5: I/O Bound Code Profiling

Real-world scenario: A web scraper, API client, or file processor spends time
waiting for I/O. You want to see how much time is waiting vs processing.

Use case: Identify I/O bottlenecks and understand async opportunities.
"""

import time
import json
from pathlib import Path
from typing import List, Dict


def simulate_network_request(delay: float = 0.01) -> str:
    """Simulate a network request with latency."""
    time.sleep(delay)  # Simulate network delay
    return json.dumps({"status": "success", "data": "response"})


def slow_sequential_processing() -> List[Dict]:
    """Slow: Process requests sequentially - waits for each one."""
    results = []
    for i in range(10):
        # Each request waits for network delay
        response = simulate_network_request(delay=0.01)
        data = json.loads(response)
        results.append(data)
    return results


def optimized_batch_processing() -> List[Dict]:
    """Better: Batch multiple requests and process in parallel."""
    # Note: In real code, you'd use asyncio or ThreadPoolExecutor
    # This example shows the difference in pure Python
    results = []
    
    # Simulate batch processing - fewer waits
    for batch_start in range(0, 10, 2):
        batch = []
        for i in range(batch_start, min(batch_start + 2, 10)):
            batch.append(i)
        
        # Process batch
        for idx in batch:
            response = simulate_network_request(delay=0.01)
            data = json.loads(response)
            results.append(data)
    
    return results


def file_io_operations():
    """Demonstrate file I/O profiling."""
    # Create temporary test data
    temp_file = Path("/tmp/scalene_example.json")
    
    test_data = {
        f"key_{i}": {"value": i, "data": f"test_data_{i}" * 10}
        for i in range(100)
    }
    
    # Write to file
    with open(temp_file, 'w') as f:
        json.dump(test_data, f)
    
    # Read from file
    with open(temp_file, 'r') as f:
        loaded_data = json.load(f)
    
    # Process data
    processed = {k: v['value'] * 2 for k, v in loaded_data.items()}
    
    # Cleanup
    temp_file.unlink()
    
    return processed


def main():
    """Run I/O profiling examples."""
    print("="*60)
    print("I/O Bound Code Profiling")
    print("="*60)
    
    print("\nSequential Processing (waits for each request)...")
    results_seq = slow_sequential_processing()
    print(f"  Completed: {len(results_seq)} requests")
    
    print("\nBatch Processing (some parallelization)...")
    results_batch = optimized_batch_processing()
    print(f"  Completed: {len(results_batch)} requests")
    
    print("\nFile I/O Operations...")
    processed = file_io_operations()
    print(f"  Processed: {len(processed)} items")
    
    print("\n" + "="*60)
    print("When you profile this with Scalene-MCP:")
    print("  - Most time is in time.sleep() (simulated network)")
    print("  - File I/O operations show system time")
    print("  - See breakdown: Python vs system time")
    print("  - Identify where to add async/parallel processing")
    print("="*60)


if __name__ == "__main__":
    main()
