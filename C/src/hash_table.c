/* Hash Table implementation */
#include <stdio.h>

#include "../include/hash_table.h"


/* ============================================
   HASH FUNCTION
   ============================================ */

static int hashFunction(int id) {
    return id % HASH_TABLE_SIZE;
}


/* ============================================
   INITIALIZE HASH TABLE
   ============================================ */

void initializeHashTable(HashTable *hashTable) {

    for (int i = 0; i < HASH_TABLE_SIZE; i++) {

        hashTable->table[i].occupied = 0;
    }
}


/* ============================================
   INSERT RESTAURANT
   ============================================ */

int insertRestaurant(
    HashTable *hashTable,
    Restaurant restaurant
) {

    int index = hashFunction(restaurant.id);

    /*
        Linear probing handles collisions.

        If the calculated position is occupied,
        move to the next position.
    */

    for (int i = 0; i < HASH_TABLE_SIZE; i++) {

        int currentIndex =
            (index + i) % HASH_TABLE_SIZE;


        /* Empty position */

        if (!hashTable->table[currentIndex].occupied) {

            hashTable->table[currentIndex].restaurant =
                restaurant;

            hashTable->table[currentIndex].occupied = 1;

            return 1;
        }


        /* Duplicate ID */

        if (hashTable->table[currentIndex].restaurant.id
            == restaurant.id) {

            return 0;
        }
    }

    /* Hash table is full */

    return 0;
}


/* ============================================
   SEARCH RESTAURANT
   ============================================ */

Restaurant *searchRestaurant(
    HashTable *hashTable,
    int id
) {

    int index = hashFunction(id);


    for (int i = 0; i < HASH_TABLE_SIZE; i++) {

        int currentIndex =
            (index + i) % HASH_TABLE_SIZE;


        /* Empty position means not found */

        if (!hashTable->table[currentIndex].occupied) {

            return NULL;
        }


        /* Restaurant found */

        if (hashTable->table[currentIndex].restaurant.id
            == id) {

            return &hashTable->table[currentIndex].restaurant;
        }
    }


    return NULL;
}


/* ============================================
   DELETE RESTAURANT
   ============================================ */

int deleteRestaurantFromHashTable(
    HashTable *hashTable,
    int id
) {

    Restaurant *restaurant =
        searchRestaurant(hashTable, id);


    if (restaurant == NULL) {

        return 0;
    }


    int index = hashFunction(id);


    for (int i = 0; i < HASH_TABLE_SIZE; i++) {

        int currentIndex =
            (index + i) % HASH_TABLE_SIZE;


        if (hashTable->table[currentIndex].occupied &&
            hashTable->table[currentIndex].restaurant.id
                == id) {

            hashTable->table[currentIndex].occupied = 0;

            return 1;
        }
    }


    return 0;
}


/* ============================================
   DISPLAY HASH TABLE
   ============================================ */

void displayHashTable(
    const HashTable *hashTable
) {

    printf("\n");
    printf("============================================\n");
    printf("             FOODSAFE HASH TABLE\n");
    printf("============================================\n");


    for (int i = 0; i < HASH_TABLE_SIZE; i++) {

        printf("[%d] ", i);


        if (hashTable->table[i].occupied) {

            printf("ID: %d | %s",
                   hashTable->table[i].restaurant.id,
                   hashTable->table[i].restaurant.name);
        }

        else {

            printf("EMPTY");
        }


        printf("\n");
    }


    printf("============================================\n");
}