/* Inventory management implementation */
#include <stdio.h>
#include <string.h>

#include "../include/inventory.h"


FoodItem createFoodItem(
    int id,
    const char *productName,
    const char *batchNumber,
    int quantity,
    const char *purchaseDate,
    const char *expiryDate,
    const char *supplierName
) {

    FoodItem item;

    item.id = id;

    strncpy(
        item.productName,
        productName,
        MAX_PRODUCT_NAME - 1
    );

    item.productName[MAX_PRODUCT_NAME - 1] = '\0';


    strncpy(
        item.batchNumber,
        batchNumber,
        MAX_BATCH_NUMBER - 1
    );

    item.batchNumber[MAX_BATCH_NUMBER - 1] = '\0';


    item.quantity = quantity;


    strncpy(
        item.purchaseDate,
        purchaseDate,
        sizeof(item.purchaseDate) - 1
    );

    item.purchaseDate[
        sizeof(item.purchaseDate) - 1
    ] = '\0';


    strncpy(
        item.expiryDate,
        expiryDate,
        sizeof(item.expiryDate) - 1
    );

    item.expiryDate[
        sizeof(item.expiryDate) - 1
    ] = '\0';


    strncpy(
        item.supplierName,
        supplierName,
        MAX_SUPPLIER_NAME - 1
    );

    item.supplierName[
        MAX_SUPPLIER_NAME - 1
    ] = '\0';


    item.status = ACTIVE;


    return item;
}


void displayFoodItem(
    const FoodItem *item
) {

    printf("\n--------------------------------------------\n");

    printf("ID            : %d\n", item->id);

    printf("Product       : %s\n",
           item->productName);

    printf("Batch Number  : %s\n",
           item->batchNumber);

    printf("Quantity      : %d\n",
           item->quantity);

    printf("Purchase Date : %s\n",
           item->purchaseDate);

    printf("Expiry Date   : %s\n",
           item->expiryDate);

    printf("Supplier      : %s\n",
           item->supplierName);

    printf("--------------------------------------------\n");
}


void displayInventoryStatus(
    const FoodItem *item
) {

    printf("Status        : ");

    switch (item->status) {

        case ACTIVE:
            printf("ACTIVE\n");
            break;

        case EXPIRING_SOON:
            printf("EXPIRING SOON\n");
            break;

        case EXPIRED:
            printf("EXPIRED\n");
            break;

        case DISPOSED:
            printf("DISPOSED\n");
            break;

        default:
            printf("UNKNOWN\n");
    }
}