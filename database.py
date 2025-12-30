import sqlite3

conn = sqlite3.connect("dala_foods.db")
cursor = conn.cursor()

# Staff table
cursor.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Add default accounts
cursor.execute("""
INSERT OR IGNORE INTO staff (email, password, role)
VALUES 
('admin@dalafoods.com', 'admin123', 'Admin'),
('storekeeper@dalafoods.com', 'store123', 'Storekeeper'),
('staff@dalafoods.com', 'staff123', 'Staff')
""")

# Store table
cursor.execute("""
CREATE TABLE IF NOT EXISTS store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    date_added TEXT
)
""")

# Production table
cursor.execute("""
CREATE TABLE IF NOT EXISTS production (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    produced_by TEXT NOT NULL,
    date_produced TEXT
)
""")

conn.commit()
conn.close()
print("Database created successfully")
