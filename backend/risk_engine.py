"""Weighted, transparent FoodSafe demo risk engine.

All detailed compliance/inspection records in this project are SIMULATED DEMO DATA,
not actual findings or official ratings for any named establishment.
"""
from datetime import date
from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parents[1] / 'database' / 'foodsafe.db'


def _age_days(value):
    try:
        return max(0, (date.today() - date.fromisoformat(str(value)[:10])).days)
    except Exception:
        return 9999


def _get_assessment(rest):
    # Allow callers/tests to pass joined compliance fields directly; otherwise read the normalized table.
    if rest.get('license_validity') is not None and rest.get('inspection_status') is not None:
        return dict(rest)
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM compliance_assessments WHERE restaurant_id=?', (rest.get('id'),)).fetchone()
        con.close()
        return dict(row) if row else {}
    except Exception:
        return {}


def calculate(rest, verified_reports=None, pending_reports=None, inventory_incidents=None):
    a = _get_assessment(rest)
    vr = int(rest.get('verified_reports') or 0) if verified_reports is None else int(verified_reports)
    pr = int(rest.get('pending_reports') or 0) if pending_reports is None else int(pending_reports)
    inv = int(rest.get('inventory_incidents') or 0) if inventory_incidents is None else int(inventory_incidents)
    name = str(rest.get('name') or 'Restaurant')
    age = _age_days(a.get('inspection_date') or rest.get('last_updated'))

    license_map = {'VALID': 0, 'PENDING': -12, 'EXPIRED': -24, 'INVALID': -30}
    inspection_map = {'PASSED': 0, 'OVERDUE': -8, 'NOT_DONE': -12, 'NOTICE': -10, 'FAILED': -20}
    finding_map = {'NONE': 0, 'MINOR': -4, 'MAJOR': -10, 'CRITICAL': -18, 'UNKNOWN': -3}
    notice_map = {'NONE': 0, 'CORRECTIVE_NOTICE': -6, 'STOP_SERVICE': -20}
    corrective_map = {'NOT_REQUIRED': 0, 'COMPLETED': 3, 'IN_PROGRESS': -3, 'FAILED': -10}
    reopening_map = {'NOT_REQUIRED': 0, 'APPROVED': 2, 'PENDING': -8, 'NOT_APPROVED': -20}
    sample_map = {'PASS': 0, 'PENDING': -3, 'FAIL': -15}
    pest_map = {'COMPLIANT': 0, 'OVERDUE': -4, 'INFESTATION': -12}
    water_map = {'PASS': 0, 'PENDING': -3, 'FAIL': -12}
    cold_map = {'COMPLIANT': 0, 'WARNING': -4, 'FAILED': -12}
    training_map = {'CURRENT': 0, 'PARTIAL': -3, 'EXPIRED': -7}
    trace_map = {'COMPLETE': 0, 'PARTIAL': -3, 'MISSING': -7}

    def lookup(mapping, value, default=-4):
        return mapping.get(str(value or '').upper(), default)

    license_validity = str(a.get('license_validity') or ('VALID' if str(rest.get('license_status','')).lower()=='verified' else 'PENDING')).upper()
    inspection_status = str(a.get('inspection_status') or ('PASSED' if str(rest.get('inspection','')).lower()=='available' else 'OVERDUE')).upper()
    findings = str(a.get('inspection_findings') or 'UNKNOWN').upper()
    notice = str(a.get('notice_status') or 'NONE').upper()
    corrective = str(a.get('corrective_action_status') or 'NOT_REQUIRED').upper()
    reopening = str(a.get('reopening_permission') or 'NOT_REQUIRED').upper()
    hygiene = max(0, min(100, int(a.get('hygiene_score') or 70)))
    food_sample = str(a.get('food_sample_status') or 'PENDING').upper()
    pest = str(a.get('pest_control_status') or 'OVERDUE').upper()
    water = str(a.get('water_quality_status') or 'PENDING').upper()
    cold = str(a.get('cold_chain_status') or 'WARNING').upper()
    training = str(a.get('staff_training_status') or 'PARTIAL').upper()
    traceability = str(a.get('traceability_status') or 'PARTIAL').upper()

    # Raw penalties are assigned to explicit categories. Each category has a cap,
    # preventing correlated findings from being counted repeatedly without limit.
    raw_factors = [
        ('License validity', license_validity, lookup(license_map, license_validity, -12), 'regulatory'),
        ('Inspection status', inspection_status, lookup(inspection_map, inspection_status, -8), 'inspection'),
        ('Inspection findings', findings, lookup(finding_map, findings, -4), 'inspection'),
        ('Notice / enforcement status', notice, lookup(notice_map, notice, -6), 'enforcement'),
        ('Corrective action follow-up', corrective, lookup(corrective_map, corrective, -3), 'enforcement'),
        ('Reopening permission', reopening, lookup(reopening_map, reopening, -8) if int(a.get('reopening_required') or 0) else 0, 'enforcement'),
        ('Hygiene inspection score', f'{hygiene}/100', -round((100-hygiene)*0.20), 'hygiene'),
        ('Food sample testing', food_sample, lookup(sample_map, food_sample, -3), 'food_controls'),
        ('Pest control', pest, lookup(pest_map, pest, -4), 'food_controls'),
        ('Water quality', water, lookup(water_map, water, -3), 'food_controls'),
        ('Cold-chain / temperature control', cold, lookup(cold_map, cold, -4), 'food_controls'),
        ('Staff food-safety training', training, lookup(training_map, training, -3), 'staff_traceability'),
        ('Ingredient traceability', traceability, lookup(trace_map, traceability, -3), 'staff_traceability'),
        ('Confirmed violations', str(int(rest.get('violations') or 0)), -min(int(rest.get('violations') or 0)*4,16), 'history'),
        ('Verified reports', str(vr), -min(round(vr*1.5),9), 'history'),
        ('Pending reports', str(pr), -min(round(pr*0.75),4), 'history'),
        ('Inventory incidents', str(inv), -min(inv*3,12), 'history'),
        ('Inspection recency', f'{age} day(s) since inspection', 0 if age <= 90 else -3 if age <= 180 else -6, 'recency'),
    ]
    # Category caps are the final weights. Their maximum combined deduction is 95
    # points, so even a compound worst-case scenario remains distinguishable.
    group_caps = {
        'regulatory': 16, 'inspection': 16, 'enforcement': 14,
        'hygiene': 12, 'food_controls': 16, 'staff_traceability': 7,
        'history': 10, 'recency': 4,
    }
    negative_totals = {}
    for _, _, points, group in raw_factors:
        if points < 0:
            negative_totals[group] = negative_totals.get(group, 0) + abs(int(points))
    scaled = []
    for label, value, points, group in raw_factors:
        weighted = int(points)
        total_negative = negative_totals.get(group, 0)
        cap = group_caps[group]
        if weighted < 0 and total_negative > cap:
            weighted = -int(round(abs(weighted) * cap / total_negative))
        scaled.append([label, value, weighted, group])
    # Correct any rounding overrun by trimming the last negative factor in a group.
    for group, cap in group_caps.items():
        indexes = [i for i, row in enumerate(scaled) if row[3] == group and row[2] < 0]
        current = sum(abs(scaled[i][2]) for i in indexes)
        overflow = current - cap
        for i in reversed(indexes):
            if overflow <= 0:
                break
            reduction = min(overflow, abs(scaled[i][2]))
            scaled[i][2] += reduction
            overflow -= reduction

    score = 100
    factor_rows = []
    for label, value, points, group in scaled:
        score = max(0, min(100, score + int(points)))
        factor_rows.append({
            'name': label,
            'category': group,
            'value': value,
            'impact': 'positive' if int(points) > 0 else 'negative' if int(points) < 0 else 'neutral',
            'points': int(points),
            'score_after_factor': score,
        })
    level = 'LOW' if score >= 80 else 'MODERATE' if score >= 60 else 'HIGH'
    return {
        'score': int(score),
        'level': level,
        'factors': factor_rows,
        'data_status': 'SIMULATED DEMO DATA - NOT AN ACTUAL INSPECTION RECORD',
        'explanation': 'Weighted prototype indicator: license, inspection findings, enforcement/notice and reopening status, corrective actions, hygiene, food sampling, pest/water/cold-chain controls, staff training, traceability, reports, inventory incidents and inspection recency. The detailed assessment data is simulated for demonstration, not an official rating or a claim about the named restaurant.',
        'weights': {
            'license_validity': license_map,
            'inspection_status': inspection_map,
            'inspection_findings': finding_map,
            'notice_status': notice_map,
            'corrective_action_status': corrective_map,
            'reopening_permission': reopening_map,
            'hygiene_score': 'deduction = round((100 - hygiene_score) * 0.20)',
            'food_sample_status': sample_map,
            'pest_control_status': pest_map,
            'water_quality_status': water_map,
            'cold_chain_status': cold_map,
            'staff_training_status': training_map,
            'traceability_status': trace_map,
            'confirmed_violations': '−4 each, category-capped with reports and inventory incidents',
            'verified_reports': '−1.5 each, category-capped with other historical signals',
            'pending_reports': '−0.75 each, category-capped with other historical signals',
            'inventory_incidents': '−3 each, category-capped with other historical signals',
            'inspection_recency': '0 to −6 based on age; category capped at −4',
            'category_caps': group_caps,
        },
    }
