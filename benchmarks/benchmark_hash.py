"""
FoodSafe IEEE Benchmark
Hash Table lookup performance.
"""

import os
import sys
import time

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "backend"
    )
)

from data_structures.hash_table import HashTable


def benchmark(n):
    table = HashTable(max(53, n * 2 + 1))

    # Insert records
    for i in range(n):
        table.insert(
            f"restaurant-{i}",
            {
                "id": i,
                "name": f"Restaurant {i}"
            }
        )

    repetitions = 5000

    start = time.perf_counter()

    for i in range(repetitions):
        key = f"restaurant-{(i * 97) % n}"
        table.search(key)

    elapsed = time.perf_counter() - start

    average_us = (elapsed / repetitions) * 1_000_000

    return average_us


if __name__ == "__main__":

    print("=" * 60)
    print("FoodSafe IEEE Hash Table Benchmark")
    print("=" * 60)

    for n in [100, 1000, 10000, 50000, 100000]:

        result = benchmark(n)

        print(
            f"{n:>7} records | "
            f"Average lookup: {result:.3f} microseconds"
        )