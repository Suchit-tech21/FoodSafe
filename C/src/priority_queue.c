/* Priority Queue implementation for complaints */
#include <stdio.h>

#include "../include/priority_queue.h"


/* ============================================
   SWAP
   ============================================ */

static void swapComplaints(
    Complaint *a,
    Complaint *b
) {

    Complaint temp = *a;

    *a = *b;

    *b = temp;
}


/* ============================================
   HEAPIFY UP
   ============================================ */

static void heapifyUp(
    ComplaintPriorityQueue *queue,
    int index
) {

    while (index > 0) {

        int parent =
            (index - 1) / 2;


        if (
            queue->complaints[parent].priorityScore
            >=
            queue->complaints[index].priorityScore
        ) {

            break;
        }


        swapComplaints(
            &queue->complaints[parent],
            &queue->complaints[index]
        );


        index = parent;
    }
}


/* ============================================
   HEAPIFY DOWN
   ============================================ */

static void heapifyDown(
    ComplaintPriorityQueue *queue,
    int index
) {

    while (1) {

        int left =
            2 * index + 1;

        int right =
            2 * index + 2;

        int highest = index;


        if (
            left < queue->size &&
            queue->complaints[left].priorityScore
            >
            queue->complaints[highest].priorityScore
        ) {

            highest = left;
        }


        if (
            right < queue->size &&
            queue->complaints[right].priorityScore
            >
            queue->complaints[highest].priorityScore
        ) {

            highest = right;
        }


        if (highest == index) {

            break;
        }


        swapComplaints(
            &queue->complaints[index],
            &queue->complaints[highest]
        );


        index = highest;
    }
}


/* ============================================
   INITIALIZE
   ============================================ */

void initializePriorityQueue(
    ComplaintPriorityQueue *queue
) {

    queue->size = 0;
}


/* ============================================
   ENQUEUE
   ============================================ */

int enqueueComplaint(
    ComplaintPriorityQueue *queue,
    Complaint complaint
) {

    if (
        queue->size >= MAX_COMPLAINTS
    ) {

        return 0;
    }


    queue->complaints[
        queue->size
    ] = complaint;


    heapifyUp(
        queue,
        queue->size
    );


    queue->size++;


    return 1;
}


/* ============================================
   PEEK
   ============================================ */

Complaint *peekHighestPriority(
    ComplaintPriorityQueue *queue
) {

    if (queue->size == 0) {

        return NULL;
    }


    return &queue->complaints[0];
}


/* ============================================
   DEQUEUE
   ============================================ */

Complaint dequeueHighestPriority(
    ComplaintPriorityQueue *queue
) {

    Complaint emptyComplaint = {0};


    if (queue->size == 0) {

        return emptyComplaint;
    }


    Complaint highest =
        queue->complaints[0];


    queue->size--;


    if (queue->size > 0) {

        queue->complaints[0] =
            queue->complaints[queue->size];


        heapifyDown(
            queue,
            0
        );
    }


    return highest;
}


/* ============================================
   DISPLAY
   ============================================ */

void displayPriorityQueue(
    const ComplaintPriorityQueue *queue
) {

    printf("\n");
    printf("============================================\n");
    printf("        FOODSAFE COMPLAINT QUEUE\n");
    printf("============================================\n");


    if (queue->size == 0) {

        printf("No complaints.\n");

        return;
    }


    for (int i = 0; i < queue->size; i++) {

        printf(
            "[%d] Complaint #%d | Priority: %d/100\n",
            i,
            queue->complaints[i].id,
            queue->complaints[i].priorityScore
        );
    }


    printf("============================================\n");
}