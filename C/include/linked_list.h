#ifndef LINKED_LIST_H
#define LINKED_LIST_H

#include "restaurant.h"

/* Node of the restaurant linked list */
typedef struct RestaurantNode {
    Restaurant restaurant;
    struct RestaurantNode *next;
} RestaurantNode;

/* Linked List */
typedef struct {
    RestaurantNode *head;
    int size;
} RestaurantList;

/* Initialize an empty list */
void initializeList(RestaurantList *list);

/* Add a restaurant to the list */
void addRestaurant(RestaurantList *list, Restaurant restaurant);

/* Display all restaurants */
void displayAllRestaurants(const RestaurantList *list);

/* Search restaurant by ID */
RestaurantNode *searchRestaurantById(
    RestaurantList *list,
    int id
);

/* Delete restaurant by ID */
int deleteRestaurant(
    RestaurantList *list,
    int id
);

/* Free all nodes */
void freeList(RestaurantList *list);

#endif