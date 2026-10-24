/* Searching algorithms */
#include <stdio.h>

#include "../include/searching.h"


/* ============================================
   LINEAR SEARCH
   ============================================ */

int linearSearchRestaurant(
    Restaurant restaurants[],
    int size,
    int id
) {

    for (int i = 0; i < size; i++) {

        if (restaurants[i].id == id) {

            return i;
        }
    }

    return -1;
}


/* ============================================
   BINARY SEARCH
   ============================================ */

int binarySearchRestaurant(
    Restaurant restaurants[],
    int size,
    int id
) {

    int left = 0;
    int right = size - 1;


    while (left <= right) {

        int middle =
            left + (right - left) / 2;


        if (restaurants[middle].id == id) {

            return middle;
        }


        if (restaurants[middle].id < id) {

            left = middle + 1;
        }

        else {

            right = middle - 1;
        }
    }


    return -1;
}


/* ============================================
   DISPLAY RESULT
   ============================================ */

void displaySearchResult(
    Restaurant restaurants[],
    int index
) {

    if (index == -1) {

        printf("\nRestaurant not found.\n");

        return;
    }


    printf("\n");
    printf("============================================\n");
    printf("          SEARCH RESULT\n");
    printf("============================================\n");

    printf("Restaurant ID : %d\n",
           restaurants[index].id);

    printf("Name          : %s\n",
           restaurants[index].name);

    printf("Address       : %s\n",
           restaurants[index].address);

    printf("City          : %s\n",
           restaurants[index].city);

    printf("============================================\n");
}