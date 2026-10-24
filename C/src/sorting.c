/* Sorting algorithms */
#include <stdio.h>

#include "../include/sorting.h"


/* ============================================
   SWAP RESTAURANTS
   ============================================ */

static void swapRestaurants(
    Restaurant *a,
    Restaurant *b
)
{
    Restaurant temp = *a;

    *a = *b;

    *b = temp;
}


/* ============================================
   BUBBLE SORT
   HIGHEST RISK FIRST
   ============================================ */

void bubbleSortByRisk(
    Restaurant restaurants[],
    int size
)
{
    for (int i = 0; i < size - 1; i++) {

        int swapped = 0;

        for (int j = 0; j < size - i - 1; j++) {

            if (
                restaurants[j].risk_score
                <
                restaurants[j + 1].risk_score
            ) {

                swapRestaurants(
                    &restaurants[j],
                    &restaurants[j + 1]
                );

                swapped = 1;
            }
        }

        /*
            If no swapping occurred,
            the array is already sorted.
        */

        if (!swapped) {
            break;
        }
    }
}


/* ============================================
   SELECTION SORT
   HIGHEST RISK FIRST
   ============================================ */

void selectionSortByRisk(
    Restaurant restaurants[],
    int size
)
{
    for (int i = 0; i < size - 1; i++) {

        int highestIndex = i;

        for (int j = i + 1; j < size; j++) {

            if (
                restaurants[j].risk_score
                >
                restaurants[highestIndex].risk_score
            ) {

                highestIndex = j;
            }
        }

        if (highestIndex != i) {

            swapRestaurants(
                &restaurants[i],
                &restaurants[highestIndex]
            );
        }
    }
}


/* ============================================
   INSERTION SORT
   HIGHEST RISK FIRST
   ============================================ */

void insertionSortByRisk(
    Restaurant restaurants[],
    int size
)
{
    for (int i = 1; i < size; i++) {

        Restaurant current =
            restaurants[i];

        int j = i - 1;


        while (
            j >= 0 &&
            restaurants[j].risk_score
            <
            current.risk_score
        ) {

            restaurants[j + 1] =
                restaurants[j];

            j--;
        }


        restaurants[j + 1] =
            current;
    }
}


/* ============================================
   DISPLAY SORTED RESTAURANTS
   ============================================ */

void displaySortedRestaurants(
    Restaurant restaurants[],
    int size
)
{
    printf("\n");
    printf("============================================\n");
    printf("          RESTAURANTS BY RISK\n");
    printf("          HIGHEST RISK FIRST\n");
    printf("============================================\n");

    for (int i = 0; i < size; i++) {

        printf(
            "%d. %-25s | Risk: %d/100\n",
            i + 1,
            restaurants[i].name,
            restaurants[i].risk_score
        );
    }

    printf("============================================\n");
}