"""
Example 2: Algorithm Comparison

Real-world scenario: A developer is implementing a feature and has two different
approaches. They want to compare which one performs better.

Use case: Profile both implementations and compare with Scalene-MCP.
"""

import time
from typing import List


def algorithm_a_bubble_sort(arr: List[int]) -> List[int]:
    """Bubble sort - O(n²) but simple."""
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def algorithm_b_quick_sort(arr: List[int]) -> List[int]:
    """Quick sort - O(n log n) average case."""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return algorithm_b_quick_sort(left) + middle + algorithm_b_quick_sort(right)


def algorithm_c_python_sorted(arr: List[int]) -> List[int]:
    """Python's built-in sorted (C implementation, Timsort)."""
    return sorted(arr)


def run_comparison():
    """Compare all three algorithms."""
    import random
    import numpy as np
    
    # Generate test data - not too large to avoid excessive runtime
    np.random.seed(42)
    test_array = list(np.random.randint(0, 1000, 500))
    
    print("=" * 50)
    print("Algorithm Comparison (Sorting)")
    print("=" * 50)
    
    # Algorithm A: Bubble Sort
    print("\nAlgorithm A: Bubble Sort (O(n²))")
    result_a = algorithm_a_bubble_sort(test_array)
    print(f"  Result: {result_a[:10]}... (sorted: {result_a == sorted(test_array)})")
    
    # Algorithm B: Quick Sort
    print("\nAlgorithm B: Quick Sort (O(n log n) avg)")
    result_b = algorithm_b_quick_sort(test_array)
    print(f"  Result: {result_b[:10]}... (sorted: {result_b == sorted(test_array)})")
    
    # Algorithm C: Python sorted (C/Timsort)
    print("\nAlgorithm C: Python sorted() (C/Timsort - O(n log n))")
    result_c = algorithm_c_python_sorted(test_array)
    print(f"  Result: {result_c[:10]}... (sorted: {result_c == sorted(test_array)})")
    
    print("\n" + "=" * 50)
    print("Run this with Scalene-MCP to see which is fastest!")
    print("Profile it: python -m scalene examples/2_algorithm_comparison.py")
    print("=" * 50)
    
    return {
        'bubble_sort': result_a,
        'quick_sort': result_b,
        'python_sorted': result_c
    }


if __name__ == "__main__":
    results = run_comparison()
