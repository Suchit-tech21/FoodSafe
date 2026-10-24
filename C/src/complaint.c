/* Complaint management implementation */
#include <stdio.h>
#include <string.h>

#include "../include/complaint.h"


/* ============================================
   CREATE COMPLAINT
   ============================================ */

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
) {

    Complaint complaint;

    complaint.id = id;

    complaint.restaurantId = restaurantId;

    complaint.userId = userId;


    strncpy(
        complaint.description,
        description,
        MAX_COMPLAINT_DESCRIPTION - 1
    );

    complaint.description[
        MAX_COMPLAINT_DESCRIPTION - 1
    ] = '\0';


    complaint.severity = severity;

    complaint.hasEvidence = hasEvidence;

    complaint.previousViolations = previousViolations;

    complaint.independentReports = independentReports;

    complaint.daysOld = daysOld;

    complaint.status = COMPLAINT_PENDING;

    complaint.priorityScore = 0;


    return complaint;
}


/* ============================================
   CALCULATE PRIORITY
   ============================================ */

int calculateComplaintPriority(
    Complaint *complaint
) {

    int score = 0;


    /*
        Severity contributes the largest weight.
    */

    score += complaint->severity * 25;


    /*
        Evidence increases confidence.
    */

    if (complaint->hasEvidence) {

        score += 20;
    }


    /*
        Previous violations increase priority.
    */

    score += complaint->previousViolations * 10;


    /*
        Independent reports increase priority.
    */

    score += complaint->independentReports * 5;


    /*
        Recent complaints receive higher priority.

        Maximum contribution = 15.
    */

    if (complaint->daysOld <= 1) {

        score += 15;
    }

    else if (complaint->daysOld <= 3) {

        score += 10;
    }

    else if (complaint->daysOld <= 7) {

        score += 5;
    }


    if (score > 100) {

        score = 100;
    }


    complaint->priorityScore = score;

    return score;
}


/* ============================================
   DISPLAY COMPLAINT
   ============================================ */

void displayComplaint(
    const Complaint *complaint
) {

    printf("\n--------------------------------------------\n");

    printf("Complaint ID       : %d\n",
           complaint->id);

    printf("Restaurant ID      : %d\n",
           complaint->restaurantId);

    printf("User ID            : %d\n",
           complaint->userId);

    printf("Description        : %s\n",
           complaint->description);

    printf("Severity           : ");

    switch (complaint->severity) {

        case SEVERITY_LOW:
            printf("LOW\n");
            break;

        case SEVERITY_MEDIUM:
            printf("MEDIUM\n");
            break;

        case SEVERITY_HIGH:
            printf("HIGH\n");
            break;

        case SEVERITY_CRITICAL:
            printf("CRITICAL\n");
            break;

        default:
            printf("UNKNOWN\n");
    }


    printf("Evidence           : %s\n",
           complaint->hasEvidence
           ? "AVAILABLE"
           : "NONE");

    printf("Previous Violations: %d\n",
           complaint->previousViolations);

    printf("Independent Reports: %d\n",
           complaint->independentReports);

    printf("Days Old           : %d\n",
           complaint->daysOld);

    printf("Priority Score     : %d/100\n",
           complaint->priorityScore);

    printf("--------------------------------------------\n");
}


/* ============================================
   DISPLAY PRIORITY
   ============================================ */

void displayComplaintPriority(
    const Complaint *complaint
) {

    printf(
        "Complaint #%d → Priority: %d/100\n",
        complaint->id,
        complaint->priorityScore
    );
}