/* Priority Queue declarations */
#ifndef PRIORITY_QUEUE_H
#define PRIORITY_QUEUE_H

#include "complaint.h"

#define MAX_COMPLAINTS 100


typedef struct {

    Complaint complaints[MAX_COMPLAINTS];

    int size;

} ComplaintPriorityQueue;


/* Initialize queue */

void initializePriorityQueue(
    ComplaintPriorityQueue *queue
);


/* Insert complaint */

int enqueueComplaint(
    ComplaintPriorityQueue *queue,
    Complaint complaint
);


/* Get highest priority complaint */

Complaint *peekHighestPriority(
    ComplaintPriorityQueue *queue
);


/* Remove highest priority complaint */

Complaint dequeueHighestPriority(
    ComplaintPriorityQueue *queue
);


/* Display queue */

void displayPriorityQueue(
    const ComplaintPriorityQueue *queue
);

#endif