/* Linked List implementation */
#include <stdio.h>
#include <stdlib.h>
#include "../include/linked_list.h"
void initializeList(RestaurantList *list) {
    list->head = NULL;
    list->size = 0;
}
void addRestaurant(
    RestaurantList *list,
    Restaurant restaurant
) {

    RestaurantNode *newNode =
        (RestaurantNode *)malloc(sizeof(RestaurantNode));

    if (newNode == NULL) {

        printf("Error: Memory allocation failed.\n");
        return;
    }

    newNode->restaurant = restaurant;
    newNode->next = NULL;


    /* If list is empty */

    if (list->head == NULL) {

        list->head = newNode;
    }

    else {

        RestaurantNode *current = list->head;

        while (current->next != NULL) {

            current = current->next;
        }

        current->next = newNode;
    }

    list->size++;
}


void displayAllRestaurants(
    const RestaurantList *list
) {

    if (list->head == NULL) {

        printf("\nNo restaurants found.\n");
        return;
    }


    printf("\n============================================\n");
    printf("           FOODSAFE RESTAURANTS\n");
    printf("============================================\n");


    RestaurantNode *current = list->head;

    while (current != NULL) {

        printf("\nID      : %d\n",
               current->restaurant.id);

        printf("Name    : %s\n",
               current->restaurant.name);

        printf("Address : %s\n",
               current->restaurant.address);

        printf("City    : %s\n",
               current->restaurant.city);

        printf("--------------------------------------------\n");

        current = current->next;
    }

    printf("\nTotal Restaurants: %d\n", list->size);
}


RestaurantNode *searchRestaurantById(
    RestaurantList *list,
    int id
) {

    RestaurantNode *current = list->head;

    while (current != NULL) {

        if (current->restaurant.id == id) {

            return current;
        }

        current = current->next;
    }

    return NULL;
}


int deleteRestaurant(
    RestaurantList *list,
    int id
) {

    RestaurantNode *current = list->head;
    RestaurantNode *previous = NULL;


    while (current != NULL) {

        if (current->restaurant.id == id) {

            /* Deleting the first node */

            if (previous == NULL) {

                list->head = current->next;
            }

            /* Deleting another node */

            else {

                previous->next = current->next;
            }

            free(current);

            list->size--;

            return 1;
        }

        previous = current;
        current = current->next;
    }

    return 0;
}


void freeList(RestaurantList *list) {

    RestaurantNode *current = list->head;

    while (current != NULL) {

        RestaurantNode *next = current->next;

        free(current);

        current = next;
    }

    list->head = NULL;
    list->size = 0;
}