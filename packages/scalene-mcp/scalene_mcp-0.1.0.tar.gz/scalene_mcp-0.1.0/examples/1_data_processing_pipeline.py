"""
Example 1: Data Processing Pipeline Optimization

Real-world scenario: A data scientist has a data processing pipeline that's slow.
They need to identify whether the bottleneck is in Python code or C bindings (NumPy).

Use case: Run with Scalene-MCP to profile and optimize.

What Scalene shows:
- slow_python_processing() uses Python loops → high Python time
- fast_vectorized_processing() uses NumPy → high C time (NumPy is in C)
- This teaches you where to focus optimization efforts

Requirement: numpy (pip install numpy)
"""

import numpy as np
import time


def load_data(rows: int = 10000) -> dict:
    """Simulate loading raw data from source (CSV, database, etc.)."""
    np.random.seed(42)
    return {
        'id': np.arange(rows),
        'value': np.random.randn(rows),
        'category': np.random.choice(['A', 'B', 'C'], rows),
    }


def slow_python_processing(data: dict) -> list:
    """Inefficient Python-based processing (the bottleneck we want to find)."""
    # Bad: Using Python loops instead of vectorized operations
    result = []
    for i in range(len(data['id'])):
        # Expensive: Converting each value using Python
        normalized = float(data['value'][i]) / 100.0
        squared = normalized ** 2
        categorized = data['category'][i].lower()
        result.append({
            'id': int(data['id'][i]),
            'normalized': normalized,
            'squared': squared,
            'category': categorized
        })
    return result


def fast_vectorized_processing(data: dict) -> dict:
    """Efficient vectorized processing using NumPy (C bindings)."""
    # Good: Using NumPy vectorized operations (C implementation)
    # This is much faster because NumPy operations run in C, not Python
    normalized = data['value'] / 100.0  # NumPy: vectorized division
    squared = normalized ** 2  # NumPy: vectorized power
    
    # Convert categories to lowercase
    categories = np.array([c.lower() for c in data['category']])
    
    return {
        'id': data['id'],
        'normalized': normalized,
        'squared': squared,
        'category': categories
    }


def aggregate_results(processed: dict) -> dict:
    """Aggregate results for reporting using NumPy."""
    normalized = processed['normalized']
    squared = processed['squared']
    
    return {
        'mean_value': float(np.mean(normalized)),
        'std_value': float(np.std(normalized)),
        'max_squared': float(np.max(squared)),
        'min_normalized': float(np.min(normalized)),
    }


def main():
    """Main pipeline - demonstrates slow vs fast processing."""
    print("Loading data...")
    data = load_data(5000)
    
    print("\nTiming slow Python processing...")
    start = time.time()
    processed_slow = slow_python_processing(data)
    slow_time = time.time() - start
    
    print(f"Slow processing took {slow_time:.3f}s")
    
    print("\nTiming fast vectorized processing...")
    start = time.time()
    processed_fast = fast_vectorized_processing(data)
    fast_time = time.time() - start
    
    print(f"Fast processing took {fast_time:.3f}s")
    print(f"Speedup: {slow_time/fast_time:.1f}x faster!")
    
    print("\nAggregating results...")
    results = aggregate_results(processed_fast)
    
    print(f"Results: {results}")
    return results


if __name__ == "__main__":
    main()
