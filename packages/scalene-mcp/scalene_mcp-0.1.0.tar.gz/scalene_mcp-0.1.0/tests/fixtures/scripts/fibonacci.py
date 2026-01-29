"""Fibonacci calculation - simple CPU test."""


def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def main() -> None:
    """Main function."""
    result = fibonacci(30)
    print(f"fibonacci(30) = {result}")


if __name__ == "__main__":
    main()
