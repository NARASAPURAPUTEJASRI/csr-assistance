import sqlite3

DB_FILE = "csr_database.db"

def _connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id         INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            email      TEXT,
            phone      TEXT,
            city       TEXT,
            segment    TEXT    DEFAULT 'REGULAR',
            created_at TEXT    DEFAULT (date('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id   INTEGER NOT NULL,
            customer_name TEXT,
            product       TEXT,
            quantity      INTEGER DEFAULT 1,
            amount        REAL,
            status        TEXT    DEFAULT 'Processing',
            delivery_date TEXT,
            created_at    TEXT    DEFAULT (date('now')),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER,
            customer_id INTEGER,
            issue       TEXT,
            priority    TEXT    DEFAULT 'MEDIUM',
            status      TEXT    DEFAULT 'OPEN',
            created_at  TEXT    DEFAULT (date('now')),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER,
            customer_id INTEGER,
            reason      TEXT,
            priority    TEXT    DEFAULT 'LOW',
            status      TEXT    DEFAULT 'OPEN',
            created_at  TEXT    DEFAULT (date('now')),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    cur.executemany(
        "INSERT OR IGNORE INTO customers(id, name, email, phone, city, segment) VALUES (?,?,?,?,?,?)",
        [
            (1, "Tejasri", "tejasri@email.com", "9000000001", "Hyderabad", "PREMIUM"),
            (2, "Anand", "anand@email.com", "9000000002", "Bangalore", "REGULAR"),
            (3, "Priya", "priya@email.com", "9000000003", "Chennai", "REGULAR"),
            (4, "Ravi", "ravi@email.com", "9000000004", "Mumbai", "PREMIUM"),
            (5, "Sneha", "sneha@email.com", "9000000005", "Hyderabad", "PREMIUM"),
        ]
    )

    cur.executemany(
        "INSERT OR IGNORE INTO orders(id, customer_id, customer_name, product, quantity, amount, status, delivery_date) VALUES (?,?,?,?,?,?,?,?)",
        [
            (101, 1, "Tejasri", "MacBook Air M3", 1, 124900, "Shipped", "2026-04-20"),
            (102, 1, "Tejasri", "Wireless Earbuds", 2, 8990, "Delivered", "2026-04-05"),
            (103, 2, "Anand", "iPhone 16", 1, 79900, "Processing", "2026-04-25"),
            (104, 3, "Priya", "Samsung Galaxy Watch", 1, 28990, "Delayed", "2026-04-10"),
            (105, 4, "Ravi", "Sony WH-1000XM5", 1, 29990, "Shipped", "2026-04-18"),
        ]
    )

    conn.commit()
    conn.close()

def get_order_by_id(order_id: int):
    conn = _connect()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_orders_by_customer_id(customer_id: int):
    conn = _connect()
    rows = conn.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_orders_by_customer_name(name: str):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM orders WHERE LOWER(customer_name) LIKE ? OR LOWER(customer_name) LIKE ?",
        (f"%{name.lower()}%", f"%{name.lower().replace(' ', '')}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cancel_order(order_id: int):
    conn = _connect()
    conn.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ?", (order_id,))
    changed = conn.total_changes
    conn.commit()
    conn.close()
    return changed > 0

def get_customer_by_id(customer_id: int):
    conn = _connect()
    row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_by_name(name: str):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM customers WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
        (f"%{name.lower()}%", f"%{name.lower().replace(' ', '')}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_ticket(order_id: int, customer_id: int = None, issue: str = "General issue"):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO tickets (order_id, customer_id, issue) VALUES (?,?,?)",
        (order_id, customer_id, issue)
    )
    ticket_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def create_complaint(order_id: int, customer_id: int = None, reason: str = "Not specified", priority: str = "LOW"):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO complaints (order_id, customer_id, reason, priority) VALUES (?,?,?,?)",
        (order_id, customer_id, reason, priority)
    )
    comp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return comp_id

def create_order(customer_id: int, customer_name: str, product: str, quantity: int, amount: float, status: str, delivery_date: str):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO orders (customer_id, customer_name, product, quantity, amount, status, delivery_date) VALUES (?,?,?,?,?,?,?)",
        (customer_id, customer_name, product, quantity, amount, status, delivery_date)
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def check_duplicate_complaint(order_id: int):
    conn = _connect()
    row = conn.execute("SELECT id FROM complaints WHERE order_id = ? AND status = 'OPEN'", (order_id,)).fetchone()
    conn.close()
    return row is not None

def check_duplicate_ticket(order_id: int):
    conn = _connect()
    row = conn.execute("SELECT id FROM tickets WHERE order_id = ? AND status = 'OPEN'", (order_id,)).fetchone()
    conn.close()
    return row is not None

def get_high_priority_complaints():
    conn = _connect()
    rows = conn.execute("""
        SELECT c.id, c.order_id, COALESCE(cust.name, ord.customer_name) AS customer_name, c.reason, c.priority
        FROM complaints c
        LEFT JOIN customers cust ON c.customer_id = cust.id
        LEFT JOIN orders ord ON c.order_id = ord.id
        WHERE c.priority = 'HIGH' AND c.status = 'OPEN'
        ORDER BY c.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_order_id(order_id: int):
    conn = _connect()
    rows = conn.execute("""
        SELECT c.id, c.order_id, COALESCE(cust.name, ord.customer_name) AS customer_name, c.reason, c.priority, c.status, c.created_at
        FROM complaints c
        LEFT JOIN customers cust ON c.customer_id = cust.id
        LEFT JOIN orders ord ON c.order_id = ord.id
        WHERE c.order_id = ?
        ORDER BY c.id DESC
    """, (order_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_customer_id(customer_id: int):
    conn = _connect()
    rows = conn.execute("""
        SELECT c.id, c.order_id, COALESCE(cust.name, ord.customer_name) AS customer_name, c.reason, c.priority, c.status, c.created_at
        FROM complaints c
        LEFT JOIN customers cust ON c.customer_id = cust.id
        LEFT JOIN orders ord ON c.order_id = ord.id
        WHERE c.customer_id = ?
        ORDER BY c.id DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_customer_name(name: str):
    conn = _connect()
    rows = conn.execute("""
        SELECT c.id, c.order_id, COALESCE(cust.name, ord.customer_name) AS customer_name, c.reason, c.priority, c.status, c.created_at
        FROM complaints c
        LEFT JOIN customers cust ON c.customer_id = cust.id
        LEFT JOIN orders ord ON c.order_id = ord.id
        WHERE LOWER(COALESCE(cust.name, ord.customer_name)) LIKE ?
        ORDER BY c.id DESC
    """, (f"%{name.lower()}%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]