"""
Example 6: GPU Profiling (Optional - requires GPU hardware)

Real-world scenario: A machine learning engineer uses GPU libraries like PyTorch
or TensorFlow and wants to understand how much time is spent on GPU vs CPU.

Use case: Identify GPU bottlenecks and optimization opportunities.

Note: This example requires a GPU. It's safe to run on CPU - it will just show
minimal GPU time. The example is included for teams with GPU hardware.
"""

import numpy as np


def cpu_matrix_multiply(size: int = 100) -> np.ndarray:
    """Pure CPU matrix multiplication using NumPy."""
    a = np.random.randn(size, size)
    b = np.random.randn(size, size)
    # np.dot uses BLAS (optimized C code) but runs on CPU
    result = np.dot(a, b)
    return result


def demonstrate_gpu_potential():
    """
    Show where GPU could help.
    
    Note: This doesn't actually use GPU without PyTorch/TensorFlow installed.
    It's here to show the pattern.
    """
    print("="*60)
    print("GPU Profiling Example")
    print("="*60)
    
    print("\n1. CPU Matrix Multiplication")
    result = cpu_matrix_multiply(size=100)
    print(f"   Shape: {result.shape}")
    
    # Demonstrate the pattern (without actual GPU code)
    print("\n2. Pattern for GPU profiling with PyTorch:")
    print("""
    # If you had PyTorch:
    import torch
    
    # CPU computation
    cpu_tensor = torch.randn(100, 100)
    cpu_result = torch.mm(cpu_tensor, cpu_tensor)
    
    # GPU computation (if available)
    if torch.cuda.is_available():
        gpu_tensor = torch.randn(100, 100, device='cuda')
        gpu_result = torch.mm(gpu_tensor, gpu_tensor)
    
    # Scalene would show:
    # - Python time: Control flow, setup
    # - C time: NumPy/torch CPU operations  
    # - GPU time: Computation on GPU (if you have GPU monitoring)
    """)
    
    print("\n3. Pattern for GPU profiling with TensorFlow:")
    print("""
    # If you had TensorFlow:
    import tensorflow as tf
    
    @tf.function  # Compile to GPU
    def gpu_computation():
        a = tf.random.normal((100, 100))
        b = tf.random.normal((100, 100))
        return tf.matmul(a, b)
    
    result = gpu_computation()
    
    # Scalene shows time breakdown between Python, C, and GPU
    """)
    
    print("\n" + "="*60)
    print("GPU Profiling Benefits:")
    print("  - See CPU vs GPU time split")
    print("  - Identify if GPU is utilized")
    print("  - Find bottlenecks (CPU waiting for GPU, etc.)")
    print("  - Optimize data transfer between CPU/GPU")
    print("="*60)
    
    print("\nTo enable GPU profiling:")
    print("  - Install NVIDIA drivers (for NVIDIA GPU)")
    print("  - Profile with: python -m scalene --gpu examples/6_gpu_profiling.py")
    print("\nNote: Requires NVIDIA GPU support. CPU fallback is safe.")


if __name__ == "__main__":
    demonstrate_gpu_potential()
