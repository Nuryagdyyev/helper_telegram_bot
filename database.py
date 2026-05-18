import sqlite3

def init_db():
    with sqlite3.connect('orders.db') as conn:
        conn.execute("""
                CREATE TABLE IF NOT EXISTS clients(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT UNIQUE
                )
        """)
        conn.commit()
        print('Database tayyar boldy')



                # Zakazlar tablisasy (TÄZE)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                service_type TEXT,
                amount REAL NOT NULL,
                due_date TEXT,
                completion_deadline TEXT,
                status TEXT DEFAULT 'pending',
                paid REAL DEFAULT 0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        conn.commit()
        print('Database tayyar boldy (clients + orders)')


def add_client(name):
    """Taze musderi goshulyar(eger yok bolsa)"""
    with sqlite3.connect('orders.db') as conn:
        try:
            conn.execute("INSERT INTO clients(name) VALUES(?)", (name,))
            conn.commit()
            return True, 'goshuldy'
        except sqlite3.IntegrityError:
            """eger shol musderin ady bar bolsa, onda hata berer"""
            return False, 'Bu musderi bar'
        

def get_all_clients():
    with sqlite3.connect('orders.db') as conn:
        cursor = conn.execute("SELECT id, name FROM clients")
        return cursor.fetchall()


def check_db():
    import sqlite3
    try:
        with sqlite3.connect('orders.db') as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
            if cursor.fetchone():
                print("Database bar we dogry guruldy.")
                clients = get_all_clients()
                print(f"Müşderiler:{clients}")
            else:
                print("Database ýok ýa-da 'clients' tablisasy ýok.")
    except sqlite3.Error as e:
        print(f"Database bilen baglanyşykda hata: {e}")
           

def add_order(client_id, service_type, amount, due_date, completion_deadline, description):
    with sqlite3.connect('orders.db') as conn:
        cursor = conn.execute("""
            INSERT INTO orders(client_id, service_type, amount, due_date, completion_deadline, description)
            VALUES(?, ?, ?, ?, ?, ?)
        """, (client_id, service_type, amount, due_date, completion_deadline, description))
        conn.commit()
        return cursor.lastrowid
    

def get_pending_tasks():
    """Ýerine ýetirilmedik zakazlar"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE o.status = 'pending'
            ORDER BY o.completion_deadline ASC NULLS LAST
        """)
        return cursor.fetchall()
    

def complete_order(order_id):
    with sqlite3.connect('orders.db') as conn:
        cursor = conn.execute("UPDATE orders SET status = 'done' WHERE id = ?", (order_id,))
        conn.commit()
        return cursor.rowcount > 0
    

def get_debts():
    """Klientlerden algylar"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type,
                   o.amount, o.paid,
                   (o.amount - o.paid) as debt
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE o.status = 'done' AND o.paid < o.amount
            ORDER BY debt DESC
        """)
        return cursor.fetchall()
    
def get_order_by_id(order_id):
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.status, o.paid, o.description
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        return cursor.fetchone()
    

def add_payment(order_id, amount):
    with sqlite3.connect('orders.db') as conn:
        cursor = conn.execute("SELECT paid FROM orders WHERE id = ?", (order_id,))
        result = cursor.fetchone()
        if result:
            current_paid = result[0] or 0
            new_paid = current_paid + amount
            conn.execute("UPDATE orders SET paid = ? WHERE id = ?", (new_paid, order_id))
            conn.commit()
            return True
        return False
    

def get_today_tasks():
    """Bu gün ýerine ýetiriljek zakazlar"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE date(o.completion_deadline) = date('now') AND o.status = 'pending'
            ORDER BY o.completion_deadline ASC
        """)
        return cursor.fetchall()


def get_today_payments():
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE date(o.due_date) = date('now') AND o.paid < o.amount
            ORDER BY o.due_date ASC
        """)
        return cursor.fetchall()
    

def update_order(order_id, field, value):
    """Zakazyň belli bir ugry boýunça maglumatyny üýtgetmek üçin funksiýa"""
    with sqlite3.connect('orders.db') as conn:
        conn.execute(f"UPDATE orders SET {field} = ? WHERE id = ?", (value, order_id))
        conn.commit()


def search_orders(query):
    """Zakazlary gözlemek üçin funksiýa"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.status, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE c.name LIKE ? OR o.service_type LIKE ? OR o.description LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return cursor.fetchall()


def get_statistics():
    """Zakazlar we tölegler boýunça statistika"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(paid), 0) as total_paid,
                COALESCE(SUM(amount - paid), 0) as total_debt
            FROM orders
        """)
        return cursor.fetchone()
    
def get_month_report(month):
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(paid), 0) as total_paid,
                COALESCE(SUM(amount - paid), 0) as total_debt
            FROM orders
            WHERE strftime('%Y-%m', created_at) = ?
        """, (month,))
        return cursor.fetchone()
    

def get_overdue_tasks():
    """Möhleti geçen sargytlar"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE date(o.completion_deadline) < date('now') AND o.status = 'pending'
            ORDER BY o.completion_deadline ASC
        """)
        return cursor.fetchall()


def get_tomorrow_tasks():
    """Ertirki gün tamamlanmaly işler"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE date(o.completion_deadline) = date('now', '+1 day') AND o.status = 'pending'
            ORDER BY o.completion_deadline ASC
        """)
        return cursor.fetchall()
    

def get_tomorrow_payments():
    """Ertir töleg möhleti geçen zakazlar"""
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.paid
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            WHERE date(o.due_date) = date('now', '+1 day') AND o.paid < o.amount
            ORDER BY o.due_date ASC
        """)
        return cursor.fetchall()
    

def delete_order(order_id):
    with sqlite3.connect('orders.db') as conn:
        cursor = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        return cursor.rowcount > 0
    

def get_all_orders(month=None):
    with sqlite3.connect('orders.db') as conn:
        conn.row_factory = sqlite3.Row
        query = """
            SELECT o.id, c.name as client_name, o.service_type, o.amount, 
                   o.due_date, o.completion_deadline, o.status, o.paid,
                   o.description, o.created_at
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            
        """
        if month:
            query += " WHERE strftime('%Y-%m', created_at) = ?"
            query += " ORDER BY created_at DESC"
            cursor = conn.execute(query, (month,))
        else:
            query += " ORDER BY created_at DESC"
            cursor = conn.execute(query)
        return cursor.fetchall()