"""
Example 3: C Bindings Profiling

Real-world scenario: A developer uses libraries with C/C++ bindings (NumPy, etc.)
and wants to understand whether their code is spending time in Python or C code.

Scalene shows "C time" separately from "Python time", so you can see:
- How much time is spent in Python
- How much time is spent in C extensions
- Where to focus optimization efforts

Use case: Understand the breakdown of Python vs C time.

Requirement: numpy (pip install numpy)
"""

import numpy as np
from typing import List


def pure_python_sum(arr: List[int]) -> int:
    """Pure Python sum - shows up as Python time."""
    total = 0
    for value in arr:
        total += value
    return total


def numpy_sum(arr: np.ndarray) -> int:
    """NumPy sum - shows up as C time (NumPy is implemented in C)."""
    return np.sum(arr)


def pure_python_mean(arr: List[float]) -> float:
    """Pure Python mean calculation - Python time."""
    total = 0
    for value in arr:
        total += value
    return total / len(arr)


def numpy_mean(arr: np.ndarray) -> float:
    """NumPy mean - C time (vectorized C code)."""
    return np.mean(arr)


def mixed_operations():
    """Mix of Python and C operations."""
    # Generate test data
    np.random.seed(42)
    data = np.random.randn(10000)
    
    print("="*60)
    print("C Bindings Profiling: Python vs C time")
    print("="*60)
    
    # Operation 1: Pure Python
    print("\n1. Pure Python Operations (should show as Python time)")
    python_list = list(range(1000))
    result1 = pure_python_sum(python_list)
    print(f"   Pure Python sum: {result1}")
    
    # Operation 2: NumPy (C bindings)
    print("\n2. NumPy Operations (should show as C time)")
    numpy_array = np.array(range(1000))
    result2 = numpy_sum(numpy_array)
    print(f"   NumPy sum: {result2}")
    
    # Operation 3: Python mean calculation
    print("\n3. Pure Python Mean Calculation (Python time)")
    python_floats = [float(x) for x in range(1000)]
    mean_python = pure_python_mean(python_floats)
    print(f"   Python mean: {mean_python:.4f}")
    
    # Operation 4: NumPy mean
    print("\n4. NumPy Mean (C time)")
    numpy_floats = np.array(range(1000), dtype=float)
    mean_numpy = numpy_mean(numpy_floats)
    print(f"   NumPy mean: {mean_numpy:.4f}")
    
    # Operation 5: NumPy vectorized math operations
    print("\n5. NumPy Math Operations (C time)")
    large_array = np.random.randn(5000)
    squared = large_array ** 2  # C time
    sin_vals = np.sin(large_array)  # C time
    exp_vals = np.exp(large_array)  # C time
    print(f"   Math operations complete")
    print(f"   Mean of squared: {np.mean(squared):.4f}")
    
    # Operation 6: NumPy statistical operations
    print("\n6. NumPy Statistical Operations (C time)")
    stats_array = np.random.randn(1000)
    std_val = np.std(stats_array)  # C time
    var_val = np.var(stats_array)  # C time
    max_val = np.max(stats_array)  # C time
    print(f"   Std: {std_val:.4f}, Var: {var_val:.4f}, Max: {max_val:.4f}")
    
    print("\n" + "="*60)
    print("When you profile this with Scalene-MCP:")
    print("  - Python time: Pure Python code (for loops, etc.)")
    print("  - C time: NumPy and other C extensions")
    print("  - System time: I/O operations, system calls")
    print("\nNotice: Operations 2, 4, 5, 6 are C time (NumPy)")
    print("        Operations 1, 3 are Python time (pure loops)")
    print("\nThis shows you where to focus optimization!")
    print("="*60)
    
    return {
        'pure_python_sum': result1,
        'numpy_sum': result2,
        'python_mean': mean_python,
        'numpy_mean': mean_numpy
    }


if __name__ == "__main__":
    results = mixed_operations()
