#ifndef STORAGE_H
#define STORAGE_H

#include "restaurant.h"
#include "complaint.h"
#include "inventory.h"


#define RESTAURANT_FILE "data/restaurants.dat"
#define COMPLAINT_FILE  "data/complaints.dat"
#define INVENTORY_FILE  "data/inventory.dat"


/* ============================================
   RESTAURANT STORAGE
   ============================================ */

int saveRestaurants(
    Restaurant restaurants[],
    int count
);

int loadRestaurants(
    Restaurant restaurants[],
    int maxCount
);


/* ============================================
   COMPLAINT STORAGE
   ============================================ */

int saveComplaints(
    Complaint complaints[],
    int count
);

int loadComplaints(
    Complaint complaints[],
    int maxCount
);


/* ============================================
   INVENTORY STORAGE
   ============================================ */

int saveInventory(
    FoodItem items[],
    int count
);

int loadInventory(
    FoodItem items[],
    int maxCount
);


/* ============================================
   SAVE ALL DATA
   ============================================ */

void saveAllData(
    Restaurant restaurants[],
    int restaurantCount,
    Complaint complaints[],
    int complaintCount,
    FoodItem inventory[],
    int inventoryCount
);


/* ============================================
   DISPLAY LOADED DATA
   ============================================ */

void displayLoadedData(
    Restaurant restaurants[],
    int restaurantCount,
    Complaint complaints[],
    int complaintCount,
    FoodItem inventory[],
    int inventoryCount
);

#endif