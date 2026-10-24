"""
FoodSafe IEEE Reproducible Benchmark Report

Generates:
    benchmark_results.csv
"""

import csv
import os

from benchmark_hash import benchmark as hash_benchmark
from benchmark_heap import benchmark as heap_benchmark
from benchmark_priority_queue import benchmark as pq_benchmark


BASE = os.path.dirname(
    os.path.abspath(__file__)
)

OUTPUT = os.path.join(
    BASE,
    "benchmark_results.csv"
)


def main():

    rows = []

    # =====================================================
    # HASH TABLE
    # =====================================================

    print("Running Hash Table benchmarks...")

    for n in [
        100,
        1000,
        10000,
        50000,
        100000
    ]:

        value = hash_benchmark(n)

        rows.append([
            "Hash Table",
            n,
            "Average Lookup",
            value,
            "microseconds"
        ])

    # =====================================================
    # MIN HEAP
    # =====================================================

    print("Running Min Heap benchmarks...")

    for n in [
        100,
        1000,
        5000,
        10000,
        20000
    ]:

        result = heap_benchmark(n)

        rows.append([
            "Min Heap",
            n,
            "Linear Scan",
            result["linear_scan_ms"],
            "milliseconds"
        ])

        rows.append([
            "Min Heap",
            n,
            "Re-sort",
            result["resort_ms"],
            "milliseconds"
        ])

        rows.append([
            "Min Heap",
            n,
            "Min Heap",
            result["min_heap_ms"],
            "milliseconds"
        ])

    # =====================================================
    # PRIORITY QUEUE
    # =====================================================

    print("Running Priority Queue benchmarks...")

    for n in [
        100,
        1000,
        5000,
        10000,
        20000
    ]:

        result = pq_benchmark(n)

        rows.append([
            "Priority Queue",
            n,
            "FIFO High Priority Position",
            result["fifo_high_position"],
            "position"
        ])

        rows.append([
            "Priority Queue",
            n,
            "PQ High Priority Position",
            result["pq_high_position"],
            "position"
        ])

        rows.append([
            "Priority Queue",
            n,
            "Position Improvement",
            result["position_improvement_percent"],
            "percent"
        ])

    # =====================================================
    # WRITE CSV
    # =====================================================

    with open(
        OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Structure",
            "Records",
            "Metric",
            "Value",
            "Unit"
        ])

        writer.writerows(rows)

    # =====================================================
    # RESULT
    # =====================================================

    print()
    print("=" * 60)
    print("FoodSafe IEEE Benchmark Report")
    print("=" * 60)

    print()
    print(
        f"Results saved to:\n{OUTPUT}"
    )

    print()
    print(
        f"Total measurements: {len(rows)}"
    )


if __name__ == "__main__":
    main()