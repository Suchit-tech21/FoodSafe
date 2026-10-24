/* Sorting algorithm declarations */
#ifndef SORTING_H
#define SORTING_H

#include "restaurant.h"

/* Bubble Sort */
void bubbleSortByRisk(
    Restaurant restaurants[],
    int size
);

/* Selection Sort */
void selectionSortByRisk(
    Restaurant restaurants[],
    int size
);

/* Insertion Sort */
void insertionSortByRisk(
    Restaurant restaurants[],
    int size
);

/* Display sorted restaurants */
void displaySortedRestaurants(
    Restaurant restaurants[],
    int size
);

#endif