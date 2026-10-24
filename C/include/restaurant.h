#ifndef RESTAURANT_H
#define RESTAURANT_H

#define MAX_NAME 100
#define MAX_ADDRESS 200
#define MAX_CITY 50
#define MAX_PHONE 20


typedef struct {

    int id;

    char name[MAX_NAME];
    char address[MAX_ADDRESS];
    char city[MAX_CITY];
    char phone[MAX_PHONE];

    /* Official safety information */

    int license_valid;
    int inspection_available;

    /* Risk-related information */

    int confirmed_violations;
    int verified_complaints;
    int pending_complaints;
    int inventory_incidents;

    /*
        Risk Score:

        0   = SAFEST
        100 = MOST DANGEROUS
    */

    int risk_score;

} Restaurant;


/* ============================================
   CREATE RESTAURANT
   ============================================ */

Restaurant createRestaurant(
    int id,
    const char *name,
    const char *address,
    const char *city,
    const char *phone
);


/* ============================================
   DISPLAY RESTAURANT
   ============================================ */

void displayRestaurant(
    const Restaurant *restaurant
);


/* ============================================
   DISPLAY SAFETY PROFILE
   ============================================ */

void displaySafetyProfile(
    const Restaurant *restaurant
);


/* ============================================
   CALCULATE RISK SCORE
   ============================================ */

void calculateRiskScore(
    Restaurant *restaurant
);


#endif