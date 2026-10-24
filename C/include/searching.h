/* Searching algorithm declarations */
#ifndef SEARCHING_H
#define SEARCHING_H

#include "restaurant.h"

/* Linear search */

int linearSearchRestaurant(
    Restaurant restaurants[],
    int size,
    int id
);


/* Binary search */

int binarySearchRestaurant(
    Restaurant restaurants[],
    int size,
    int id
);


/* Display search result */

void displaySearchResult(
    Restaurant restaurants[],
    int index
);

#endif