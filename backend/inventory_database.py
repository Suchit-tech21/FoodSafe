from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[1]
DB = BASE / 'database' / 'inventory.db'
DB.parent.mkdir(exist_ok=True)

def inv_conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_inventory_db():
    c = inv_conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        product TEXT NOT NULL,
        category TEXT DEFAULT 'Other',
        batch_number TEXT,
        quantity REAL DEFAULT 0,
        unit TEXT DEFAULT 'unit',
        purchase_date TEXT,
        expiry_date TEXT,
        supplier TEXT,
        storage_condition TEXT DEFAULT 'Ambient',
        reorder_level REAL DEFAULT 5,
        incident_type TEXT DEFAULT 'NONE',
        notes TEXT,
        status TEXT DEFAULT 'SAFE',
        disposed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_inventory_restaurant ON inventory(restaurant_id);
    CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON inventory(expiry_date);
    ''')
    c.commit(); c.close()

def migrate_legacy_inventory(main_conn):
    init_inventory_db()
    c = inv_conn()
    if c.execute('SELECT COUNT(*) FROM inventory').fetchone()[0] == 0:
        try:
            for r in main_conn.execute('SELECT * FROM inventory').fetchall():
                d = dict(r)
                c.execute('''INSERT INTO inventory(restaurant_id,product,batch_number,quantity,purchase_date,expiry_date,supplier,status,disposed) VALUES(?,?,?,?,?,?,?,?,?)''', (
                    d.get('restaurant_id'), d.get('product'), d.get('batch_number'), d.get('quantity'),
                    d.get('purchase_date'), d.get('expiry_date'), d.get('supplier'), d.get('status') or 'SAFE', d.get('disposed', 0)))
            c.commit()
        except Exception:
            pass
    c.close()
