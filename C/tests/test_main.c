#include <assert.h>
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

int main(void) {
    Restaurant a = createRestaurant(1, "Green Leaf Restaurant", "Kothrud", "Pune", "000");
    Restaurant b = createRestaurant(2, "Spice Garden", "Baner", "Pune", "001");
    a.license_valid = 1; a.inspection_available = 1; a.confirmed_violations = 1; a.verified_complaints = 2;
    b.license_valid = 1; b.inspection_available = 1; b.confirmed_violations = 0; b.verified_complaints = 0;
    calculateRiskScore(&a); calculateRiskScore(&b);

    RestaurantList list; initializeList(&list); addRestaurant(&list,a); addRestaurant(&list,b);
    assert(list.size == 2); assert(searchRestaurantById(&list,2) != NULL); assert(deleteRestaurant(&list,2) == 1); assert(list.size == 1); freeList(&list);

    HashTable ht; initializeHashTable(&ht); assert(insertRestaurant(&ht,a)==1); assert(searchRestaurant(&ht,1)!=NULL); assert(deleteRestaurantFromHashTable(&ht,1)==1); assert(searchRestaurant(&ht,1)==NULL);

    FoodItem f1 = {0}, f2 = {0}, f3 = {0};
    strcpy(f1.productName,"Milk"); strcpy(f1.expiryDate,"2026-09-11");
    strcpy(f2.productName,"Paneer"); strcpy(f2.expiryDate,"2026-09-13");
    strcpy(f3.productName,"Sauce"); strcpy(f3.expiryDate,"2026-09-30");
    MinHeap heap; initializeMinHeap(&heap); assert(insertIntoMinHeap(&heap,f2)); assert(insertIntoMinHeap(&heap,f1)); assert(insertIntoMinHeap(&heap,f3)); assert(strcmp(peekMinHeap(&heap)->productName,"Milk")==0); assert(strcmp(extractMin(&heap).productName,"Milk")==0);

    Complaint c1={0}, c2={0}; c1.id=1; c1.priorityScore=40; c2.id=2; c2.priorityScore=90;
    ComplaintPriorityQueue pq; initializePriorityQueue(&pq); assert(enqueueComplaint(&pq,c1)); assert(enqueueComplaint(&pq,c2)); assert(peekHighestPriority(&pq)->id==2); assert(dequeueHighestPriority(&pq).id==2);

    Restaurant arr[3] = {a,b,createRestaurant(3,"Royal Tandoor","Wakad","Pune","002")};
    arr[2].risk_score=95; arr[0].risk_score=30; arr[1].risk_score=60;
    assert(linearSearchRestaurant(arr,3,2)==1); assert(binarySearchRestaurant((Restaurant[]){a,b},2,2)==1);
    insertionSortByRisk(arr,3); assert(arr[0].risk_score==95); assert(arr[2].risk_score==30);

    printf("FOODSAFE C DS tests: PASS\n");
    return 0;
}
