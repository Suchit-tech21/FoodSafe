#include <stdio.h>
#include <string.h>

#include "../include/restaurant.h"
#include "../include/linked_list.h"
#include "../include/hash_table.h"
#include "../include/inventory.h"
#include "../include/min_heap.h"
#include "../include/complaint.h"
#include "../include/priority_queue.h"
#include "../include/searching.h"
#include "../include/sorting.h"
#include "../include/storage.h"

int main(void) {

    printf("\n");
    printf("============================================\n");
    printf("       FOODSAFE - FOOD SAFETY PLATFORM\n");
    printf("============================================\n");


    /* ========================================
       CREATE RESTAURANT LIST
       ======================================== */

    RestaurantList restaurantList;

    initializeList(&restaurantList);


    /* ========================================
       CREATE RESTAURANTS
       ======================================== */

    Restaurant restaurant1 = createRestaurant(
        1,
        "Green Leaf Restaurant",
        "FC Road",
        "Pune",
        "9876543210"
    );


    Restaurant restaurant2 = createRestaurant(
        2,
        "Spice Garden",
        "Kothrud",
        "Pune",
        "9876543211"
    );


    Restaurant restaurant3 = createRestaurant(
        3,
        "Food Plaza",
        "Shivajinagar",
        "Pune",
        "9876543212"
    );


    Restaurant restaurant4 = createRestaurant(
        4,
        "Healthy Bites",
        "Baner",
        "Pune",
        "9876543213"
    );


    /* ========================================
       ADD SAFETY INFORMATION
       ======================================== */

    restaurant1.license_valid = 1;
    restaurant1.inspection_available = 1;
    restaurant1.confirmed_violations = 1;
    restaurant1.verified_complaints = 2;


    restaurant2.license_valid = 1;
    restaurant2.inspection_available = 1;
    restaurant2.confirmed_violations = 0;
    restaurant2.verified_complaints = 1;


    restaurant3.license_valid = 0;
    restaurant3.inspection_available = 0;
    restaurant3.confirmed_violations = 3;
    restaurant3.verified_complaints = 4;


    restaurant4.license_valid = 1;
    restaurant4.inspection_available = 1;
    restaurant4.confirmed_violations = 0;
    restaurant4.verified_complaints = 0;


    /* ========================================
       CALCULATE RISK
       ======================================== */

    calculateRiskScore(&restaurant1);
    calculateRiskScore(&restaurant2);
    calculateRiskScore(&restaurant3);
    calculateRiskScore(&restaurant4);


    /* ========================================
       ADD TO LINKED LIST
       ======================================== */

    addRestaurant(&restaurantList, restaurant1);
    addRestaurant(&restaurantList, restaurant2);
    addRestaurant(&restaurantList, restaurant3);
    addRestaurant(&restaurantList, restaurant4);


    /* ========================================
       DISPLAY ALL RESTAURANTS
       ======================================== */

    displayAllRestaurants(&restaurantList);


    /* ========================================
       SEARCH RESTAURANT
       ======================================== */

    printf("\n");
    printf("============================================\n");
    printf("             RESTAURANT SEARCH\n");
    printf("============================================\n");

    int searchId = 3;

    RestaurantNode *result =
        searchRestaurantById(&restaurantList, searchId);


    if (result != NULL) {

        printf("\nRestaurant Found!\n");

        displayRestaurant(&result->restaurant);

        displaySafetyProfile(&result->restaurant);
    }

    else {

        printf("\nRestaurant with ID %d not found.\n",
               searchId);
    }


    /* ========================================
       DELETE TEST
       ======================================== */

    printf("\n");
    printf("============================================\n");
    printf("          DELETE RESTAURANT TEST\n");
    printf("============================================\n");


    if (deleteRestaurant(&restaurantList, 2)) {

        printf("\nRestaurant ID 2 deleted successfully.\n");
    }

    else {

        printf("\nRestaurant ID 2 not found.\n");
    }


    /* Display list after deletion */

    displayAllRestaurants(&restaurantList);
        /* ========================================
       HASH TABLE
       ======================================== */

    printf("\n");
    printf("============================================\n");
    printf("          HASH TABLE DEMONSTRATION\n");
    printf("============================================\n");


    HashTable hashTable;

    initializeHashTable(&hashTable);


    /* Insert restaurants into Hash Table */

    insertRestaurant(&hashTable, restaurant1);
    insertRestaurant(&hashTable, restaurant2);
    insertRestaurant(&hashTable, restaurant3);
    insertRestaurant(&hashTable, restaurant4);


    /* Display Hash Table */

    displayHashTable(&hashTable);


    /* Search using Hash Table */

    int hashSearchId = 4;

    Restaurant *hashResult =
        searchRestaurant(&hashTable, hashSearchId);


    if (hashResult != NULL) {

        printf("\nHash Table Search Result:\n");

        printf("Restaurant Found!\n");
        printf("ID   : %d\n", hashResult->id);
        printf("Name : %s\n", hashResult->name);
    }

    else {

        printf("\nRestaurant not found.\n");
    }
    /* ========================================
   INVENTORY + MIN HEAP
   ======================================== */

printf("\n");
printf("============================================\n");
printf("        INVENTORY + MIN HEAP DEMO\n");
printf("============================================\n");


MinHeap expiryHeap;

initializeMinHeap(&expiryHeap);


/* Create food items */

FoodItem milk = createFoodItem(
    1,
    "Milk",
    "MILK001",
    20,
    "2026-08-25",
    "2026-08-28",
    "Fresh Dairy Supplier"
);


FoodItem chicken = createFoodItem(
    2,
    "Chicken",
    "CHK001",
    15,
    "2026-08-26",
    "2026-08-29",
    "Quality Meat Supplier"
);


FoodItem paneer = createFoodItem(
    3,
    "Paneer",
    "PNR001",
    10,
    "2026-08-27",
    "2026-08-30",
    "Fresh Dairy Supplier"
);


FoodItem sauce = createFoodItem(
    4,
    "Tomato Sauce",
    "SCE001",
    25,
    "2026-08-20",
    "2026-09-10",
    "Food Supply Co."
);


/* Insert into Min Heap */

insertIntoMinHeap(
    &expiryHeap,
    milk
);

insertIntoMinHeap(
    &expiryHeap,
    chicken
);

insertIntoMinHeap(
    &expiryHeap,
    paneer
);

insertIntoMinHeap(
    &expiryHeap,
    sauce
);


/* Display heap */

displayMinHeap(&expiryHeap);


/* Find earliest expiry */

FoodItem *earliest =
    peekMinHeap(&expiryHeap);


if (earliest != NULL) {

    printf("\n");
    printf("============================================\n");
    printf("           EARLIEST EXPIRY ALERT\n");
    printf("============================================\n");

    printf("Product      : %s\n",
           earliest->productName);

    printf("Batch Number : %s\n",
           earliest->batchNumber);

    printf("Expiry Date  : %s\n",
           earliest->expiryDate);

    printf("\nRecommended Action:\n");
    printf("Check/remove item from active inventory.\n");

    printf("============================================\n");
}
/* ========================================
   COMPLAINT + PRIORITY QUEUE
   ======================================== */

printf("\n");
printf("============================================\n");
printf("       COMPLAINT PRIORITY SYSTEM\n");
printf("============================================\n");


ComplaintPriorityQueue complaintQueue;

initializePriorityQueue(
    &complaintQueue
);


/* Complaint 1 */

Complaint complaint1 = createComplaint(
    101,
    1,
    501,
    "Improper food handling observed.",
    SEVERITY_HIGH,
    1,
    1,
    2,
    1
);


/* Complaint 2 */

Complaint complaint2 = createComplaint(
    102,
    2,
    502,
    "Restaurant surroundings appear unhygienic.",
    SEVERITY_MEDIUM,
    1,
    0,
    1,
    2
);


/* Complaint 3 */

Complaint complaint3 = createComplaint(
    103,
    3,
    503,
    "Expired food product found.",
    SEVERITY_CRITICAL,
    1,
    3,
    3,
    1
);


/* Complaint 4 */

Complaint complaint4 = createComplaint(
    104,
    4,
    504,
    "General cleanliness issue.",
    SEVERITY_LOW,
    0,
    0,
    1,
    5
);


/* Calculate priorities */

calculateComplaintPriority(
    &complaint1
);

calculateComplaintPriority(
    &complaint2
);

calculateComplaintPriority(
    &complaint3
);

calculateComplaintPriority(
    &complaint4
);


/* Insert into Priority Queue */

enqueueComplaint(
    &complaintQueue,
    complaint1
);

enqueueComplaint(
    &complaintQueue,
    complaint2
);

enqueueComplaint(
    &complaintQueue,
    complaint3
);

enqueueComplaint(
    &complaintQueue,
    complaint4
);


/* Display */

displayPriorityQueue(
    &complaintQueue
);


/* ========================================
   HIGHEST PRIORITY CASE
   ======================================== */

Complaint *highestPriority =
    peekHighestPriority(
        &complaintQueue
    );


if (highestPriority != NULL) {

    printf("\n");
    printf("============================================\n");
    printf("         HIGHEST PRIORITY CASE\n");
    printf("============================================\n");

    displayComplaint(
        highestPriority
    );

    printf("ACTION: Admin should investigate this case first.\n");

    printf("============================================\n");
}
/* ========================================
   SEARCHING ALGORITHMS
   ======================================== */

printf("\n");
printf("============================================\n");
printf("          SEARCHING DEMONSTRATION\n");
printf("============================================\n");


/*
    Create an array of restaurants.

    This array is sorted by ID.
*/

Restaurant restaurantArray[4];

restaurantArray[0] = restaurant1;
restaurantArray[1] = restaurant2;
restaurantArray[2] = restaurant3;
restaurantArray[3] = restaurant4;


/* ========================================
   LINEAR SEARCH
   ======================================== */

int linearResult =
    linearSearchRestaurant(
        restaurantArray,
        4,
        3
    );


printf("\nLinear Search for Restaurant ID 3:\n");

displaySearchResult(
    restaurantArray,
    linearResult
);


/* ========================================
   BINARY SEARCH
   ======================================== */

int binaryResult =
    binarySearchRestaurant(
        restaurantArray,
        4,
        4
    );


printf("\nBinary Search for Restaurant ID 4:\n");

displaySearchResult(
    restaurantArray,
    binaryResult
);
/* ========================================
   SORTING ALGORITHMS
   ======================================== */

printf("\n");
printf("============================================\n");
printf("             SORTING DEMO\n");
printf("============================================\n");


/*
    Create a separate array so that
    sorting does not destroy our original
    restaurant data.
*/

Restaurant sortingArray[4];

sortingArray[0] = restaurant1;
sortingArray[1] = restaurant2;
sortingArray[2] = restaurant3;
sortingArray[3] = restaurant4;


/* ========================================
   BUBBLE SORT
   ======================================== */

bubbleSortByRisk(
    sortingArray,
    4
);

printf("\nBubble Sort Result:\n");

displaySortedRestaurants(
    sortingArray,
    4
);


/* ========================================
   SELECTION SORT
   ======================================== */

sortingArray[0] = restaurant1;
sortingArray[1] = restaurant2;
sortingArray[2] = restaurant3;
sortingArray[3] = restaurant4;


selectionSortByRisk(
    sortingArray,
    4
);

printf("\nSelection Sort Result:\n");

displaySortedRestaurants(
    sortingArray,
    4
);


/* ========================================
   INSERTION SORT
   ======================================== */

sortingArray[0] = restaurant1;
sortingArray[1] = restaurant2;
sortingArray[2] = restaurant3;
sortingArray[3] = restaurant4;


insertionSortByRisk(
    sortingArray,
    4
);

printf("\nInsertion Sort Result:\n");

displaySortedRestaurants(
    sortingArray,
    4
);
/* ========================================
   FILE STORAGE TEST
   ======================================== */

Restaurant restaurantData[4];

restaurantData[0] = restaurant1;
restaurantData[1] = restaurant2;
restaurantData[2] = restaurant3;
restaurantData[3] = restaurant4;


/* Store complaints */

Complaint complaintData[4];

complaintData[0] = complaint1;
complaintData[1] = complaint2;
complaintData[2] = complaint3;
complaintData[3] = complaint4;


/* Store inventory */

FoodItem inventoryData[4];

inventoryData[0] = milk;
inventoryData[1] = chicken;
inventoryData[2] = paneer;
inventoryData[3] = sauce;


/* Save everything */

saveAllData(
    restaurantData,
    4,
    complaintData,
    4,
    inventoryData,
    4
);
/* ========================================
   LOAD DATA TEST
   ======================================== */

Restaurant loadedRestaurants[100];

Complaint loadedComplaints[100];

FoodItem loadedInventory[100];


int loadedRestaurantCount =
    loadRestaurants(
        loadedRestaurants,
        100
    );


int loadedComplaintCount =
    loadComplaints(
        loadedComplaints,
        100
    );


int loadedInventoryCount =
    loadInventory(
        loadedInventory,
        100
    );


displayLoadedData(
    loadedRestaurants,
    loadedRestaurantCount,
    loadedComplaints,
    loadedComplaintCount,
    loadedInventory,
    loadedInventoryCount
);


    /* ========================================
       FREE MEMORY
       ======================================== */

    freeList(&restaurantList);


    return 0;
}