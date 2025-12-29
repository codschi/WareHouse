import sqlite3
import os

# Define the database path (assuming default dev.db)
DB_PATH = "local_dev.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Starting Phase 3 Migration...")

    # 1. Update Staff Table
    try:
        print("Adding columns to Staff...")
        cursor.execute("ALTER TABLE Staff ADD COLUMN username TEXT")
        cursor.execute("ALTER TABLE Staff ADD COLUMN password TEXT")
        cursor.execute("ALTER TABLE Staff ADD COLUMN is_manager BOOLEAN DEFAULT 0")
        
        # Backfill Data
        print("Backfilling Staff credentials...")
        cursor.execute("UPDATE Staff SET username = stName, password = '0000'")
        
        # Create Unique Index (Since we can't add UNIQUE constraint easily via ALTER)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_username ON Staff (username)")
        print("Staff table updated.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Staff columns already exist. Skipping.")
        else:
            print(f"Error updating Staff: {e}")

    # 2. Update InboundOrder
    try:
        print("Adding Status to InboundOrder...")
        cursor.execute("ALTER TABLE InboundOrder ADD COLUMN Status TEXT DEFAULT 'Completed'")
        print("InboundOrder table updated.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("InboundOrder Status already exists. Skipping.")
        else:
            print(f"Error updating InboundOrder: {e}")

    # 3. Update Requisition
    try:
        print("Adding Status to Requisition...")
        cursor.execute("ALTER TABLE Requisition ADD COLUMN Status TEXT DEFAULT 'Completed'")
        print("Requisition table updated.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Requisition Status already exists. Skipping.")
        else:
            print(f"Error updating Requisition: {e}")

    conn.commit()
    conn.close()
    print("Migration Complete!")

if __name__ == "__main__":
    migrate()
