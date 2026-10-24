/* Inventory management declarations */
#ifndef INVENTORY_H
#define INVENTORY_H

#define MAX_PRODUCT_NAME 100
#define MAX_BATCH_NUMBER 50
#define MAX_SUPPLIER_NAME 100

typedef enum {
    ACTIVE,
    EXPIRING_SOON,
    EXPIRED,
    DISPOSED
} InventoryStatus;


typedef struct {

    int id;

    char productName[MAX_PRODUCT_NAME];

    char batchNumber[MAX_BATCH_NUMBER];

    int quantity;

    char purchaseDate[20];

    char expiryDate[20];

    char supplierName[MAX_SUPPLIER_NAME];

    InventoryStatus status;

} FoodItem;


/* Create a food item */

FoodItem createFoodItem(
    int id,
    const char *productName,
    const char *batchNumber,
    int quantity,
    const char *purchaseDate,
    const char *expiryDate,
    const char *supplierName
);


/* Display food item */

void displayFoodItem(const FoodItem *item);


/* Display inventory status */

void displayInventoryStatus(const FoodItem *item);

#endif