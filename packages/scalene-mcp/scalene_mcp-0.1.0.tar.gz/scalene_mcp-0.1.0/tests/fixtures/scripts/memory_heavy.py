"""Memory-intensive operations test."""


def allocate_large_list() -> list[int]:
    """Allocate a large list."""
    return [i for i in range(10_000_000)]


def process_data(data: list[int]) -> int:
    """Process large data structure."""
    total = sum(x * 2 for x in data)
    return total


def main() -> None:
    """Main function."""
    print("Allocating large list...")
    data = allocate_large_list()

    print("Processing data...")
    result = process_data(data)

    print(f"Result: {result}")


if __name__ == "__main__":
    main()
