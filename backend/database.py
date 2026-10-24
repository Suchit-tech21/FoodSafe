from pathlib import Path
import sqlite3
from datetime import date, timedelta, datetime

BASE = Path(__file__).resolve().parents[1]
DB = BASE / 'database' / 'foodsafe.db'
DB.parent.mkdir(exist_ok=True)


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c


def add_column_if_missing(c, table, column, definition):
    columns = [x['name'] for x in c.execute(f'PRAGMA table_info({table})').fetchall()]

    if column not in columns:
        c.execute(
            f'ALTER TABLE {table} ADD COLUMN {column} {definition}'
        )


def init_db():
    c = conn()

    c.executescript('''
    CREATE TABLE IF NOT EXISTS restaurants(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        area TEXT NOT NULL,
        license TEXT,
        license_status TEXT,
        inspection TEXT,
        violations INTEGER DEFAULT 0,
        verified_reports INTEGER DEFAULT 0,
        pending_reports INTEGER DEFAULT 0,
        inventory_incidents INTEGER DEFAULT 0,
        last_updated TEXT
    );

    CREATE TABLE IF NOT EXISTS complaints(
        id TEXT PRIMARY KEY,
        restaurant_id INTEGER NOT NULL,
        category TEXT,
        severity INTEGER,
        description TEXT,
        location TEXT,
        bill_reference TEXT,
        evidence_path TEXT,
        verification_status TEXT,
        priority TEXT,
        priority_score REAL,
        timestamp TEXT,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        product TEXT,
        batch_number TEXT,
        quantity INTEGER,
        purchase_date TEXT,
        expiry_date TEXT,
        supplier TEXT,
        status TEXT,
        disposed INTEGER DEFAULT 0,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS provenance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER,
        type TEXT,
        title TEXT,
        source TEXT,
        source_reference TEXT,
        verification_status TEXT,
        evidence TEXT,
        timestamp TEXT,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        display_name TEXT,
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS complaint_reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        decision TEXT NOT NULL,
        remarks TEXT,
        timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS verified_visits(
        id TEXT PRIMARY KEY,
        restaurant_id INTEGER NOT NULL,
        methods TEXT,
        location TEXT,
        bill_reference TEXT,
        bill_evidence_path TEXT,
        verification_status TEXT,
        timestamp TEXT,
        verification_score REAL,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS compliance_assessments(
        restaurant_id INTEGER PRIMARY KEY,
        license_validity TEXT NOT NULL DEFAULT 'PENDING',
        inspection_status TEXT NOT NULL DEFAULT 'NOT_DONE',
        inspection_findings TEXT NOT NULL DEFAULT 'UNKNOWN',
        notice_status TEXT NOT NULL DEFAULT 'NONE',
        notice_deadline TEXT,
        corrective_action_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED',
        reopening_required INTEGER NOT NULL DEFAULT 0,
        reopening_permission TEXT NOT NULL DEFAULT 'NOT_REQUIRED',
        hygiene_score INTEGER NOT NULL DEFAULT 70,
        food_sample_status TEXT NOT NULL DEFAULT 'PENDING',
        pest_control_status TEXT NOT NULL DEFAULT 'OVERDUE',
        water_quality_status TEXT NOT NULL DEFAULT 'PENDING',
        cold_chain_status TEXT NOT NULL DEFAULT 'WARNING',
        staff_training_status TEXT NOT NULL DEFAULT 'PARTIAL',
        traceability_status TEXT NOT NULL DEFAULT 'PARTIAL',
        inspection_date TEXT,
        last_review_date TEXT,
        assessment_source TEXT NOT NULL DEFAULT 'FoodSafe demo dataset',
        data_status TEXT NOT NULL DEFAULT 'SIMULATED DEMO SCENARIO',
        notes TEXT,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS inspection_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        inspection_date TEXT NOT NULL,
        inspector_type TEXT,
        outcome TEXT,
        findings TEXT,
        notice_issued TEXT,
        corrective_due_date TEXT,
        follow_up_result TEXT,
        reopening_permission TEXT,
        notes TEXT,
        data_status TEXT NOT NULL DEFAULT 'SIMULATED DEMO SCENARIO',
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS enforcement_actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        issued_date TEXT,
        due_date TEXT,
        status TEXT,
        reason TEXT,
        resolved_date TEXT,
        data_status TEXT NOT NULL DEFAULT 'SIMULATED DEMO SCENARIO',
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );
    ''')

    # ---------------------------------------------------------
    # GPS SUPPORT
    # ---------------------------------------------------------
    # Safe migration for an existing FoodSafe database.
    add_column_if_missing(c, 'restaurants', 'latitude', 'REAL')
    add_column_if_missing(c, 'restaurants', 'longitude', 'REAL')
    add_column_if_missing(c, 'restaurants', 'address', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'cuisine', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'popular_food', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'price_range', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'phone', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'image_url', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'image_type', 'TEXT')
    add_column_if_missing(c, 'restaurants', 'data_status', 'TEXT')
    add_column_if_missing(c, 'complaints', 'bill_evidence_path', 'TEXT')

    add_column_if_missing(c, 'verified_visits', 'latitude', 'REAL')
    add_column_if_missing(c, 'verified_visits', 'longitude', 'REAL')
    add_column_if_missing(c, 'verified_visits', 'distance_meters', 'REAL')

    # ---------------------------------------------------------
    # DEMO USERS
    # ---------------------------------------------------------
    if c.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash

        c.execute(
            '''
            INSERT INTO users(username,password_hash,role,display_name)
            VALUES(?,?,?,?)
            ''',
            (
                'admin',
                generate_password_hash('admin123'),
                'ADMIN',
                'FoodSafe Administrator'
            )
        )

        c.execute(
            '''
            INSERT INTO users(username,password_hash,role,display_name)
            VALUES(?,?,?,?)
            ''',
            (
                'moderator',
                generate_password_hash('mod123'),
                'MODERATOR',
                'Food Safety Moderator'
            )
        )

        c.execute(
            '''
            INSERT INTO users(username,password_hash,role,display_name)
            VALUES(?,?,?,?)
            ''',
            (
                'business',
                generate_password_hash('biz123'),
                'BUSINESS',
                'Restaurant Manager'
            )
        )

    # ---------------------------------------------------------
    # PRIMARY ADMIN ACCOUNT
    # ---------------------------------------------------------
    # Keep the project owner's admin credentials synchronized so an
    # existing database cannot retain the old demo admin password.
    # This is intentionally done at startup because the project is a
    # local/demo application.
    from werkzeug.security import generate_password_hash

    admin_hash = 'scrypt:32768:8:1$SuchitSalt123456$50eed0222680af3cc9641406eb05d7e13128fd55b8530f206c6f406cdacad04c768fd024adf91fe976f388d1cda08d87e9bd0fc4a3e63fb4908541e02d128b8b'
    existing_admin = c.execute(
        'SELECT id FROM users WHERE username=?',
        ('Suchit',)
    ).fetchone()

    if existing_admin:
        c.execute(
            '''UPDATE users
               SET password_hash=?, role='ADMIN', display_name=?, active=1
               WHERE username=?''',
            (admin_hash, 'Suchit', 'Suchit')
        )
    else:
        c.execute(
            '''INSERT INTO users(username,password_hash,role,display_name,active)
               VALUES(?,?,?,?,1)''',
            ('Suchit', admin_hash, 'ADMIN', 'Suchit')
        )

    # Disable the old demo admin account so there is one clear admin
    # login for the project. Other existing users are preserved.
    c.execute(
        "UPDATE users SET active=0 WHERE username='admin' AND username<>'Suchit'"
    )

    # Restaurant management demo account. Restaurant scope is selected at login
    # and enforced by the server for every management inventory request.
    manager_hash = generate_password_hash('FoodSafe@2107')
    existing_manager = c.execute("SELECT id FROM users WHERE username='restaurant'").fetchone()
    if existing_manager:
        c.execute("UPDATE users SET password_hash=?, role='BUSINESS', display_name='Restaurant Staff', active=1 WHERE username='restaurant'", (manager_hash,))
    else:
        c.execute("INSERT INTO users(username,password_hash,role,display_name,active) VALUES(?,?,?,?,1)", ('restaurant', manager_hash, 'BUSINESS', 'Restaurant Staff'))

    # ---------------------------------------------------------
    # DEMO RESTAURANTS
    # ---------------------------------------------------------
    if c.execute('SELECT COUNT(*) FROM restaurants').fetchone()[0] == 0:

        # Demo coordinates for GPS-distance validation.
        # These are prototype coordinates, not official restaurant
        # addresses.
        rs = [
            (
                'Green Leaf Restaurant',
                'Kothrud',
                'FSSAI-100245',
                'Verified',
                'Available',
                1, 3, 1, 0,
                18.5074,
                73.8077
            ),
            (
                'Spice Garden',
                'Baner',
                'FSSAI-100821',
                'Verified',
                'Available',
                0, 1, 0, 0,
                18.5590,
                73.7868
            ),
            (
                'Royal Tandoor',
                'Hinjewadi',
                'FSSAI-100912',
                'Verified',
                'Available',
                3, 7, 2, 2,
                18.5913,
                73.7389
            ),
            (
                'Healthy Bites',
                'Shivajinagar',
                'FSSAI-101104',
                'Verified',
                'Available',
                0, 0, 0, 0,
                18.5308,
                73.8470
            ),
            (
                'Urban Spice Kitchen',
                'Viman Nagar',
                'FSSAI-101230',
                'Verified',
                'Available',
                1, 2, 1, 0,
                18.5679,
                73.9143
            ),
            (
                'Fresh Corner Cafe',
                'FC Road',
                'FSSAI-101451',
                'Verified',
                'Available',
                0, 1, 0, 0,
                18.5289,
                73.8400
            ),
            (
                'Taste Junction',
                'Wakad',
                'FSSAI-101772',
                'Verified',
                'Available',
                2, 4, 1, 1,
                18.5975,
                73.7633
            ),
            (
                'Green Bowl',
                'Aundh',
                'FSSAI-101883',
                'Verified',
                'Available',
                0, 0, 1, 0,
                18.5596,
                73.8073
            )
        ]

        c.executemany(
            '''
            INSERT INTO restaurants(
                name,
                area,
                license,
                license_status,
                inspection,
                violations,
                verified_reports,
                pending_reports,
                inventory_incidents,
                latitude,
                longitude,
                last_updated
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            [
                r[:11] + (date.today().isoformat(),)
                for r in rs
            ]
        )

        # -----------------------------------------------------
        # PROVENANCE
        # -----------------------------------------------------
        for rid in range(1, 9):
            c.execute(
                '''
                INSERT INTO provenance(
                    restaurant_id,
                    type,
                    title,
                    source,
                    source_reference,
                    verification_status,
                    evidence,
                    timestamp
                )
                VALUES(?,?,?,?,?,?,?,?)
                ''',
                (
                    rid,
                    'OFFICIAL',
                    'Food Safety License',
                    'FSSAI / State Food Safety Authority',
                    f'DEMO-OFFICIAL-{rid}',
                    'Verified',
                    'Prototype/curated record',
                    date.today().isoformat()
                )
            )

        extra = [
            (
                1,
                'VERIFIED',
                'Hygiene Inspection',
                'FoodSafe verified inspection',
                'DEMO-VERIFIED-1',
                'Verified',
                'Inspection record available',
                '2026-08-20'
            ),
            (
                1,
                'EXTERNAL',
                'Public Food Safety Information',
                'Public announcement',
                'DEMO-EXTERNAL-1',
                'External source',
                'Publicly available information',
                '2026-08-15'
            ),
            (
                1,
                'USER REPORTED',
                'Food Handling Complaint',
                'FoodSafe user',
                'DEMO-USER-1',
                'Pending',
                'User-submitted report',
                '2026-09-10'
            ),
            (
                3,
                'VERIFIED',
                'Previous Hygiene Finding',
                'FoodSafe verified report',
                'DEMO-VERIFIED-3',
                'Verified',
                'Evidence-backed report',
                '2026-08-10'
            )
        ]

        c.executemany(
            '''
            INSERT INTO provenance(
                restaurant_id,
                type,
                title,
                source,
                source_reference,
                verification_status,
                evidence,
                timestamp
            )
            VALUES(?,?,?,?,?,?,?,?)
            ''',
            extra
        )

        # -----------------------------------------------------
        # INVENTORY
        # -----------------------------------------------------
        today = date.today()

        inv = [
            (
                1,
                'Milk',
                'MLK2390',
                10,
                (today - timedelta(days=5)).isoformat(),
                (today + timedelta(days=1)).isoformat(),
                'Fresh Dairy'
            ),
            (
                1,
                'Paneer',
                'PNR2390',
                8,
                (today - timedelta(days=4)).isoformat(),
                (today + timedelta(days=2)).isoformat(),
                'Fresh Dairy'
            ),
            (
                1,
                'Sauce',
                'SAU4412',
                12,
                (today - timedelta(days=9)).isoformat(),
                (today + timedelta(days=20)).isoformat(),
                'Food Supplier'
            ),
            (
                3,
                'Chicken',
                'CHK2201',
                15,
                (today - timedelta(days=3)).isoformat(),
                (today - timedelta(days=1)).isoformat(),
                'Prime Meats'
            ),
            (
                2,
                'Rice',
                'RCE1102',
                25,
                (today - timedelta(days=10)).isoformat(),
                (today + timedelta(days=30)).isoformat(),
                'Grain House'
            )
        ]

        for x in inv:
            status, _ = inventory_status(x[5], today)

            c.execute(
                '''
                INSERT INTO inventory(
                    restaurant_id,
                    product,
                    batch_number,
                    quantity,
                    purchase_date,
                    expiry_date,
                    supplier,
                    status
                )
                VALUES(?,?,?,?,?,?,?,?)
                ''',
                x[:7] + (status,)
            )

        # -----------------------------------------------------
        # DEMO COMPLAINTS
        # -----------------------------------------------------
        comps = [
            (
                'CMP-1001',
                1,
                'Hygiene',
                8,
                'Improper food handling observed.',
                'Kothrud',
                'BILL-1001',
                '',
                'VERIFIED',
                78
            ),
            (
                'CMP-1002',
                3,
                'Expired Food',
                9,
                'Expired food product reported.',
                'Hinjewadi',
                'BILL-1002',
                'USER REPORT',
                'PENDING',
                86
            ),
            (
                'CMP-1003',
                1,
                'Storage',
                5,
                'Cold storage temperature concern.',
                'Kothrud',
                '',
                'Inspection record',
                'VERIFIED',
                55
            )
        ]

        for (
            cid,
            rid,
            cat,
            sev,
            desc,
            loc,
            bill,
            evid,
            ver,
            score
        ) in comps:

            pri = (
                'HIGH'
                if score >= 70
                else 'MEDIUM'
                if score >= 40
                else 'LOW'
            )

            c.execute(
                '''
                INSERT INTO complaints(
                    id,
                    restaurant_id,
                    category,
                    severity,
                    description,
                    location,
                    bill_reference,
                    evidence_path,
                    verification_status,
                    priority,
                    priority_score,
                    timestamp
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (
                    cid,
                    rid,
                    cat,
                    sev,
                    desc,
                    loc,
                    bill,
                    evid,
                    ver,
                    pri,
                    score,
                    datetime.now().isoformat(timespec='minutes')
                )
            )

    # ---------------------------------------------------------
    # COMPLIANCE / ENFORCEMENT DEMO DATA
    # These are simulated examples for the hackathon prototype,
    # NOT actual findings or enforcement records for real businesses.
    # ---------------------------------------------------------
    demo_assessments = {
        1:  ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',91,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-12','Minor handwashing signage improvement completed.'),
        2:  ('VALID','PASSED','NONE','NONE',None,'NOT_REQUIRED',0,'NOT_REQUIRED',92,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-18','Routine inspection passed in the simulated scenario.'),
        3:  ('VALID','FAILED','MAJOR','CORRECTIVE_NOTICE','2026-10-20','IN_PROGRESS',0,'NOT_REQUIRED',74,'PENDING','OVERDUE','PASS','WARNING','PARTIAL','PARTIAL','2026-09-20','Major storage and sanitation findings; corrective action still open.'),
        4:  ('VALID','PASSED','NONE','NONE',None,'NOT_REQUIRED',0,'NOT_REQUIRED',96,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-22','Good simulated hygiene and traceability indicators.'),
        5:  ('VALID','NOTICE','MINOR','CORRECTIVE_NOTICE','2026-10-18','COMPLETED',1,'APPROVED',79,'PASS','OVERDUE','PASS','WARNING','CURRENT','PARTIAL','2026-09-14','Improvement notice closed after follow-up; reopening permission recorded in demo scenario.'),
        6:  ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',88,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-25','Minor observation resolved during inspection.'),
        7:  ('VALID','FAILED','CRITICAL','STOP_SERVICE','2026-10-16','FAILED',1,'NOT_APPROVED',48,'FAIL','INFESTATION','FAIL','FAILED','EXPIRED','MISSING','2026-09-26','Failed follow-up after notice; reopening not approved in simulated case.'),
        8:  ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',84,'PASS','COMPLIANT','PASS','WARNING','CURRENT','COMPLETE','2026-09-17','One minor cold-storage log issue corrected.'),
        9:  ('VALID','PASSED','NONE','NONE',None,'NOT_REQUIRED',0,'NOT_REQUIRED',93,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-21','Routine inspection scenario passed.'),
        10: ('VALID','NOTICE','MINOR','CORRECTIVE_NOTICE','2026-10-22','COMPLETED',1,'APPROVED',86,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-28','Notice-period improvements completed and follow-up approved in demo scenario.'),
        11: ('VALID','OVERDUE','UNKNOWN','NONE',None,'IN_PROGRESS',0,'NOT_REQUIRED',78,'PENDING','OVERDUE','PENDING','WARNING','PARTIAL','PARTIAL','2026-06-12','Inspection follow-up due; no adverse finding is asserted.'),
        12: ('PENDING','NOTICE','MAJOR','CORRECTIVE_NOTICE','2026-10-15','IN_PROGRESS',0,'NOT_REQUIRED',68,'PENDING','OVERDUE','PENDING','WARNING','PARTIAL','PARTIAL','2026-09-11','License documentation and major hygiene corrections awaiting review in demo scenario.'),
        13: ('INVALID','FAILED','MAJOR','STOP_SERVICE','2026-10-13','FAILED',1,'NOT_APPROVED',55,'FAIL','INFESTATION','PENDING','FAILED','EXPIRED','MISSING','2026-09-08','Invalid license and failed corrective follow-up in simulated case.'),
        14: ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',89,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-24','Minor observation corrected.'),
        15: ('VALID','PASSED','NONE','NONE',None,'NOT_REQUIRED',0,'NOT_REQUIRED',97,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-27','All sample compliance factors marked satisfactory for the demo.'),
        16: ('EXPIRED','NOTICE','MINOR','CORRECTIVE_NOTICE','2026-10-17','IN_PROGRESS',0,'NOT_REQUIRED',70,'PENDING','OVERDUE','PASS','WARNING','PARTIAL','PARTIAL','2026-09-15','License renewal pending and improvement notice open in simulated scenario.'),
        17: ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',85,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-16','Routine check passed after minor record correction.'),
        18: ('PENDING','OVERDUE','UNKNOWN','NONE',None,'IN_PROGRESS',0,'NOT_REQUIRED',73,'PENDING','OVERDUE','PASS','WARNING','PARTIAL','PARTIAL','2026-06-30','License verification and inspection update are pending in demo scenario.'),
        19: ('INVALID','FAILED','CRITICAL','STOP_SERVICE','2026-10-14','FAILED',1,'NOT_APPROVED',52,'FAIL','INFESTATION','FAIL','FAILED','EXPIRED','MISSING','2026-09-07','Invalid license, critical finding and failed follow-up in simulated case.'),
        20: ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',90,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-23','Minor labeling observation closed in demo scenario.'),
        21: ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',82,'PASS','COMPLIANT','PASS','WARNING','CURRENT','COMPLETE','2026-09-19','Minor temperature-log improvement completed.'),
        22: ('VALID','PASSED','NONE','NONE',None,'NOT_REQUIRED',0,'NOT_REQUIRED',94,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-26','Routine inspection scenario passed.'),
        23: ('PENDING','NOTICE','MAJOR','CORRECTIVE_NOTICE','2026-10-19','IN_PROGRESS',0,'NOT_REQUIRED',72,'PASS','OVERDUE','PASS','WARNING','PARTIAL','PARTIAL','2026-09-13','Notice-period improvement work remains in progress in simulated case.'),
        24: ('VALID','PASSED','MINOR','NONE',None,'COMPLETED',0,'NOT_REQUIRED',87,'PASS','COMPLIANT','PASS','COMPLIANT','CURRENT','COMPLETE','2026-09-24','Minor storage observation corrected.'),
        25: ('EXPIRED','FAILED','CRITICAL','STOP_SERVICE','2026-10-12','FAILED',1,'NOT_APPROVED',45,'FAIL','INFESTATION','FAIL','FAILED','EXPIRED','MISSING','2026-09-06','Expired license and failed critical corrective actions in simulated case.'),
    }
    for rid, values in demo_assessments.items():
        if c.execute('SELECT 1 FROM restaurants WHERE id=?', (rid,)).fetchone() is None:
            continue
        existing = c.execute('SELECT 1 FROM compliance_assessments WHERE restaurant_id=?', (rid,)).fetchone()
        if not existing:
            (license_validity, inspection_status, findings, notice_status, deadline,
             corrective, reopening_required, reopening_permission, hygiene, food_sample,
             pest, water, cold, training, traceability, inspection_date, notes) = values
            c.execute('''INSERT INTO compliance_assessments(
                restaurant_id,license_validity,inspection_status,inspection_findings,notice_status,
                notice_deadline,corrective_action_status,reopening_required,reopening_permission,
                hygiene_score,food_sample_status,pest_control_status,water_quality_status,
                cold_chain_status,staff_training_status,traceability_status,inspection_date,
                last_review_date,assessment_source,data_status,notes)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (rid,license_validity,inspection_status,findings,notice_status,deadline,corrective,
                 reopening_required,reopening_permission,hygiene,food_sample,pest,water,cold,training,
                 traceability,inspection_date,date.today().isoformat(),'FoodSafe curated demo scenario',
                 'SIMULATED DEMO DATA - NOT AN ACTUAL INSPECTION RECORD',notes))
        # Keep the legacy summary fields coherent with the richer current assessment.
        row = c.execute('SELECT license_validity,inspection_status FROM compliance_assessments WHERE restaurant_id=?',(rid,)).fetchone()
        if row:
            license_display = {'VALID':'Verified','PENDING':'Pending','EXPIRED':'Expired','INVALID':'Invalid'}.get(row['license_validity'],'Pending')
            inspection_display = {'PASSED':'Available','NOTICE':'Notice Period','FAILED':'Failed','OVERDUE':'Overdue','NOT_DONE':'Not Done'}.get(row['inspection_status'],'Verify status')
            c.execute('UPDATE restaurants SET license_status=?, inspection=?, data_status=? WHERE id=?',
                      (license_display,inspection_display,'SIMULATED DEMO DATA - NOT AN ACTUAL INSPECTION RECORD',rid))

    # Keep one illustrative inspection history and enforcement action per seeded scenario.
    for rid, values in demo_assessments.items():
        if c.execute('SELECT 1 FROM restaurants WHERE id=?',(rid,)).fetchone() is None:
            continue
        a = c.execute('SELECT * FROM compliance_assessments WHERE restaurant_id=?',(rid,)).fetchone()
        if a and not c.execute('SELECT 1 FROM inspection_history WHERE restaurant_id=?',(rid,)).fetchone():
            outcome = {'PASSED':'PASS','NOTICE':'NOTICE ISSUED','FAILED':'FAIL','OVERDUE':'FOLLOW-UP DUE','NOT_DONE':'NOT DONE'}.get(a['inspection_status'],'REVIEW')
            findings_text = f"{a['inspection_findings']} findings; hygiene score {a['hygiene_score']}/100; sample {a['food_sample_status']}"
            c.execute('''INSERT INTO inspection_history(restaurant_id,inspection_date,inspector_type,outcome,findings,notice_issued,corrective_due_date,follow_up_result,reopening_permission,notes,data_status)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                      (rid,a['inspection_date'] or date.today().isoformat(),'FoodSafe demo inspector',outcome,findings_text,a['notice_status'],a['notice_deadline'],a['corrective_action_status'],a['reopening_permission'],a['notes'],'SIMULATED DEMO DATA - NOT AN ACTUAL INSPECTION RECORD'))
        if a and a['notice_status']!='NONE' and not c.execute('SELECT 1 FROM enforcement_actions WHERE restaurant_id=?',(rid,)).fetchone():
            c.execute('''INSERT INTO enforcement_actions(restaurant_id,action_type,issued_date,due_date,status,reason,resolved_date,data_status)
                         VALUES(?,?,?,?,?,?,?,?)''',
                      (rid,a['notice_status'],a['inspection_date'],a['notice_deadline'],a['corrective_action_status'],a['notes'],date.today().isoformat() if a['corrective_action_status']=='COMPLETED' else None,'SIMULATED DEMO DATA - NOT AN ACTUAL ENFORCEMENT RECORD'))

    # Multi-step notice/follow-up examples make the enforcement lifecycle explicit.
    # These are deliberately marked simulated and must not be represented as real FSSAI actions.
    event_sequences = {
        5: [
            ('2026-09-14','ROUTINE INSPECTION','NOTICE ISSUED','MINOR observations; improvement notice issued','CORRECTIVE_NOTICE','2026-09-28','IN_PROGRESS','NOT_REQUIRED','Simulated notice-period start.'),
            ('2026-09-28','FOLLOW-UP INSPECTION','PASS','Corrective steps verified in the demo scenario','CORRECTIVE_NOTICE','2026-10-18','COMPLETED','APPROVED','Simulated follow-up passed; reopening approval recorded.'),
        ],
        7: [
            ('2026-09-10','ROUTINE INSPECTION','FAIL','CRITICAL findings; service-stop action in demo scenario','STOP_SERVICE','2026-09-20','IN_PROGRESS','PENDING','Simulated critical findings and notice period.'),
            ('2026-09-26','FOLLOW-UP INSPECTION','FAIL','Required improvements not demonstrated in the demo scenario','STOP_SERVICE','2026-10-16','FAILED','NOT_APPROVED','Simulated follow-up failed; reopening not approved.'),
        ],
        10: [
            ('2026-09-12','ROUTINE INSPECTION','NOTICE ISSUED','MINOR corrective points raised in demo scenario','CORRECTIVE_NOTICE','2026-09-25','IN_PROGRESS','PENDING','Simulated notice period opened.'),
            ('2026-09-28','FOLLOW-UP INSPECTION','PASS','Improvement actions recorded as complete in demo scenario','CORRECTIVE_NOTICE','2026-10-22','COMPLETED','APPROVED','Simulated follow-up passed and reopening permission approved.'),
        ],
        13: [
            ('2026-09-08','DOCUMENT REVIEW','FAIL','Invalid license status in simulated record','STOP_SERVICE','2026-09-18','IN_PROGRESS','PENDING','Simulated license and compliance review.'),
            ('2026-09-24','FOLLOW-UP INSPECTION','FAIL','Corrective evidence not accepted in simulated record','STOP_SERVICE','2026-10-13','FAILED','NOT_APPROVED','Simulated follow-up failed; reopening not approved.'),
        ],
        19: [
            ('2026-09-07','ROUTINE INSPECTION','FAIL','CRITICAL findings in simulated record','STOP_SERVICE','2026-09-17','IN_PROGRESS','PENDING','Simulated notice and improvement period.'),
            ('2026-09-25','FOLLOW-UP INSPECTION','FAIL','Required improvements not demonstrated in simulated record','STOP_SERVICE','2026-10-14','FAILED','NOT_APPROVED','Simulated follow-up failed; reopening not approved.'),
        ],
        25: [
            ('2026-09-06','DOCUMENT REVIEW','FAIL','Expired license and critical control gaps in simulated record','STOP_SERVICE','2026-09-16','IN_PROGRESS','PENDING','Simulated enforcement review started.'),
            ('2026-09-24','FOLLOW-UP INSPECTION','FAIL','Corrective actions not completed in simulated record','STOP_SERVICE','2026-10-12','FAILED','NOT_APPROVED','Simulated follow-up failed; reopening not approved.'),
        ],
    }
    for rid, events in event_sequences.items():
        # Keep the initial generated history row, then add named timeline events once.
        if c.execute('SELECT COUNT(*) FROM inspection_history WHERE restaurant_id=?',(rid,)).fetchone()[0] <= 1:
            for event in events:
                (event_date, inspector, outcome, findings_text, notice_type, due_date,
                 follow_up, reopening_permission, event_notes) = event
                c.execute('''INSERT INTO inspection_history(restaurant_id,inspection_date,inspector_type,outcome,findings,notice_issued,corrective_due_date,follow_up_result,reopening_permission,notes,data_status)
                             VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                          (rid,event_date,inspector,outcome,findings_text,notice_type,due_date,follow_up,reopening_permission,event_notes,'SIMULATED DEMO DATA - NOT AN ACTUAL INSPECTION RECORD'))

    # Use the exact user-supplied photographs for the matching sign/name.
    local_images = {
        1: ('/images/restaurants/green-leaf-restaurant.png','user_uploaded_sign_match'),
        2: ('/images/restaurants/spice-garden.png','user_uploaded_sign_match'),
        3: ('/images/restaurants/royal-tandoor.png','user_uploaded_sign_match'),
        4: ('/images/restaurants/healthy-bites.png','user_uploaded_sign_match'),
        5: ('/images/restaurants/urban-spice-kitchen-sign.png','user_uploaded_name_similarity_unverified'),
        6: ('/images/restaurants/fresh-corner-cafe.png','user_uploaded_sign_match'),
        7: ('/images/restaurants/taste-junction.png','user_uploaded_sign_match'),
        8: ('/images/restaurants/green-bowl.png','user_uploaded_sign_match'),
    }
    for rid, (url, image_type) in local_images.items():
        c.execute('UPDATE restaurants SET image_url=?, image_type=? WHERE id=?', (url,image_type,rid))

    c.commit()
    c.close()


def inventory_status(expiry, today=None):
    today = today or date.today()
    d = (date.fromisoformat(expiry) - today).days

    return (
        'EXPIRED'
        if d < 0
        else 'EXPIRING SOON'
        if d <= 3
        else 'ACTIVE'
    ), d


def rows(sql, args=()):
    c = conn()
    r = [
        dict(x)
        for x in c.execute(sql, args).fetchall()
    ]
    c.close()
    return r