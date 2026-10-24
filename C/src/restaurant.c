#include <stdio.h>
#include <string.h>
#include "risk.h"

#include "../include/restaurant.h"


/* ============================================
   CREATE RESTAURANT
   ============================================ */

Restaurant createRestaurant(
    int id,
    const char *name,
    const char *address,
    const char *city,
    const char *phone
) {

    Restaurant restaurant;

    restaurant.id = id;


    /* Restaurant name */

    strncpy(
        restaurant.name,
        name,
        MAX_NAME - 1
    );

    restaurant.name[MAX_NAME - 1] = '\0';


    /* Address */

    strncpy(
        restaurant.address,
        address,
        MAX_ADDRESS - 1
    );

    restaurant.address[MAX_ADDRESS - 1] = '\0';


    /* City */

    strncpy(
        restaurant.city,
        city,
        MAX_CITY - 1
    );

    restaurant.city[MAX_CITY - 1] = '\0';


    /* Phone */

    strncpy(
        restaurant.phone,
        phone,
        MAX_PHONE - 1
    );

    restaurant.phone[MAX_PHONE - 1] = '\0';


    /* ========================================
       DEFAULT SAFETY INFORMATION
       ======================================== */

    restaurant.license_valid = 0;

    restaurant.inspection_available = 0;

    restaurant.confirmed_violations = 0;

    restaurant.verified_complaints = 0;

    restaurant.pending_complaints = 0;

    restaurant.inventory_incidents = 0;

    restaurant.risk_score = 0;


    return restaurant;
}


/* ============================================
   CALCULATE RISK SCORE
   ============================================ */

void calculateRiskScore(
    Restaurant *restaurant
) {

    /*
        FOODSAFE RISK SCORE

        0   = SAFEST
        100 = MOST DANGEROUS
    */

    int score = 0;


    /* ========================================
       LICENSE
       ======================================== */

    /*
        Invalid/unverified license
        creates significant risk.
    */

    if (!restaurant->license_valid) {

        score += 30;
    }


    /* ========================================
       INSPECTION
       ======================================== */

    /*
        Missing inspection information
        contributes to risk.
    */

    if (!restaurant->inspection_available) {

        score += 10;
    }


    /* ========================================
       CONFIRMED VIOLATIONS
       ======================================== */

    /*
        Confirmed violations have a
        strong impact on risk.
    */

    score +=
        restaurant->confirmed_violations * 15;


    /* ========================================
       VERIFIED COMPLAINTS
       ======================================== */

    /*
        Verified complaints contribute
        moderate risk.
    */

    score +=
        restaurant->verified_complaints * 5;


    /* ========================================
       PENDING COMPLAINTS
       ======================================== */

    /*
        Pending complaints have a smaller
        impact because they are not yet
        confirmed.
    */

    score +=
        restaurant->pending_complaints * 2;


    /* ========================================
       INVENTORY INCIDENTS
       ======================================== */

    /*
        Food inventory safety incidents
        increase risk.
    */

    score +=
        restaurant->inventory_incidents * 10;


    /* ========================================
       LIMIT SCORE
       ======================================== */

    if (score > 100) {

        score = 100;
    }


    if (score < 0) {

        score = 0;
    }


    restaurant->risk_score = score;
}


/* ============================================
   DISPLAY RESTAURANT
   ============================================ */

void displayRestaurant(
    const Restaurant *restaurant
) {

    printf("\n");
    printf("========================================\n");
    printf("           RESTAURANT PROFILE\n");
    printf("========================================\n");


    printf(
        "ID      : %d\n",
        restaurant->id
    );


    printf(
        "Name    : %s\n",
        restaurant->name
    );


    printf(
        "Address : %s\n",
        restaurant->address
    );


    printf(
        "City    : %s\n",
        restaurant->city
    );


    printf(
        "Phone   : %s\n",
        restaurant->phone
    );


    printf("========================================\n");
}


/* ============================================
   DISPLAY SAFETY PROFILE
   ============================================ */

void displaySafetyProfile(
    const Restaurant *restaurant
) {

    printf("\n");
    printf("========================================\n");
    printf("          FOOD SAFETY PROFILE\n");
    printf("========================================\n");


    printf(
        "Restaurant          : %s\n",
        restaurant->name
    );


    printf("\n");


    /* License */

    printf(
        "License             : %s\n",
        restaurant->license_valid
            ? "VERIFIED"
            : "NOT VERIFIED"
    );


    /* Inspection */

    printf(
        "Inspection          : %s\n",
        restaurant->inspection_available
            ? "AVAILABLE"
            : "NOT AVAILABLE"
    );


    /* Confirmed violations */

    printf(
        "Confirmed Violations: %d\n",
        restaurant->confirmed_violations
    );


    /* Verified complaints */

    printf(
        "Verified Complaints : %d\n",
        restaurant->verified_complaints
    );


    /* Pending complaints */

    printf(
        "Pending Complaints  : %d\n",
        restaurant->pending_complaints
    );


    /* Inventory incidents */

    printf(
        "Inventory Incidents : %d\n",
        restaurant->inventory_incidents
    );


    /* Risk */

    printf(
        "Risk Score          : %d/100\n",
        restaurant->risk_score
    );


    printf("----------------------------------------\n");


    /* ========================================
       RISK LEVEL
       ======================================== */

    if (restaurant->risk_score <= 25) {

        printf(
            "Safety Indicator     : LOW RISK\n"
        );
    }

    else if (restaurant->risk_score <= 50) {

        printf(
            "Safety Indicator     : MODERATE RISK\n"
        );
    }

    else if (restaurant->risk_score <= 75) {

        printf(
            "Safety Indicator     : HIGH RISK\n"
        );
    }

    else {

        printf(
            "Safety Indicator     : CRITICAL RISK\n"
        );
    }


    printf("========================================\n");
}