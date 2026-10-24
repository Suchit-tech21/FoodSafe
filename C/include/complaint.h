/* Complaint management declarations */
#ifndef COMPLAINT_H
#define COMPLAINT_H

#define MAX_COMPLAINT_DESCRIPTION 300

typedef enum {
    COMPLAINT_PENDING,
    COMPLAINT_UNDER_REVIEW,
    COMPLAINT_VERIFIED,
    COMPLAINT_REJECTED
} ComplaintStatus;


typedef enum {
    SEVERITY_LOW = 1,
    SEVERITY_MEDIUM = 2,
    SEVERITY_HIGH = 3,
    SEVERITY_CRITICAL = 4
} ComplaintSeverity;


typedef struct {

    int id;

    int restaurantId;

    int userId;

    char description[MAX_COMPLAINT_DESCRIPTION];

    ComplaintSeverity severity;

    int hasEvidence;

    int previousViolations;

    int independentReports;

    int daysOld;

    ComplaintStatus status;

    int priorityScore;

} Complaint;


/* Create complaint */

Complaint createComplaint(
    int id,
    int restaurantId,
    int userId,
    const char *description,
    ComplaintSeverity severity,
    int hasEvidence,
    int previousViolations,
    int independentReports,
    int daysOld
);


/* Calculate priority */

int calculateComplaintPriority(
    Complaint *complaint
);


/* Display complaint */

void displayComplaint(
    const Complaint *complaint
);


/* Display priority information */

void displayComplaintPriority(
    const Complaint *complaint
);

#endif