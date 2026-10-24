"""Web-facing Data Structures integration layer.

These structures are rebuilt from persistent SQLite records per request so the
web application uses real DS operations without making the database depend on
process memory.
"""

from .hash_table import HashTable
from .linked_list import LinkedList
from .min_heap import MinHeap
from .priority_queue import PriorityQueue
from .sorting import merge_sort
from .searching import binary_search


def restaurant_index(restaurants):
    """Build Hash Table and Linked List indexes for restaurants."""

    ht = HashTable(
        max(
            53,
            len(restaurants) * 2 + 1
        )
    )

    ll = LinkedList()

    for r in restaurants:

        item = dict(r)

        # Hash Table:
        # Restaurant ID
        ht.insert(
            str(item['id']),
            item
        )

        # Hash Table:
        # Restaurant name
        ht.insert(
            item['name'].strip().lower(),
            item
        )

        # Linked List
        ll.append(item)

    return ht, ll


def search_restaurants(restaurants, query=''):
    """
    Search restaurants using the data-structure pipeline:

    1. Hash Table exact lookup
    2. Binary Search exact lookup
    3. Partial search
    4. Merge Sort for deterministic results
    """

    # ---------------------------------------------------------
    # HASH TABLE
    # ---------------------------------------------------------

    ht, _ = restaurant_index(restaurants)

    q = (
        query or ''
    ).strip().lower()

    # ---------------------------------------------------------
    # EMPTY SEARCH
    # ---------------------------------------------------------

    if not q:

        return merge_sort(
            restaurants,
            key=lambda x:
                x['name'].lower()
        )

    # ---------------------------------------------------------
    # HASH TABLE EXACT SEARCH
    # ---------------------------------------------------------

    exact = ht.search(q)

    if exact:

        return [exact]

    # ---------------------------------------------------------
    # BINARY SEARCH
    # ---------------------------------------------------------

    # Binary Search requires a sorted collection.
    sorted_rs = merge_sort(
        restaurants,
        key=lambda x:
            x['name'].lower()
    )

    bs = binary_search(
        sorted_rs,
        q,
        key=lambda x:
            x['name'].lower()
    )

    if bs:

        return [bs]

    # ---------------------------------------------------------
    # PARTIAL SEARCH
    # ---------------------------------------------------------

    matches = [
        r
        for r in restaurants
        if (
            q in r['name'].lower()
            or
            q in r['area'].lower()
        )
    ]

    # ---------------------------------------------------------
    # MERGE SORT
    # ---------------------------------------------------------

    return merge_sort(
        matches,
        key=lambda x:
            x['name'].lower()
    )


def expiry_heap(items):
    """Min Heap keyed by ISO expiry date and item ID."""

    heap = MinHeap()

    for item in items:

        heap.insert(
            (
                item['expiry_date'],
                int(item['id']),
                item
            )
        )

    return heap


def ordered_complaints(items):
    """Priority Queue: highest calculated priority score first."""

    queue = PriorityQueue()

    for item in items:

        queue.push(
            float(
                item.get(
                    'priority_score'
                ) or 0
            ),
            item
        )

    return queue.ordered()