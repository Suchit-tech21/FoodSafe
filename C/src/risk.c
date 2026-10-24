/* Risk calculation implementation */
#include <stdio.h>
#include "risk.h"

int calculate_risk_score(RiskFactors factors)
{
    int score = 100;

    score -= factors.confirmed_violations * 12;
    score -= factors.verified_complaints * 5;
    score -= factors.pending_reports * 2;
    score -= factors.inventory_incidents * 5;

    score += factors.official_compliance;
    score += factors.inspection_history;
    score += factors.recency;

    if (score > 100)
        score = 100;

    if (score < 0)
        score = 0;

    return score;
}

const char *get_risk_level(int score)
{
    if (score >= 75)
        return "LOW";

    if (score >= 50)
        return "MODERATE";

    return "HIGH";
}