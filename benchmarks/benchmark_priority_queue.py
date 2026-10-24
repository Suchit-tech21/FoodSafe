"""
IEEE FoodSafe Benchmark
Priority Queue complaint processing.

Measures how quickly high-priority complaints
appear near the front of the processing order.
"""

import os
import sys
import time
import random

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "backend"
    )
)

from data_structures.priority_queue import PriorityQueue


def generate_complaints(n):

    random.seed(42)

    complaints = []

    for i in range(n):

        score = random.randint(
            1,
            100
        )

        complaints.append({
            "id": i,
            "priority_score": score
        })

    return complaints


def priority_queue_order(complaints):

    queue = PriorityQueue()

    for complaint in complaints:

        queue.push(
            complaint["priority_score"],
            complaint
        )

    return queue.ordered()


def fifo_order(complaints):

    return list(complaints)


def average_high_position(items):

    high_positions = []

    for position, item in enumerate(items):

        score = item.get(
            "priority_score",
            0
        )

        if score >= 70:

            high_positions.append(
                position + 1
            )

    if not high_positions:

        return 0

    return (
        sum(high_positions)
        / len(high_positions)
    )


def benchmark(n):

    complaints = generate_complaints(n)

    # FIFO baseline
    start = time.perf_counter()

    fifo = fifo_order(
        complaints
    )

    fifo_time = (
        time.perf_counter()
        - start
    ) * 1000

    fifo_position = (
        average_high_position(
            fifo
        )
    )

    # Priority Queue
    start = time.perf_counter()

    pq = priority_queue_order(
        complaints
    )

    pq_time = (
        time.perf_counter()
        - start
    ) * 1000

    pq_position = (
        average_high_position(
            pq
        )
    )

    if fifo_position:

        improvement = (
            1
            - (
                pq_position
                / fifo_position
            )
        ) * 100

    else:

        improvement = 0

    return {
        "records": n,
        "fifo_ms": fifo_time,
        "priority_queue_ms": pq_time,
        "fifo_high_position": fifo_position,
        "pq_high_position": pq_position,
        "position_improvement_percent":
            improvement
    }


if __name__ == "__main__":

    print("=" * 80)
    print("FoodSafe IEEE Priority Queue Benchmark")
    print("=" * 80)

    for n in [
        100,
        1000,
        5000,
        10000,
        20000
    ]:

        result = benchmark(n)

        print(
            f"{n:>7} complaints | "
            f"FIFO high position: "
            f"{result['fifo_high_position']:.2f} | "
            f"PQ high position: "
            f"{result['pq_high_position']:.2f} | "
            f"Improvement: "
            f"{result['position_improvement_percent']:.2f}%"
        )