/* Min Heap declarations */
#ifndef MIN_HEAP_H
#define MIN_HEAP_H

#include "inventory.h"

#define MAX_HEAP_SIZE 100


typedef struct {

    FoodItem items[MAX_HEAP_SIZE];

    int size;

} MinHeap;


/* Initialize heap */

void initializeMinHeap(MinHeap *heap);


/* Insert food item */

int insertIntoMinHeap(
    MinHeap *heap,
    FoodItem item
);


/* Get earliest-expiring item */

FoodItem *peekMinHeap(
    MinHeap *heap
);


/* Remove earliest-expiring item */

FoodItem extractMin(
    MinHeap *heap
);


/* Display heap */

void displayMinHeap(
    const MinHeap *heap
);

#endif