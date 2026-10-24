#ifndef HASH_TABLE_H
#define HASH_TABLE_H

#include "restaurant.h"

#define HASH_TABLE_SIZE 10

/* Hash table entry */
typedef struct HashEntry {
    Restaurant restaurant;
    int occupied;
} HashEntry;

/* Hash table */
typedef struct {
    HashEntry table[HASH_TABLE_SIZE];
} HashTable;

/* Initialize hash table */
void initializeHashTable(HashTable *hashTable);

/* Insert restaurant */
int insertRestaurant(HashTable *hashTable, Restaurant restaurant);

/* Search restaurant by ID */
Restaurant *searchRestaurant(
    HashTable *hashTable,
    int id
);

/* Delete restaurant by ID */
int deleteRestaurantFromHashTable(
    HashTable *hashTable,
    int id
);

/* Display hash table */
void displayHashTable(const HashTable *hashTable);

#endif