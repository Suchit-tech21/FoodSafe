import time
import random
import heapq


def generate_inventory(n):
    random.seed(42)

    return [
        {
            "id": i,
            "expiry": random.randint(1, 1_000_000)
        }
        for i in range(n)
    ]


def benchmark(n, repeats=100):
    data = generate_inventory(n)

    # -----------------------------
    # Linear Scan
    # -----------------------------
    start = time.perf_counter()

    for _ in range(repeats):
        min(data, key=lambda x: x["expiry"])

    linear_scan_ms = (
        (time.perf_counter() - start) * 1000 / repeats
    )

    # -----------------------------
    # Re-sort
    # -----------------------------
    start = time.perf_counter()

    for _ in range(repeats):
        sorted(data, key=lambda x: x["expiry"])[0]

    resort_ms = (
        (time.perf_counter() - start) * 1000 / repeats
    )

    # -----------------------------
    # Min Heap
    # Build once, retrieve minimum
    # -----------------------------
    heap = [
        (item["expiry"], item["id"])
        for item in data
    ]

    heapq.heapify(heap)

    start = time.perf_counter()

    for _ in range(repeats):
        heap[0]

    min_heap_ms = (
        (time.perf_counter() - start) * 1000 / repeats
    )

    return {
        "n": n,
        "linear_scan_ms": linear_scan_ms,
        "resort_ms": resort_ms,
        "min_heap_ms": min_heap_ms
    }


if __name__ == "__main__":
    for n in [100, 1000, 5000, 10000, 20000]:
        result = benchmark(n)

        print(
            f"{n}: "
            f"Linear={result['linear_scan_ms']:.6f} ms, "
            f"Re-sort={result['resort_ms']:.6f} ms, "
            f"Min Heap={result['min_heap_ms']:.6f} ms"
        )