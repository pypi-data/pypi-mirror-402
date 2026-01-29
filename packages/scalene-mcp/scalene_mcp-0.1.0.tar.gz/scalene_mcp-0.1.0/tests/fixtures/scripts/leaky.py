"""Script with intentional memory leak."""

import time

# Global list that continuously grows
leaked_memory: list[bytes] = []


def leak_memory() -> None:
    """Continuously allocate memory without releasing."""
    for _ in range(100):
        # Allocate 1MB chunks
        leaked_memory.append(b"x" * (1024 * 1024))
        time.sleep(0.01)


def main() -> None:
    """Main function."""
    print("Starting memory leak...")
    leak_memory()
    print(f"Leaked {len(leaked_memory)} MB")


if __name__ == "__main__":
    main()
