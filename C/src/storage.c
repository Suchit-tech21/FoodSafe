#include <stdio.h>

#include "../include/storage.h"


/* ============================================
   SAVE RESTAURANTS
   ============================================ */

int saveRestaurants(
    Restaurant restaurants[],
    int count
)
{
    FILE *file = fopen(
        RESTAURANT_FILE,
        "wb"
    );

    if (file == NULL) {
        printf("Error: Unable to save restaurants.\n");
        return 0;
    }

    size_t written = fwrite(
        restaurants,
        sizeof(Restaurant),
        count,
        file
    );

    fclose(file);

    return written == (size_t)count;
}


/* ============================================
   LOAD RESTAURANTS
   ============================================ */

int loadRestaurants(
    Restaurant restaurants[],
    int maxCount
)
{
    FILE *file = fopen(
        RESTAURANT_FILE,
        "rb"
    );

    if (file == NULL) {
        return 0;
    }

    size_t count = fread(
        restaurants,
        sizeof(Restaurant),
        maxCount,
        file
    );

    fclose(file);

    return (int)count;
}


/* ============================================
   SAVE COMPLAINTS
   ============================================ */

int saveComplaints(
    Complaint complaints[],
    int count
)
{
    FILE *file = fopen(
        COMPLAINT_FILE,
        "wb"
    );

    if (file == NULL) {
        printf("Error: Unable to save complaints.\n");
        return 0;
    }

    size_t written = fwrite(
        complaints,
        sizeof(Complaint),
        count,
        file
    );

    fclose(file);

    return written == (size_t)count;
}


/* ============================================
   LOAD COMPLAINTS
   ============================================ */

int loadComplaints(
    Complaint complaints[],
    int maxCount
)
{
    FILE *file = fopen(
        COMPLAINT_FILE,
        "rb"
    );

    if (file == NULL) {
        return 0;
    }

    size_t count = fread(
        complaints,
        sizeof(Complaint),
        maxCount,
        file
    );

    fclose(file);

    return (int)count;
}


/* ============================================
   SAVE INVENTORY
   ============================================ */

int saveInventory(
    FoodItem items[],
    int count
)
{
    FILE *file = fopen(
        INVENTORY_FILE,
        "wb"
    );

    if (file == NULL) {
        printf("Error: Unable to save inventory.\n");
        return 0;
    }

    size_t written = fwrite(
        items,
        sizeof(FoodItem),
        count,
        file
    );

    fclose(file);

    return written == (size_t)count;
}


/* ============================================
   LOAD INVENTORY
   ============================================ */

int loadInventory(
    FoodItem items[],
    int maxCount
)
{
    FILE *file = fopen(
        INVENTORY_FILE,
        "rb"
    );

    if (file == NULL) {
        return 0;
    }

    size_t count = fread(
        items,
        sizeof(FoodItem),
        maxCount,
        file
    );

    fclose(file);

    return (int)count;
}


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
)
{
    int restaurantResult =
        saveRestaurants(
            restaurants,
            restaurantCount
        );

    int complaintResult =
        saveComplaints(
            complaints,
            complaintCount
        );

    int inventoryResult =
        saveInventory(
            inventory,
            inventoryCount
        );


    printf("\n");
    printf("============================================\n");
    printf("              DATA SAVED\n");
    printf("============================================\n");

    printf(
        "Restaurants : %s\n",
        restaurantResult ? "SUCCESS" : "FAILED"
    );

    printf(
        "Complaints  : %s\n",
        complaintResult ? "SUCCESS" : "FAILED"
    );

    printf(
        "Inventory   : %s\n",
        inventoryResult ? "SUCCESS" : "FAILED"
    );

    printf("============================================\n");
}


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
)
{
    printf("\n");
    printf("============================================\n");
    printf("             LOADED DATA\n");
    printf("============================================\n");


    printf(
        "Restaurants loaded : %d\n",
        restaurantCount
    );

    printf(
        "Complaints loaded  : %d\n",
        complaintCount
    );

    printf(
        "Inventory loaded   : %d\n",
        inventoryCount
    );


    printf("\nRestaurants:\n");

    for (int i = 0; i < restaurantCount; i++) {

        printf(
            "  [%d] %s | Risk: %d/100\n",
            restaurants[i].id,
            restaurants[i].name,
            restaurants[i].risk_score
        );
    }


    printf("\nComplaints:\n");

    for (int i = 0; i < complaintCount; i++) {

        printf(
            "  Complaint #%d | Priority: %d/100\n",
            complaints[i].id,
            complaints[i].priorityScore
        );
    }


    printf("\nInventory:\n");

    for (int i = 0; i < inventoryCount; i++) {

        printf(
            "  [%d] %s | Expiry: %s\n",
            inventory[i].id,
            inventory[i].productName,
            inventory[i].expiryDate
        );
    }


    printf("============================================\n");
}