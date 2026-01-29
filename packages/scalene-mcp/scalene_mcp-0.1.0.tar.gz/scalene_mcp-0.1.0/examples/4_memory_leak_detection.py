"""
Example 4: Memory Leak Detection

Real-world scenario: A long-running web service is slowly consuming more memory.
You need to identify where the memory is being allocated.

Use case: Detect memory leaks with allocation velocity metrics.
"""

from typing import List, Dict


def simulate_memory_leak():
    """Simulates a memory leak pattern."""
    cache = {}  # Global cache that grows without bound
    
    def add_to_cache(key: str, data: str):
        """This function has a memory leak - cache never gets cleared."""
        cache[key] = data * 1000  # Store large string
    
    # Simulate request processing (like in a web service)
    for i in range(1000):
        request_id = f"request_{i}"
        request_data = f"Data for request {i}"
        add_to_cache(request_id, request_data)
    
    return cache


def healthy_memory_usage():
    """Proper memory management with cleanup."""
    results = {}
    
    def process_request(request_id: int):
        """Process request and clean up after."""
        # Store data temporarily
        request_data = {"id": request_id, "data": f"Request {request_id}" * 100}
        results[request_id] = request_data
        return request_data
    
    # Process requests
    for i in range(1000):
        data = process_request(i)
        # Explicitly clean up old entries
        if i > 100 and (i - 100) in results:
            del results[i - 100]
    
    return results


def main():
    """Run both patterns so profiler can see the difference."""
    print("="*60)
    print("Memory Leak Detection Example")
    print("="*60)
    
    print("\nRunning healthy memory usage pattern...")
    healthy_result = healthy_memory_usage()
    print(f"  Healthy: {len(healthy_result)} items in results")
    
    print("\nRunning memory leak pattern...")
    leak_result = simulate_memory_leak()
    print(f"  Leak: {len(leak_result)} items in cache")
    
    print("\n" + "="*60)
    print("When you profile this with Scalene-MCP:")
    print("  - Look at memory allocation per line")
    print("  - Use get_memory_leaks() to find allocation velocity")
    print("  - Lines with high velocity = potential leaks")
    print("="*60)


if __name__ == "__main__":
    main()
