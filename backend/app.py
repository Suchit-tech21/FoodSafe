from flask import Flask, jsonify, request, send_from_directory, send_file, session
from pathlib import Path
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import uuid
import os
import re
import secrets
import time
import hashlib
import hmac
import base64
import urllib.parse
import urllib.request
import urllib.error
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, conn, rows, inventory_status
from risk_engine import calculate
from data_structures.service import search_restaurants, expiry_heap, ordered_complaints
from inventory_database import inv_conn, init_inventory_db, migrate_legacy_inventory

BASE = Path(__file__).resolve().parents[1]
FRONT = BASE / 'frontend'
UP = BASE / 'backend' / 'uploads'
UP.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(FRONT), static_url_path='')
app.config['SECRET_KEY'] = 'foodsafe-demo-secret-change-in-production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 11 * 1024 * 1024  # allows two evidence files up to 5 MB each

init_db()
init_inventory_db()
try:
    _main_for_inventory=conn()
    migrate_legacy_inventory(_main_for_inventory)
    _main_for_inventory.close()
except Exception:
    pass

ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}

# Real SMS OTP configuration. Copy Food_Safe/.env.example to Food_Safe/.env.
VISIT_OTPS = {}
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_SEND_COOLDOWN_SECONDS = 60
OTP_LAST_SENT = {}

def _load_local_env():
    """Load simple KEY=VALUE entries without requiring an extra package."""
    env_file = BASE / '.env'
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_local_env()

def normalize_sms_phone(value):
    phone = re.sub(r'[\s().-]', '', str(value or '').strip())
    if phone.startswith('00'):
        phone = '+' + phone[2:]
    if phone.startswith('+'):
        digits = phone[1:]
    else:
        digits = phone
        if len(digits) == 10 and digits.isdigit():
            digits = '91' + digits
    if not digits.isdigit() or not (8 <= len(digits) <= 15):
        raise ValueError('Enter a valid mobile number, including country code (for India: +91 followed by 10 digits).')
    return '+' + digits

def send_twilio_sms(to_phone, body):
    sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
    token = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
    sender = os.getenv('TWILIO_FROM_NUMBER', '').strip()
    if not (sid and token and sender) or 'replace_with_' in token.lower() or 'xxxx' in sid.lower():
        raise RuntimeError('Real SMS is not configured. Add your Twilio Account SID, Auth Token and sender number to Food_Safe/.env.')
    endpoint = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    data = urllib.parse.urlencode({'To': to_phone, 'From': sender, 'Body': body}).encode('utf-8')
    req = urllib.request.Request(endpoint, data=data, method='POST')
    credentials = base64.b64encode(f'{sid}:{token}'.encode('utf-8')).decode('ascii')
    req.add_header('Authorization', 'Basic ' + credentials)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError('The SMS provider rejected the request.')
            return response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        try:
            import json
            detail = json.loads(exc.read().decode('utf-8', errors='replace'))
            message = detail.get('message') or detail.get('detail')
        except Exception:
            message = None
        raise RuntimeError(message or f'SMS provider returned HTTP {exc.code}.') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError('Could not connect to the SMS provider. Check your internet connection.') from exc



# =========================================================
# AUTHENTICATION
# =========================================================

def current_user():
    uid = session.get('user_id')

    if not uid:
        return None

    found = rows(
        'SELECT id,username,role,display_name '
        'FROM users WHERE id=? AND active=1',
        (uid,)
    )

    return found[0] if found else None


def login_required(role=None):
    def deco(fn):

        @wraps(fn)
        def wrapped(*args, **kwargs):

            user = current_user()

            if not user:
                return json_error(
                    'Authentication required',
                    401
                )

            if role and user['role'] not in (role, 'ADMIN'):
                return json_error(
                    'Insufficient permissions',
                    403
                )

            return fn(*args, **kwargs)

        return wrapped

    return deco


def json_error(msg, status=400):
    return jsonify({'error': msg}), status


# =========================================================
# DATABASE HELPERS
# =========================================================

def restaurant(rid):

    found = rows(
        'SELECT * FROM restaurants WHERE id=?',
        (rid,)
    )

    return found[0] if found else None


def inventory_icon(category, product=''):
    text=f"{category} {product}".lower()
    for key,icon in [('dairy','🥛'),('milk','🥛'),('vegetable','🥦'),('fruit','🍎'),('meat','🍗'),('chicken','🍗'),('seafood','🐟'),('fish','🐟'),('grain','🌾'),('rice','🍚'),('oil','🫗'),('beverage','🥤'),('drink','🥤'),('spice','🌶️'),('paneer','🧀'),('bread','🍞'),('egg','🥚')]:
        if key in text:return icon
    return '🍽️'

def refresh_inventory(c=None):
    ic=inv_conn()
    for x in ic.execute('SELECT id,expiry_date,quantity,reorder_level,disposed FROM inventory').fetchall():
        st,_=inventory_status(x['expiry_date'])
        if x['disposed']:st='DISPOSED'
        elif st=='SAFE' and float(x['quantity'] or 0)<=float(x['reorder_level'] or 0):st='LOW STOCK'
        ic.execute('UPDATE inventory SET status=? WHERE id=?',(st,x['id']))
    ic.commit();ic.close()

def serialize_inv(x):
    d=dict(x);st,days=inventory_status(d.get('expiry_date'))
    if d.get('disposed'):st='DISPOSED'
    elif st=='SAFE' and float(d.get('quantity') or 0)<=float(d.get('reorder_level') or 0):st='LOW STOCK'
    d['status']=st;d['days_remaining']=days;d['icon']=inventory_icon(d.get('category','Other'),d.get('product',''))
    return d


# =========================================================
# AUTH API
# =========================================================

@app.route('/api/auth/login', methods=['POST'])
def auth_login():

    d = (
        request.get_json(silent=True)
        or request.form.to_dict()
    )

    username = str(
        d.get('username', '')
    ).strip()

    password = str(
        d.get('password', '')
    )

    u = rows(
        'SELECT * FROM users '
        'WHERE username=? AND active=1',
        (username,)
    )

    if not u or not check_password_hash(
        u[0]['password_hash'],
        password
    ):
        return json_error(
            'Invalid username or password',
            401
        )

    selected_restaurant_id = None
    if u[0]['role'] == 'BUSINESS':
        try:
            selected_restaurant_id = int(d.get('restaurant_id') or 0)
        except (TypeError, ValueError):
            selected_restaurant_id = 0
        if not selected_restaurant_id or not restaurant(selected_restaurant_id):
            return json_error('Choose a valid restaurant to manage', 400)
        session['restaurant_id'] = selected_restaurant_id
    else:
        session.pop('restaurant_id', None)

    session['user_id'] = u[0]['id']

    return jsonify({
        'authenticated': True,
        'user': {
            'username': u[0]['username'],
            'role': u[0]['role'],
            'display_name': u[0]['display_name']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():

    session.clear()

    return jsonify({
        'authenticated': False
    })


@app.route('/api/auth/me')
def auth_me():

    u = current_user()

    return jsonify({
        'authenticated': bool(u),
        'user': u
    })


# =========================================================
# FRONTEND
# =========================================================

@app.route('/')
def index():

    return send_from_directory(
        FRONT,
        'index.html'
    )


# =========================================================
# HEALTH
# =========================================================

@app.route('/api/health')
def health():

    return jsonify({
        'status': 'ok',
        'service': 'FoodSafe',
        'database': 'sqlite',
        'version': '2.0'
    })


# =========================================================
# RESTAURANTS
# =========================================================

@app.route('/api/restaurants')
def get_restaurants():

    q = request.args.get('q', '')

    rs = rows(
        'SELECT * FROM restaurants'
    )

    rs = search_restaurants(
        rs,
        q
    )

    for r in rs:

        risk_data = calculate(r)

        r['risk'] = risk_data['score']
        r['risk_level'] = risk_data['level']

    return jsonify(rs)


# =========================================================
# BINARY SEARCH API
# IMPORTANT FIX:
# Import binary_search directly from searching.py
# =========================================================

@app.route('/api/restaurants/binary-search')
def binary_search_api():

    from data_structures.searching import binary_search

    q = request.args.get('q', '').strip().lower()

    if not q:
        return json_error('q is required')

    restaurants = rows(
        'SELECT * FROM restaurants ORDER BY LOWER(name)'
    )

    # Create sorted names for Binary Search
    names = [
        r['name'].lower()
        for r in restaurants
    ]

    # binary_search() returns the matched value
    # or None when no match is found.
    found_name = binary_search(
        names,
        q
    )

    found = None

    if found_name is not None:
        for r in restaurants:
            if r['name'].lower() == found_name:
                found = r
                break

    return jsonify({
        'algorithm': 'Binary Search',
        'query': q,
        'found': found is not None,
        'restaurant': found
    })
# =========================================================
# SINGLE RESTAURANT
# =========================================================

@app.route('/api/restaurants/<int:rid>')
def get_rest(rid):

    r = restaurant(rid)

    if not r:
        return json_error(
            'Restaurant not found',
            404
        )

    risk_data = calculate(r)

    r['risk'] = risk_data['score']
    r['risk_level'] = risk_data['level']

    return jsonify(r)


# =========================================================
# RISK
# =========================================================

@app.route('/api/restaurants/<int:rid>/risk')
def risk(rid):

    r = restaurant(rid)

    if not r:
        return json_error(
            'Restaurant not found',
            404
        )

    return jsonify(
        calculate(r)
    )


# =========================================================
# PROVENANCE
# =========================================================

@app.route('/api/restaurants/<int:rid>/provenance')
def prov(rid):

    if not restaurant(rid):

        return json_error(
            'Restaurant not found',
            404
        )

    return jsonify(
        rows(
            'SELECT type,title,source,source_reference,'
            'verification_status,evidence,timestamp '
            'FROM provenance '
            'WHERE restaurant_id=? '
            'ORDER BY timestamp DESC',
            (rid,)
        )
    )


# =========================================================
# RESTAURANT QR
# =========================================================

@app.route('/api/restaurants/<int:rid>/qr')
def restaurant_qr(rid):

    if not restaurant(rid):

        return json_error(
            'Restaurant not found',
            404
        )

    try:

        import qrcode
        from io import BytesIO

        img = qrcode.make(
            f'http://127.0.0.1:5000/?restaurant={rid}'
        )

        buf = BytesIO()

        img.save(
            buf,
            format='PNG'
        )

        buf.seek(0)

        return send_file(
            buf,
            mimetype='image/png',
            download_name=f'foodsafe-restaurant-{rid}.png'
        )

    except ImportError:

        return json_error(
            'QR support is optional; install qrcode with requirements.txt',
            503
        )


# =========================================================
# COMPLAINTS
# =========================================================

@app.route('/api/complaints')
def complaints():

    data = rows(
        'SELECT c.*,r.name restaurant,r.area '
        'FROM complaints c '
        'JOIN restaurants r ON r.id=c.restaurant_id'
    )

    return jsonify(
        ordered_complaints(data)
    )


@app.route('/api/complaints', methods=['POST'])
def add_complaint():

    d = (
        request.form.to_dict()
        if request.form
        else (
            request.get_json(silent=True)
            or {}
        )
    )

    try:

        rid = int(
            d.get('restaurant_id') or 0
        )

    except (ValueError, TypeError):

        rid = 0

    r = restaurant(rid)

    if not r:

        return json_error(
            'Valid restaurant is required'
        )

    cat = str(
        d.get('category', 'Other')
    ).strip()

    desc = str(
        d.get('description', '')
    ).strip()

    loc = str(
        d.get('location') or r['area']
    ).strip()

    if not desc:

        return json_error(
            'Description is required'
        )

    try:

        sev = max(
            1,
            min(
                10,
                int(
                    d.get(
                        'severity',
                        5
                    )
                )
            )
        )

    except (ValueError, TypeError):

        return json_error(
            'Severity must be 1-10'
        )

    evidence = request.files.get('evidence')
    bill_evidence = request.files.get('bill_evidence')
    evidence_present = bool(evidence and evidence.filename)
    bill_present = bool(bill_evidence and bill_evidence.filename)

    independent_reports = int(
        r['verified_reports']
    )

    previous_violations = int(
        r['violations']
    )

    try:

        submitted_at = str(
            d.get('timestamp') or ''
        ).strip()

        if submitted_at:

            ts = datetime.fromisoformat(
                submitted_at
            ).isoformat(
                timespec='minutes'
            )

        else:

            ts = datetime.now().isoformat(
                timespec='minutes'
            )

    except ValueError:

        return json_error(
            'Invalid date/time'
        )

    # IEEE complaint priority formula
    age_bonus = 5

    score = (
        sev * 6
        + (18 if evidence_present else 0)
        + min(independent_reports * 2, 10)
        + min(previous_violations * 3, 9)
        + age_bonus
    )

    priority = (
        'HIGH'
        if score >= 70
        else 'MEDIUM'
        if score >= 40
        else 'LOW'
    )

    cid = (
        'CMP-'
        + str(uuid.uuid4().int)[:6]
    )

    path = ''

    if evidence_present:

        original = secure_filename(
            evidence.filename
        )

        ext = (
            original.rsplit('.', 1)[-1].lower()
            if '.' in original
            else ''
        )

        if ext not in ALLOWED:

            return json_error(
                'Evidence must be JPG, PNG or WEBP'
            )

        path = (
            f'uploads/{cid}.{ext}'
        )

        evidence_target = UP / f'{cid}.{ext}'
        evidence.save(evidence_target)
        if evidence_target.stat().st_size > 5 * 1024 * 1024:
            evidence_target.unlink(missing_ok=True)
            return json_error('Evidence photo must be 5 MB or smaller')

    bill_path = ''
    if bill_present:
        bill_original = secure_filename(bill_evidence.filename)
        bill_ext = bill_original.rsplit('.', 1)[-1].lower() if '.' in bill_original else ''
        if bill_ext not in ALLOWED:
            return json_error('Bill evidence must be JPG, PNG or WEBP')
        bill_path = f'uploads/{cid}-bill.{bill_ext}'
        bill_target = UP / f'{cid}-bill.{bill_ext}'
        bill_evidence.save(bill_target)
        if bill_target.stat().st_size > 5 * 1024 * 1024:
            bill_target.unlink(missing_ok=True)
            (UP / f'{cid}.{ext}').unlink(missing_ok=True) if evidence_present and path else None
            return json_error('Bill/receipt image must be 5 MB or smaller')

    c = conn()

    c.execute(
        '''
        INSERT INTO complaints
        (
            id,
            restaurant_id,
            category,
            severity,
            description,
            location,
            bill_reference,
            evidence_path,
            bill_evidence_path,
            verification_status,
            priority,
            priority_score,
            timestamp
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        (
            cid, rid, cat, sev, desc, loc,
            str(d.get('bill_reference', '')).strip(),
            path, bill_path, 'PENDING', priority, score, ts
        )
    )

    c.execute(
        '''
        UPDATE restaurants
        SET pending_reports=pending_reports+1,
            last_updated=?
        WHERE id=?
        ''',
        (
            date.today().isoformat(),
            rid
        )
    )

    c.commit()
    c.close()

    return jsonify({
        'id': cid,
        'restaurant': r['name'],
        'verification_status': 'PENDING',
        'priority': priority,
        'priority_score': score,
        'timestamp': ts
    }), 201


# =========================================================
# COMPLAINT EVIDENCE
# =========================================================

@app.route('/api/complaints/<cid>/evidence')
def complaint_evidence(cid):

    found = rows(
        'SELECT evidence_path '
        'FROM complaints WHERE id=?',
        (cid,)
    )

    if (
        not found
        or not found[0]['evidence_path']
    ):

        return json_error(
            'Evidence not found',
            404
        )

    p = (
        BASE
        / 'backend'
        / found[0]['evidence_path']
    )

    if not p.is_file():

        return json_error(
            'Evidence file not found',
            404
        )

    return send_file(p)


@app.route('/api/admin/reports')
@login_required('MODERATOR')
def admin_reports():
    c = conn()
    reports = [dict(x) for x in c.execute('''
        SELECT cp.*, r.name AS restaurant, r.area,
          (SELECT json_group_array(json_object('reviewer', cr.reviewer, 'decision', cr.decision, 'remarks', cr.remarks, 'timestamp', cr.timestamp))
           FROM complaint_reviews cr WHERE cr.complaint_id=cp.id ORDER BY cr.timestamp DESC) AS review_history_json
        FROM complaints cp JOIN restaurants r ON r.id=cp.restaurant_id
        ORDER BY CASE WHEN cp.verification_status='PENDING' THEN 0 ELSE 1 END, cp.timestamp DESC
    ''').fetchall()]
    c.close()
    import json
    for report in reports:
        try:
            report['review_history'] = json.loads(report.pop('review_history_json') or '[]')
        except Exception:
            report['review_history'] = []
    return jsonify(reports)


@app.route('/api/admin/reports/<cid>/evidence')
@login_required('MODERATOR')
def admin_report_evidence(cid):
    found = rows('SELECT evidence_path FROM complaints WHERE id=?', (cid,))
    if not found or not found[0]['evidence_path']:
        return json_error('Evidence photo not found', 404)
    path = BASE / 'backend' / found[0]['evidence_path']
    if not path.is_file():
        return json_error('Evidence file not found', 404)
    return send_file(path)


@app.route('/api/admin/reports/<cid>/bill')
@login_required('MODERATOR')
def admin_report_bill(cid):
    found = rows('SELECT bill_evidence_path FROM complaints WHERE id=?', (cid,))
    if not found or not found[0]['bill_evidence_path']:
        return json_error('Bill/receipt image not found', 404)
    path = BASE / 'backend' / found[0]['bill_evidence_path']
    if not path.is_file():
        return json_error('Bill/receipt file not found', 404)
    return send_file(path)


# =========================================================
# INVENTORY — dedicated operational database
# =========================================================

def _sync_inventory_incidents():
    refresh_inventory(); ic=inv_conn(); counts={}
    for x in ic.execute('SELECT restaurant_id,status,incident_type FROM inventory WHERE disposed=0').fetchall():
        if x['status']=='EXPIRED' or (x['incident_type'] or 'NONE')!='NONE': counts[x['restaurant_id']]=counts.get(x['restaurant_id'],0)+1
    ic.close(); c=conn()
    for r in c.execute('SELECT id FROM restaurants').fetchall(): c.execute('UPDATE restaurants SET inventory_incidents=? WHERE id=?',(counts.get(r['id'],0),r['id']))
    c.commit();c.close()

@app.route('/api/inventory')
@login_required('ADMIN')
def get_inventory():
    rid=request.args.get('restaurant_id',type=int);refresh_inventory();_sync_inventory_incidents();ic=inv_conn();q='SELECT * FROM inventory WHERE disposed=0';args=[]
    if rid:q+=' AND restaurant_id=?';args.append(rid)
    data=[serialize_inv(x) for x in ic.execute(q,args).fetchall()];ic.close();heap=expiry_heap(data);top=heap.peek_min()
    for x in data:x['is_earliest']=bool(top and int(top[1])==int(x['id']))
    return jsonify(data)

@app.route('/api/inventory/summary')
@login_required('ADMIN')
def inventory_summary():
    refresh_inventory();_sync_inventory_incidents();rid=request.args.get('restaurant_id',type=int);ic=inv_conn();q='SELECT * FROM inventory WHERE disposed=0';args=[]
    if rid:q+=' AND restaurant_id=?';args.append(rid)
    data=[serialize_inv(x) for x in ic.execute(q,args).fetchall()];ic.close()
    return jsonify({'total_items':len(data),'safe':sum(x['status']=='SAFE' for x in data),'low_stock':sum(x['status']=='LOW STOCK' for x in data),'expiring':sum(x['status']=='EXPIRING SOON' for x in data),'expired':sum(x['status']=='EXPIRED' for x in data),'incidents':sum((x.get('incident_type') or 'NONE')!='NONE' for x in data)})

@app.route('/api/inventory/heap')
@login_required('ADMIN')
def inventory_heap():
    data=get_inventory().get_json();heap=expiry_heap(data);top=heap.peek_min();return jsonify({'structure':'Min Heap','size':len(heap.heap),'earliest':top[2] if top else None,'operations':['insert','peek_min','extract_min','heapify']})

@app.route('/api/inventory',methods=['POST'])
@login_required('ADMIN')
def add_inventory():
    d=request.get_json(silent=True) or {}
    try:rid=int(d.get('restaurant_id',1));qty=float(d.get('quantity',0));reorder=float(d.get('reorder_level',5))
    except (ValueError,TypeError):return json_error('Invalid restaurant, quantity or reorder level')
    if not restaurant(rid):return json_error('Restaurant not found',404)
    product=str(d.get('product','')).strip();batch=str(d.get('batch_number','')).strip();expiry=str(d.get('expiry_date','')).strip();purchase=str(d.get('purchase_date','')).strip()
    if not product or not batch or not expiry or not purchase:return json_error('Product, batch number, purchase date and expiry date are required')
    try:purchase_d=date.fromisoformat(purchase);expiry_d=date.fromisoformat(expiry)
    except ValueError:return json_error('Invalid date')
    if expiry_d<purchase_d:return json_error('Expiry date cannot be before purchase date')
    if qty<1:return json_error('Quantity must be at least 1')
    ic=inv_conn();cur=ic.execute("INSERT INTO inventory(restaurant_id,product,category,batch_number,quantity,unit,purchase_date,expiry_date,supplier,storage_condition,reorder_level,incident_type,notes,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(rid,product,str(d.get('category','Other')),batch,qty,str(d.get('unit','unit')),purchase,expiry,str(d.get('supplier','')).strip(),str(d.get('storage_condition','Ambient')),reorder,str(d.get('incident_type','NONE')),str(d.get('notes','')).strip(),'SAFE'));ic.commit();x=ic.execute('SELECT * FROM inventory WHERE id=?',(cur.lastrowid,)).fetchone();ic.close();refresh_inventory();_sync_inventory_incidents();return jsonify(serialize_inv(x)),201

@app.route('/api/inventory/<int:iid>',methods=['PATCH'])
@login_required('ADMIN')
def patch_inventory(iid):
    d=request.get_json(silent=True) or {};allowed={'product','category','batch_number','quantity','unit','purchase_date','expiry_date','supplier','storage_condition','reorder_level','incident_type','notes','disposed'};vals={k:d[k] for k in d if k in allowed}
    if not vals:return json_error('No supported fields supplied')
    ic=inv_conn();x=ic.execute('SELECT * FROM inventory WHERE id=?',(iid,)).fetchone()
    if not x:ic.close();return json_error('Inventory item not found',404)
    merged=dict(x);merged.update(vals)
    try:
        if float(merged['quantity'])<1 or float(merged.get('reorder_level',0))<0:raise ValueError
        date.fromisoformat(str(merged['purchase_date']));date.fromisoformat(str(merged['expiry_date']))
    except (ValueError,TypeError):ic.close();return json_error('Invalid inventory quantity or date')
    sets=', '.join(f'{k}=?' for k in vals);args=list(vals.values());sets+=', status=?';st='DISPOSED' if merged.get('disposed') else inventory_status(str(merged['expiry_date']))[0]
    if not merged.get('disposed') and st=='SAFE' and float(merged['quantity'])<=float(merged.get('reorder_level',0)):st='LOW STOCK'
    args.extend([st,iid]);ic.execute(f'UPDATE inventory SET {sets} WHERE id=?',args);ic.commit();x=ic.execute('SELECT * FROM inventory WHERE id=?',(iid,)).fetchone();ic.close();refresh_inventory();_sync_inventory_incidents();return jsonify(serialize_inv(x))

@app.route('/api/inventory/<int:iid>',methods=['DELETE'])
@login_required('ADMIN')
def delete_inventory(iid):
    ic=inv_conn();cur=ic.execute('UPDATE inventory SET disposed=1,status="DISPOSED" WHERE id=?',(iid,));ic.commit();ic.close();_sync_inventory_incidents()
    if cur.rowcount:return jsonify({'message':'Inventory item disposed'})
    return json_error('Inventory item not found',404)

# =========================================================
# VERIFIED VISITS
# =========================================================

@app.route('/api/visits')
def visits():

    return jsonify(
        rows(
            '''
            SELECT v.*,
                   r.name restaurant,
                   r.area
            FROM verified_visits v
            JOIN restaurants r
              ON r.id=v.restaurant_id
            ORDER BY timestamp DESC
            '''
        )
    )


@app.route('/api/visits', methods=['POST'])
def create_visit():
    """Create a provenance-aware Verified Visit.

    IEEE-aligned verification methods:
    QR + browser GPS + timestamp + bill + OTP.
    Location verification compares the submitted browser coordinates with
    the restaurant's stored coordinates using the Haversine distance.
    """
    import math

    d = (
        request.form.to_dict()
        if request.form
        else (request.get_json(silent=True) or {})
    )

    try:
        rid = int(d.get('restaurant_id') or 0)
    except (ValueError, TypeError):
        rid = 0

    r = restaurant(rid)
    if not r:
        return json_error('Valid restaurant is required')

    def truthy(value):
        return str(value or '').strip().lower() in (
            '1', 'true', 'yes', 'on'
        )

    methods = []
    for method in ('qr', 'location_verified', 'timestamp_verified', 'bill', 'otp'):
        if truthy(d.get(method)):
            methods.append(method)

    if not methods:
        return json_error('Provide at least one verification method')

    # Validate visit timestamp.
    visit_ts = str(
        d.get('visit_timestamp')
        or datetime.now().isoformat(timespec='minutes')
    ).strip()

    try:
        parsed_visit_ts = datetime.fromisoformat(visit_ts)
    except ValueError:
        return json_error('Invalid visit timestamp')

    # Timestamp verification: the submitted timestamp must not be wildly
    # outside the current time window. This prevents arbitrary old/future
    # timestamps from being used as strong evidence.
    if 'timestamp_verified' in methods:
        now = datetime.now(parsed_visit_ts.tzinfo) if parsed_visit_ts.tzinfo else datetime.now()
        if abs((now - parsed_visit_ts).total_seconds()) > 24 * 60 * 60:
            return json_error(
                'Timestamp verification failed. Visit timestamp must be within 24 hours.'
            )

    # Verify the real SMS OTP, tied to the same phone number and valid once.
    if 'otp' in methods:
        try:
            otp_phone = normalize_sms_phone(d.get('otp_phone') or d.get('phone') or '')
        except ValueError as exc:
            return json_error(str(exc))
        record = VISIT_OTPS.get(otp_phone)
        submitted_code = str(d.get('otp_code', '')).strip()
        if not record or record.get('expires_at', 0) < time.time():
            VISIT_OTPS.pop(otp_phone, None)
            return json_error('OTP expired or not requested. Generate a new SMS or demo OTP.')
        if record.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
            VISIT_OTPS.pop(otp_phone, None)
            return json_error('Too many incorrect OTP attempts. Request a new OTP.')
        record['attempts'] = record.get('attempts', 0) + 1
        submitted_hash = hashlib.sha256(submitted_code.encode('utf-8')).hexdigest()
        if not hmac.compare_digest(submitted_hash, record['code_hash']):
            return json_error('Incorrect OTP. Check the SMS or demo code and try again.')
        # Consume the OTP only after successful verification.
        VISIT_OTPS.pop(otp_phone, None)

    # Bill evidence may be a reference or an uploaded image/document.
    bill_reference = str(d.get('bill_reference', '')).strip()
    bill_file = request.files.get('bill_evidence')
    if 'bill' in methods and not bill_reference and not (
        bill_file and bill_file.filename
    ):
        return json_error(
            'Bill verification requires a bill reference or bill upload'
        )

    # QR verification can use a generated QR/visit token when supplied.
    # The prototype accepts the QR method flag for backward compatibility.
    qr_token = str(d.get('qr_token', '')).strip()
    if 'qr' in methods and qr_token:
        expected_prefixes = ('VIS-', 'FOODSAFE-')
        if not qr_token.startswith(expected_prefixes):
            return json_error('QR verification failed')

    # Real browser GPS validation.
    # The database migration adds latitude/longitude to restaurants and
    # verified_visits. A location_verified visit must provide coordinates.
    distance_meters = None
    visitor_lat = None
    visitor_lon = None

    if 'location_verified' in methods:
        try:
            visitor_lat = float(d.get('latitude'))
            visitor_lon = float(d.get('longitude'))
        except (TypeError, ValueError):
            return json_error(
                'Location verification requires valid latitude and longitude'
            )

        if not (-90 <= visitor_lat <= 90 and -180 <= visitor_lon <= 180):
            return json_error('Invalid GPS coordinates')

        restaurant_lat = r.get('latitude')
        restaurant_lon = r.get('longitude')
        if restaurant_lat is None or restaurant_lon is None:
            return json_error(
                'Restaurant GPS coordinates are not configured'
            )

        try:
            restaurant_lat = float(restaurant_lat)
            restaurant_lon = float(restaurant_lon)
        except (TypeError, ValueError):
            return json_error(
                'Restaurant GPS coordinates are invalid'
            )

        earth_radius = 6371000.0
        lat1 = math.radians(visitor_lat)
        lat2 = math.radians(restaurant_lat)
        dlat = math.radians(restaurant_lat - visitor_lat)
        dlon = math.radians(restaurant_lon - visitor_lon)
        haversine_a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )
        distance_meters = 2 * earth_radius * math.asin(
            min(1.0, math.sqrt(haversine_a))
        )

        # 100 m is the prototype verification radius.
        if distance_meters > 100:
            return json_error(
                f'Location verification failed. You are {distance_meters:.1f} m '
                'from the restaurant; maximum allowed distance is 100 m.'
            )

    score = min(100, 30 + len(methods) * 14)
    status = 'VERIFIED' if score >= 58 else 'PENDING'

    vid = 'VIS-' + str(uuid.uuid4().int)[:7]
    bill_path = ''

    if bill_file and bill_file.filename:
        ext = (
            bill_file.filename.rsplit('.', 1)[-1].lower()
            if '.' in bill_file.filename
            else ''
        )
        if ext not in ALLOWED:
            return json_error('Bill evidence must be JPG, PNG or WEBP')
        bill_path = f'uploads/{vid}-bill.{ext}'
        bill_file.save(UP / f'{vid}-bill.{ext}')

    # Preserve the user-supplied location text while also storing precise
    # browser coordinates when GPS verification was used.
    location_text = str(d.get('location', '')).strip()
    if not location_text and visitor_lat is not None and visitor_lon is not None:
        location_text = f'{visitor_lat:.6f},{visitor_lon:.6f}'

    c = conn()
    c.execute(
        """
        INSERT INTO verified_visits
        (
            id,
            restaurant_id,
            methods,
            location,
            bill_reference,
            bill_evidence_path,
            verification_status,
            timestamp,
            verification_score,
            latitude,
            longitude,
            distance_meters
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            vid,
            rid,
            ','.join(methods),
            location_text,
            bill_reference,
            bill_path,
            status,
            visit_ts,
            score,
            visitor_lat,
            visitor_lon,
            distance_meters
        )
    )
    c.commit()
    c.close()

    return jsonify({
        'id': vid,
        'restaurant': r['name'],
        'verification_status': status,
        'methods': methods,
        'verification_score': score,
        'timestamp': visit_ts,
        'latitude': visitor_lat,
        'longitude': visitor_lon,
        'distance_meters': round(distance_meters, 2) if distance_meters is not None else None
    }), 201

@app.route('/api/visits/<vid>/bill-evidence')
def visit_bill_evidence(vid):

    found = rows(
        'SELECT bill_evidence_path '
        'FROM verified_visits WHERE id=?',
        (vid,)
    )

    if (
        not found
        or not found[0]['bill_evidence_path']
    ):

        return json_error(
            'Bill evidence not found',
            404
        )

    p = (
        BASE
        / 'backend'
        / found[0]['bill_evidence_path']
    )

    if not p.is_file():

        return json_error(
            'Bill evidence file not found',
            404
        )

    return send_file(p)


@app.route('/api/visits/demo-otp', methods=['POST'])
def generate_visit_demo_otp():
    """Generate a local demo OTP without sending SMS. Not real phone verification."""
    d = request.get_json(silent=True) or {}
    try:
        phone = normalize_sms_phone(d.get('phone', ''))
    except ValueError as exc:
        return json_error(str(exc), 400)

    now = time.time()
    if now - OTP_LAST_SENT.get('demo:' + phone, 0) < OTP_SEND_COOLDOWN_SECONDS:
        remaining = int(OTP_SEND_COOLDOWN_SECONDS - (now - OTP_LAST_SENT['demo:' + phone]))
        return json_error(f'Please wait {remaining} seconds before generating another demo OTP.', 429)

    code = f'{secrets.randbelow(1_000_000):06d}'
    VISIT_OTPS[phone] = {
        'code_hash': hashlib.sha256(code.encode('utf-8')).hexdigest(),
        'expires_at': now + OTP_TTL_SECONDS,
        'attempts': 0,
        'mode': 'demo',
    }
    OTP_LAST_SENT['demo:' + phone] = now
    return jsonify({
        'status': 'generated',
        'demo': True,
        'demo_code': code,
        'phone': phone,
        'expires_in_seconds': OTP_TTL_SECONDS,
        'message': 'Demo OTP generated. It expires in 5 minutes and can be used once.'
    })


@app.route('/api/visits/otp', methods=['POST'])
def send_visit_otp():
    """Send a real, short-lived OTP through the configured Twilio SMS account."""
    d = request.get_json(silent=True) or {}
    try:
        phone = normalize_sms_phone(d.get('phone', ''))
    except ValueError as exc:
        return json_error(str(exc), 400)

    now = time.time()
    if now - OTP_LAST_SENT.get(phone, 0) < OTP_SEND_COOLDOWN_SECONDS:
        remaining = int(OTP_SEND_COOLDOWN_SECONDS - (now - OTP_LAST_SENT[phone]))
        return json_error(f'Please wait {remaining} seconds before requesting another OTP.', 429)

    code = f'{secrets.randbelow(1_000_000):06d}'
    try:
        send_twilio_sms(phone, f'Your FoodSafe verification code is {code}. It expires in 5 minutes. Do not share this code.')
    except RuntimeError as exc:
        return json_error(str(exc), 503)

    VISIT_OTPS[phone] = {
        'code_hash': hashlib.sha256(code.encode('utf-8')).hexdigest(),
        'expires_at': now + OTP_TTL_SECONDS,
        'attempts': 0,
    }
    OTP_LAST_SENT[phone] = now
    return jsonify({
        'status': 'sent',
        'demo': False,
        'phone': phone,
        'expires_in_seconds': OTP_TTL_SECONDS,
        'message': f'OTP sent to {phone}. It expires in 5 minutes.'
    })


# =========================================================
# OCR — photo-based restaurant identification
# =========================================================
@app.route('/api/ocr', methods=['POST'])
def ocr():
    import os
    import shutil
    import tempfile
    import re
    import pytesseract
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    from difflib import SequenceMatcher

    # Support standard Windows installation, alternate install path, and PATH.
    candidates = [
        os.environ.get('TESSERACT_CMD', ''),
        shutil.which('tesseract') or '',
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    tesseract_path = next((x for x in candidates if x and os.path.isfile(x)), None)
    if not tesseract_path:
        return json_error('Tesseract OCR was not found. Install Tesseract OCR or add its folder to PATH, then restart FoodSafe.')
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    f = request.files.get('image')
    if not f or not f.filename:
        return json_error('Choose a restaurant photo first')

    temp_path = None
    try:
        suffix = Path(secure_filename(f.filename)).suffix or '.png'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            f.save(temp.name)
            temp_path = temp.name

        with Image.open(temp_path) as opened:
            image = ImageOps.exif_transpose(opened).convert('RGB')
            # Upscale small signs/menu text and improve contrast before OCR.
            if image.width < 1400:
                scale = min(2.5, 1400 / max(1, image.width))
                image = image.resize((int(image.width * scale), int(image.height * scale)))
            gray = ImageOps.grayscale(image)
            gray = ImageOps.autocontrast(gray)
            gray = ImageEnhance.Sharpness(gray).enhance(1.6)
            gray = ImageEnhance.Contrast(gray).enhance(1.35)
            variants = [image, gray, gray.filter(ImageFilter.MedianFilter(size=3))]

            texts = []
            # Try several OCR layouts and image treatments. Do not simply select
            # the longest OCR output: a longer but badly-recognized result can
            # hide a short, correct restaurant name.
            for variant in variants:
                for config in ('--oem 3 --psm 6', '--oem 3 --psm 11', '--oem 3 --psm 12', '--oem 3 --psm 4'):
                    try:
                        value = pytesseract.image_to_string(variant, config=config).strip()
                        if value and value not in texts:
                            texts.append(value)
                    except Exception:
                        continue

        def normalize(value):
            value = str(value or '').lower().replace('&', ' and ')
            value = value.replace('café', 'cafe').replace('good luck', 'goodluck')
            value = re.sub(r'[^a-z0-9]+', ' ', value)
            return ' '.join(value.split())

        restaurant_rows = rows('SELECT * FROM restaurants ORDER BY name')
        generic_tokens = {'restaurant','cafe','hotel','center','house','dining','hall','kitchen','the','and','of','at','camp'}

        def rank_text(candidate_text):
            normalized = normalize(candidate_text)
            tokens = set(normalized.split())
            useful_tokens = {t for t in tokens if len(t) >= 3 and t not in generic_tokens}
            ranked_items = []
            for rr in restaurant_rows:
                name = str(rr['name'] or '').strip()
                normalized_name = normalize(name)
                name_tokens = [t for t in normalized_name.split() if len(t) >= 3 and t not in generic_tokens]
                if normalized_name and normalized_name in normalized:
                    score = 1.0
                elif not name_tokens or not useful_tokens:
                    score = 0.0
                else:
                    # Distinctive brand terms should be sufficient when the OCR
                    # reads them exactly, even if it misses generic words like Cafe.
                    exact_distinctive = [t for t in name_tokens if t in useful_tokens]
                    token_scores = [max((SequenceMatcher(None, token, candidate).ratio() for candidate in useful_tokens), default=0) for token in name_tokens]
                    strong_matches = sum(x >= 0.76 for x in token_scores)
                    coverage = strong_matches / max(1, len(name_tokens))
                    best_token = max(token_scores, default=0)
                    whole_ratio = SequenceMatcher(None, normalized_name, normalized).ratio() if normalized else 0
                    score = max(coverage * 0.82, best_token * 0.42, whole_ratio * 0.65)
                    if exact_distinctive:
                        # Cafe Goodluck, for example, can still be recognized if
                        # OCR reads "Goodluck" but misses or garbles "Cafe".
                        score = max(score, 0.94 if len(exact_distinctive[0]) >= 6 else 0.78)
                    if len(name_tokens) >= 2 and strong_matches < 2 and not exact_distinctive:
                        score = min(score, 0.58)
                ranked_items.append((score, dict(rr)))
            ranked_items.sort(key=lambda item: item[0], reverse=True)
            return normalized, ranked_items

        # Choose the OCR variant which best matches an actual restaurant name.
        # This is more reliable than choosing the longest raw OCR text.
        candidate_texts = texts or ['']
        evaluated = [(rank_text(t)[1][0][0] if rank_text(t)[1] else 0, len(t), t) for t in candidate_texts]
        _, _, text = max(evaluated, key=lambda item: (item[0], item[1]))
        normalized_text, matches = rank_text(text)
        ranked = [dict(item[1], match_score=round(item[0]*100)) for item in matches[:5] if item[0] >= 0.42] if normalized_text else []
        # If a distinctive name token was read exactly, prioritize that restaurant.
        high_confidence = [m for m in ranked if m.get('match_score', 0) >= 88]
        result_matches = high_confidence[:3] if high_confidence else ranked[:5]
        return jsonify({
            'success': True,
            'text': text,
            'restaurants': result_matches,
            'matches': result_matches,
            'restaurant': result_matches[0] if result_matches else None
        })
    except Exception as e:
        return json_error(f'Photo identification failed: {str(e)}')
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# =========================================================
# ADMIN COMPLAINT MODERATION
# =========================================================

@app.route(
    '/api/admin/complaints/<cid>/review',
    methods=['POST']
)
@login_required('MODERATOR')
def review_complaint(cid):

    d = (
        request.get_json(silent=True)
        or request.form.to_dict()
    )

    decision = str(
        d.get(
            'decision',
            ''
        )
    ).upper().strip()

    remarks = str(
        d.get(
            'remarks',
            ''
        )
    ).strip()

    if decision not in (
        'VERIFY',
        'REJECT'
    ):

        return json_error(
            'Decision must be VERIFY or REJECT'
        )

    c = conn()

    complaint = c.execute(
        'SELECT * FROM complaints WHERE id=?',
        (cid,)
    ).fetchone()

    if not complaint:

        c.close()

        return json_error(
            'Complaint not found',
            404
        )

    u = current_user()

    status = (
        'VERIFIED'
        if decision == 'VERIFY'
        else 'REJECTED'
    )

    c.execute(
        '''
        UPDATE complaints
        SET verification_status=?
        WHERE id=?
        ''',
        (
            status,
            cid
        )
    )

    rid = complaint[
        'restaurant_id'
    ]

    if status == 'VERIFIED':

        c.execute(
            '''
            UPDATE restaurants
            SET pending_reports=
                    MAX(0,pending_reports-1),
                verified_reports=
                    verified_reports+1,
                last_updated=?
            WHERE id=?
            ''',
            (
                date.today().isoformat(),
                rid
            )
        )

    else:

        c.execute(
            '''
            UPDATE restaurants
            SET pending_reports=
                    MAX(0,pending_reports-1),
                last_updated=?
            WHERE id=?
            ''',
            (
                date.today().isoformat(),
                rid
            )
        )

    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS complaint_reviews
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            decision TEXT NOT NULL,
            remarks TEXT,
            timestamp TEXT NOT NULL
        )
        '''
    )

    c.execute(
        '''
        INSERT INTO complaint_reviews
        (
            complaint_id,
            reviewer,
            decision,
            remarks,
            timestamp
        )
        VALUES (?,?,?,?,?)
        ''',
        (
            cid,
            u['username'],
            status,
            remarks,
            datetime.now().isoformat(
                timespec='seconds'
            )
        )
    )

    c.commit()

    c.close()

    return jsonify({
        'success': True,
        'complaint_id': cid,
        'decision': status,
        'reviewer': u['username'],
        'remarks': remarks
    })


@app.route(
    '/api/admin/complaints/<cid>/reviews'
)
@login_required('MODERATOR')
def complaint_reviews(cid):

    return jsonify(
        rows(
            '''
            SELECT *
            FROM complaint_reviews
            WHERE complaint_id=?
            ORDER BY timestamp DESC
            ''',
            (cid,)
        )
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route('/api/admin/dashboard')
@login_required('MODERATOR')
def dashboard():

    c = conn()

    restaurants_all = [
        dict(r)
        for r in c.execute(
            'SELECT * FROM restaurants'
        ).fetchall()
    ]

    complaint_rows = [
        dict(x)
        for x in c.execute(
            '''
            SELECT c.*,
                   r.name restaurant,
                   r.area
            FROM complaints c
            JOIN restaurants r
              ON r.id=c.restaurant_id
            '''
        ).fetchall()
    ]

    c.close()

    refresh_inventory()
    ic=inv_conn()
    inventory_rows=[serialize_inv(x) for x in ic.execute('SELECT * FROM inventory WHERE disposed=0').fetchall()]
    ic.close()

    stats = {
        'total_establishments':
            len(restaurants_all),

        'verified_reports':
            sum(
                int(r['verified_reports'])
                for r in restaurants_all
            ),

        'pending_complaints':
            sum(
                1
                for x in complaint_rows
                if x['verification_status']
                == 'PENDING'
            ),

        'high_risk': sum(1 for r in restaurants_all if calculate(r)['level']=='HIGH'),

        'expiring_inventory':
            sum(
                1
                for x in inventory_rows
                if x['status']
                == 'EXPIRING SOON'
            ),

        'expired_inventory':
            sum(
                1
                for x in inventory_rows
                if x['status']
                == 'EXPIRED'
            ),

        'verified_visits':
            len(
                rows(
                    '''
                    SELECT id
                    FROM verified_visits
                    WHERE verification_status='VERIFIED'
                    '''
                )
            )
    }

    ordered = ordered_complaints(
        complaint_rows
    )

    return jsonify({
        'stats': stats,
        'priority_complaints':
            ordered[:10],

        'inventory_alerts': sorted([dict(x, restaurant=next((r['name'] for r in restaurants_all if int(r['id'])==int(x['restaurant_id'])), 'Unknown')) for x in inventory_rows if x['status'] in ('EXPIRED','EXPIRING SOON','LOW STOCK')],key=lambda x:(x['status']!='EXPIRED',x.get('days_remaining',9999)))[:30],
        'inventory_summary': {'total_items':len(inventory_rows),'safe':sum(x['status']=='SAFE' for x in inventory_rows),'low_stock':sum(x['status']=='LOW STOCK' for x in inventory_rows),'expiring':sum(x['status']=='EXPIRING SOON' for x in inventory_rows),'expired':sum(x['status']=='EXPIRED' for x in inventory_rows),'incidents':sum((x.get('incident_type') or 'NONE')!='NONE' for x in inventory_rows)},
        'risk_overview': [{'id':r['id'],'name':r['name'],'area':r['area'],'risk':calculate(r)} for r in restaurants_all]
    })


# =========================================================
# RESTAURANT MANAGEMENT API — scoped to selected restaurant
# =========================================================
def manager_restaurant_id():
    user = current_user()
    if not user or user.get('role') != 'BUSINESS':
        return None
    rid = session.get('restaurant_id')
    return int(rid) if rid and restaurant(int(rid)) else None

@app.route('/api/restaurant-management/me')
@login_required('BUSINESS')
def restaurant_management_me():
    rid = manager_restaurant_id()
    if not rid: return json_error('Restaurant session missing. Please log in again.', 401)
    r = restaurant(rid)
    return jsonify({'restaurant_id': rid, 'restaurant': r['name'], 'area': r['area']})

@app.route('/api/restaurant-management/inventory')
@login_required('BUSINESS')
def restaurant_management_inventory():
    rid = manager_restaurant_id()
    if not rid: return json_error('Restaurant session missing. Please log in again.', 401)
    refresh_inventory(); ic = inv_conn()
    data = [serialize_inv(x) for x in ic.execute('SELECT * FROM inventory WHERE restaurant_id=? AND disposed=0 ORDER BY expiry_date', (rid,)).fetchall()]
    ic.close()
    return jsonify({'items': data, 'summary': {'total_items':len(data), 'safe':sum(x['status']=='SAFE' for x in data), 'low_stock':sum(x['status']=='LOW STOCK' for x in data), 'expiring':sum(x['status']=='EXPIRING SOON' for x in data), 'expired':sum(x['status']=='EXPIRED' for x in data)}})

@app.route('/api/restaurant-management/inventory', methods=['POST'])
@login_required('BUSINESS')
def restaurant_management_add_inventory():
    rid = manager_restaurant_id()
    if not rid: return json_error('Restaurant session missing. Please log in again.', 401)
    d = request.get_json(silent=True) or {}
    try: qty=float(d.get('quantity',0)); reorder=float(d.get('reorder_level',5))
    except (ValueError,TypeError): return json_error('Invalid quantity or reorder level')
    product=str(d.get('product','')).strip(); batch=str(d.get('batch_number','')).strip(); purchase=str(d.get('purchase_date','')).strip(); expiry=str(d.get('expiry_date','')).strip()
    if not product or not batch or not purchase or not expiry: return json_error('Product, batch number, purchase date and expiry date are required')
    try: pd=date.fromisoformat(purchase); ed=date.fromisoformat(expiry)
    except ValueError: return json_error('Invalid purchase or expiry date')
    if ed < pd: return json_error('Expiry date cannot be before purchase date')
    if qty < 1 or reorder < 0: return json_error('Quantity must be at least 1 and reorder level cannot be negative')
    ic=inv_conn(); cur=ic.execute('INSERT INTO inventory(restaurant_id,product,category,batch_number,quantity,unit,purchase_date,expiry_date,supplier,storage_condition,reorder_level,incident_type,notes,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,product,str(d.get('category','Other')),batch,qty,str(d.get('unit','unit')),purchase,expiry,str(d.get('supplier','')).strip(),str(d.get('storage_condition','Ambient')),reorder,str(d.get('incident_type','NONE')),str(d.get('notes','')).strip(),'SAFE')); ic.commit(); ic.close(); refresh_inventory(); _sync_inventory_incidents()
    return jsonify({'message':'Stock item added to your restaurant inventory'}), 201

# =========================================================
# ADMIN DETAILS / ANALYTICS
# =========================================================

def _inventory_health_score(rows):
    if not rows:
        return 0
    scores={'SAFE':100,'LOW STOCK':65,'EXPIRING SOON':35,'EXPIRED':0}
    vals=[scores.get(str(x.get('status') or '').upper(),50) for x in rows]
    return round(sum(vals)/len(vals))


def _risk_engine_breakdown(rest, inventory_incidents=None):
    risk_data = calculate(rest, inventory_incidents=inventory_incidents)
    cumulative = [{'name':'Starting score','points':100,'score':100}]
    running = 100
    for factor in risk_data.get('factors', []):
        points = int(factor.get('points') or 0)
        running = max(0, min(100, running + points))
        cumulative.append({'name':factor.get('name','Factor'),'category':factor.get('category','general'),'value':factor.get('value','—'),'points':points,'score':running})
    if cumulative:
        cumulative[-1]['score'] = int(risk_data['score'])
    return cumulative, int(risk_data['score'])


@app.route('/api/admin/details')
@login_required('MODERATOR')
def admin_details():
    c=conn()
    restaurants_all=[dict(r) for r in c.execute('SELECT * FROM restaurants ORDER BY id').fetchall()]
    c.close()
    result=[]
    for r in restaurants_all:
        # Use the exact same risk calculation as the public Consumer profile.
        # This prevents the Details graph and consumer card from showing different scores.
        score_data = calculate(r)
        result.append({'id':int(r['id']),'name':r['name'],'area':r['area'],'risk_score':score_data['score'],'risk_level':score_data['level']})
    return jsonify({'restaurants':result,'demo':True,'formula_source':'calculate() — same deterministic calculation used by Consumer profiles'})


@app.route('/api/admin/details/risk/<int:rid>')
@login_required('MODERATOR')
def admin_details_risk(rid):
    c=conn(); row=c.execute('SELECT * FROM restaurants WHERE id=?',(rid,)).fetchone(); c.close()
    if not row:
        return json_error('Restaurant not found',404)
    rest=dict(row)
    # Reuse the Consumer risk calculation exactly; breakdown cumulative line ends at this score.
    risk_data = calculate(rest)
    factors, _ = _risk_engine_breakdown(rest)
    return jsonify({'id':rid,'name':rest['name'],'risk_score':risk_data['score'],'dashboard_score':risk_data['score'],'risk_level':risk_data['level'],'factors':factors,'formula':'100 base minus/plus weighted compliance, inspection, enforcement, corrective-action, hygiene, food-sampling, pest, water, cold-chain, training, traceability, report, inventory and recency factors','consistent_with_consumer':True,'data_status':risk_data.get('data_status'),'explanation':risk_data.get('explanation')})


@app.route('/api/admin/details/inventory/<int:rid>')
@login_required('MODERATOR')
def admin_details_inventory(rid):
    c=conn(); row=c.execute('SELECT id,name FROM restaurants WHERE id=?',(rid,)).fetchone(); c.close()
    if not row:
        return json_error('Restaurant not found',404)
    refresh_inventory()
    ic=inv_conn(); items=[dict(x) for x in ic.execute('SELECT * FROM inventory WHERE restaurant_id=? AND disposed=0 ORDER BY id',(rid,)).fetchall()]; ic.close()
    status_score={'SAFE':100,'LOW STOCK':65,'EXPIRING SOON':35,'EXPIRED':0}
    out=[]
    for x in items:
        out.append({'id':x['id'],'product':x['product'],'status':x.get('status'),'health_score':status_score.get(str(x.get('status') or '').upper(),50),'quantity':x.get('quantity'),'unit':x.get('unit')})
    return jsonify({'id':rid,'name':row['name'],'items':out,'inventory_health':_inventory_health_score(items)})


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def too_large(e):

    return json_error(
        'Evidence file is too large (maximum 5 MB)',
        413
    )


@app.errorhandler(500)
def server_error(e):

    app.logger.exception(e)

    return json_error(
        'FoodSafe service encountered an internal error.',
        500
    )

# =========================================================
# RUN
# =========================================================

if __name__ == '__main__':

    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )