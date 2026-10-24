/* Min Heap implementation for expiry tracking */
#include <stdio.h>
#include<string.h>

#include "../include/min_heap.h"


/* ============================================
   SWAP
   ============================================ */

static void swap(
    FoodItem *a,
    FoodItem *b
) {

    FoodItem temp = *a;

    *a = *b;

    *b = temp;
}


/* ============================================
   COMPARE EXPIRY DATES
   ============================================ */

/*
    Dates are stored as:

    YYYY-MM-DD

    Therefore normal string comparison works.
*/

static int compareExpiry(
    const FoodItem *a,
    const FoodItem *b
) {

    return strcmp(
        a->expiryDate,
        b->expiryDate
    );
}


/* ============================================
   HEAPIFY UP
   ============================================ */

static void heapifyUp(
    MinHeap *heap,
    int index
) {

    while (index > 0) {

        int parent =
            (index - 1) / 2;


        if (
            compareExpiry(
                &heap->items[index],
                &heap->items[parent]
            ) >= 0
        ) {

            break;
        }


        swap(
            &heap->items[index],
            &heap->items[parent]
        );


        index = parent;
    }
}


/* ============================================
   HEAPIFY DOWN
   ============================================ */

static void heapifyDown(
    MinHeap *heap,
    int index
) {

    while (1) {

        int left =
            2 * index + 1;

        int right =
            2 * index + 2;

        int smallest = index;


        if (
            left < heap->size &&
            compareExpiry(
                &heap->items[left],
                &heap->items[smallest]
            ) < 0
        ) {

            smallest = left;
        }


        if (
            right < heap->size &&
            compareExpiry(
                &heap->items[right],
                &heap->items[smallest]
            ) < 0
        ) {

            smallest = right;
        }


        if (smallest == index) {

            break;
        }


        swap(
            &heap->items[index],
            &heap->items[smallest]
        );


        index = smallest;
    }
}


/* ============================================
   INITIALIZE
   ============================================ */

void initializeMinHeap(
    MinHeap *heap
) {

    heap->size = 0;
}


/* ============================================
   INSERT
   ============================================ */

int insertIntoMinHeap(
    MinHeap *heap,
    FoodItem item
) {

    if (heap->size >= MAX_HEAP_SIZE) {

        return 0;
    }


    heap->items[heap->size] = item;

    heapifyUp(
        heap,
        heap->size
    );

    heap->size++;

    return 1;
}


/* ============================================
   PEEK
   ============================================ */

FoodItem *peekMinHeap(
    MinHeap *heap
) {

    if (heap->size == 0) {

        return NULL;
    }


    return &heap->items[0];
}


/* ============================================
   EXTRACT MIN
   ============================================ */

FoodItem extractMin(
    MinHeap *heap
) {

    FoodItem emptyItem = {0};


    if (heap->size == 0) {

        return emptyItem;
    }


    FoodItem minimum =
        heap->items[0];


    heap->size--;


    if (heap->size > 0) {

        heap->items[0] =
            heap->items[heap->size];

        heapifyDown(
            heap,
            0
        );
    }


    return minimum;
}


/* ============================================
   DISPLAY
   ============================================ */

void displayMinHeap(
    const MinHeap *heap
) {

    printf("\n");
    printf("============================================\n");
    printf("             FOODSAFE MIN HEAP\n");
    printf("============================================\n");


    if (heap->size == 0) {

        printf("Heap is empty.\n");

        return;
    }


    for (int i = 0; i < heap->size; i++) {

        printf(
            "[%d] %-15s | Expires: %s\n",
            i,
            heap->items[i].productName,
            heap->items[i].expiryDate
        );
    }


    printf("============================================\n");
}