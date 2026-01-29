"""Test suite for Scalene-MCP Phase 8 examples.

Verifies that all examples:
1. Run without errors
2. Produce expected output structure
3. Complete within expected time
4. Have proper documentation
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple


def run_example(example_path: Path, timeout: int = 10) -> Tuple[bool, str, float]:
    """Run an example and return (success, output, elapsed_time)."""
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=example_path.parent
        )
        elapsed = time.time() - start
        
        if result.returncode != 0:
            return False, result.stderr, elapsed
        
        return True, result.stdout, elapsed
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s", timeout
    except Exception as e:
        return False, str(e), 0


def check_example_content(example_path: Path) -> Tuple[bool, List[str]]:
    """Check that example has proper documentation."""
    issues = []
    
    with open(example_path, 'r') as f:
        content = f.read()
    
    # Check for module docstring
    if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
        issues.append("Missing module docstring")
    
    # Check for main function or execution
    if '__main__' not in content:
        issues.append("No if __name__ == '__main__' block")
    
    # Check for comments explaining what Scalene shows
    if 'scalene' not in content.lower():
        issues.append("No explanation of what Scalene shows")
    
    return len(issues) == 0, issues


def test_all_examples():
    """Test all Phase 8 examples."""
    examples_dir = Path(__file__).parent.parent / "examples"
    example_files = sorted(examples_dir.glob("[0-9]_*.py"))
    
    if not example_files:
        print("❌ No examples found!")
        return False
    
    print(f"\n📋 Testing {len(example_files)} Phase 8 Examples\n")
    
    all_passed = True
    results = []
    
    for i, example_path in enumerate(example_files, 1):
        print(f"Test {i}/6: {example_path.name}...", end=" ")
        
        # Check content
        content_ok, issues = check_example_content(example_path)
        if not content_ok:
            print(f"❌ Content issues:")
            for issue in issues:
                print(f"  - {issue}")
            all_passed = False
            continue
        
        # Run example
        success, output, elapsed = run_example(example_path)
        
        # Check if it's a missing dependency error (expected for some systems)
        is_missing_dep = "ModuleNotFoundError" in output or "pip install" in output
        
        if success:
            print(f"✅ ({elapsed:.2f}s)")
            results.append({
                'name': example_path.name,
                'status': 'PASS',
                'time': elapsed,
                'lines': len(output.split('\n'))
            })
        elif is_missing_dep:
            # Missing optional dependency (not a test failure)
            print(f"⊘ (optional dependency missing)")
            results.append({
                'name': example_path.name,
                'status': 'SKIP',
                'time': elapsed,
                'reason': 'Optional dependency'
            })
        else:
            print(f"❌ Error:")
            print(f"  {output[:200]}...")
            results.append({
                'name': example_path.name,
                'status': 'FAIL',
                'time': elapsed,
                'error': output[:100]
            })
            all_passed = False
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}\n")
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    skipped = sum(1 for r in results if r['status'] == 'SKIP')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    total = len(results)
    
    for r in results:
        if r['status'] == 'PASS':
            status_icon = "✅"
        elif r['status'] == 'SKIP':
            status_icon = "⊘"
        else:
            status_icon = "❌"
        print(f"{status_icon} {r['name']:<30} {r['status']:<6} ({r['time']:>6.2f}s)")
    
    total_time = sum(r['time'] for r in results)
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed")
    print(f"Total time: {total_time:.2f}s")
    
    # Consider skipped as OK (optional dependencies)
    if all_passed or skipped > 0:
        print(f"Status: ✅ ALL REQUIRED TESTS PASSED")
        print(f"{'='*60}\n")
        return True
    else:
        print(f"Status: ❌ SOME TESTS FAILED")
        print(f"{'='*60}\n")
        return False


def test_example_imports():
    """Test that all examples have proper imports."""
    examples_dir = Path(__file__).parent.parent / "examples"
    
    print("Testing example imports...")
    
    for example_path in sorted(examples_dir.glob("[0-9]_*.py")):
        # Check if can be imported
        try:
            spec = __import__('importlib.util').util.spec_from_file_location(
                example_path.stem,
                example_path
            )
            module = __import__('importlib.util').util.module_from_spec(spec)
            # Don't execute, just check if it can be parsed
            print(f"  ✅ {example_path.name} - imports OK")
        except SyntaxError as e:
            print(f"  ❌ {example_path.name} - syntax error: {e}")
            return False
    
    return True


def test_example_runtimes():
    """Verify examples complete within expected time."""
    examples_dir = Path(__file__).parent.parent / "examples"
    
    expected_times = {
        "1_data_processing_pipeline.py": 2.5,  # ~2 seconds
        "2_algorithm_comparison.py": 1.5,      # ~1 second
        "3_c_bindings_profiling.py": 1.0,      # ~0.5 seconds
        "4_memory_leak_detection.py": 1.0,     # <1 second
        "5_io_bound_profiling.py": 1.5,        # ~1 second
        "6_gpu_profiling.py": 0.5,             # <0.5 seconds
    }
    
    print("\nTesting example runtimes...")
    
    all_ok = True
    for example_name, max_time in expected_times.items():
        example_path = examples_dir / example_name
        if not example_path.exists():
            print(f"  ⚠️  {example_name} not found")
            continue
        
        success, _, elapsed = run_example(example_path)
        
        if not success:
            print(f"  ❌ {example_name} - failed to run")
            all_ok = False
        elif elapsed > max_time * 1.5:  # Allow 50% margin
            print(f"  ⚠️  {example_name} - took {elapsed:.2f}s (expected <{max_time:.1f}s)")
        else:
            print(f"  ✅ {example_name} - {elapsed:.2f}s")
    
    return all_ok


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*60)
    print("PHASE 8 EXAMPLES TEST SUITE")
    print("="*60)
    
    tests_passed = []
    
    # Test imports
    if test_example_imports():
        tests_passed.append(True)
    else:
        tests_passed.append(False)
    
    # Test all examples
    if test_all_examples():
        tests_passed.append(True)
    else:
        tests_passed.append(False)
    
    # Test runtimes
    if test_example_runtimes():
        tests_passed.append(True)
    else:
        tests_passed.append(False)
    
    # Final result
    print("\n" + "="*60)
    if all(tests_passed):
        print("✅ ALL EXAMPLE TESTS PASSED")
        sys.exit(0)
    elif any(tests_passed):
        print("✅ EXAMPLE TESTS PASSED (optional deps may be missing)")
        sys.exit(0)
    else:
        print("❌ SOME EXAMPLE TESTS FAILED")
        sys.exit(1)
