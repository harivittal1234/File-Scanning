import sqlite3

def init_db(db_path="new_database.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create documents table
    c.execute('''
    CREATE TABLE documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        scan_date DATETIME
    );
    ''')
    
    # Create credit_requests table
    c.execute('''
    CREATE TABLE credit_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        requested_credits INTEGER,
        admin_notes TEXT,
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    # Create users table
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        credits INTEGER DEFAULT 20,
        last_reset TIMESTAMP
    );
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
