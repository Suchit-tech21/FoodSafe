/* Risk calculation declarations */
#ifndef RISK_H
#define RISK_H

typedef struct {
    int official_compliance;
    int inspection_history;
    int confirmed_violations;
    int verified_complaints;
    int pending_reports;
    int inventory_incidents;
    int recency;
} RiskFactors;

int calculate_risk_score(RiskFactors factors);

const char *get_risk_level(int score);

#endif