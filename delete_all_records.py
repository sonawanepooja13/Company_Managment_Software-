"""
Script to delete all records from the company management database.
This will delete ALL data from ALL tables - use with caution!
"""

import sqlite3
import os
import sys

def delete_all_records(db_path='local_database.db'):
    """
    Delete all records from all tables in the database.
    """
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database '{db_path}' does not exist. Creating it first...")
        
        # Create the database with the required schema
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create all tables (same schema as enhanced_data_manager.py)
            # Customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    gst_number TEXT,
                    contact_person TEXT,
                    designation TEXT,
                    website TEXT,
                    contact_number TEXT,
                    address TEXT,
                    state TEXT,
                    district TEXT,
                    location TEXT,
                    company_turnover TEXT,
                    owner_name TEXT,
                    number_of_staff TEXT,
                    products_selected TEXT,
                    company_valuation TEXT,
                    note TEXT,
                    call_conversion_time TEXT,
                    company_data_sent TEXT,
                    enquiry_received TEXT,
                    communication_details TEXT,
                    meeting_schedule_time TEXT,
                    meeting_agenda TEXT,
                    meeting_completed_details TEXT,
                    photo_files TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT,
                    server_timestamp TIMESTAMP
                )
            """)
            
            # Production batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_number TEXT NOT NULL,
                    product_name TEXT,
                    start_date TEXT,
                    expected_completion_date TEXT,
                    assigned_personnel TEXT,
                    quantity TEXT,
                    status TEXT,
                    material_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT,
                    server_timestamp TIMESTAMP
                )
            """)
            
            # Testing records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS testing_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER,
                    product_id TEXT NOT NULL,
                    user_name TEXT,
                    timestamp TEXT,
                    visual_inspection_data TEXT,
                    controller_programming TEXT,
                    wifi_programming TEXT,
                    tested_ok TEXT,
                    repair_status TEXT,
                    front_photo TEXT,
                    back_photo TEXT,
                    last_edited_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT,
                    server_timestamp TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES production_batches(id)
                )
            """)
            
            # Enquiry status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enquiry_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'Pending',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    server_timestamp TIMESTAMP
                )
            """)
            
            # Sync log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT,
                    table_name TEXT,
                    record_id TEXT,
                    direction TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    source_client TEXT,
                    error_message TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            print(f"Database created at: {db_path}")
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    
    print(f"Working with database: {db_path}")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database.")
            conn.close()
            return True
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        print()
        
        # Count records before deletion
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"Records in {table_name}: {count}")
        
        print(f"\nTotal records to delete: {total_records}")
        print("=" * 60)
        
        # Delete all records from each table
        deleted_counts = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_counts[table_name] = cursor.rowcount
            print(f"Deleted {cursor.rowcount} records from {table_name}")
        
        # Commit changes
        conn.commit()
        
        print("=" * 60)
        print("DELETION COMPLETE")
        print(f"Total records deleted: {sum(deleted_counts.values())}")
        
        # Verify deletion
        print("\nVerifying deletion...")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            status = "[OK] Empty" if count == 0 else f"[ERROR] Still has {count} records"
            print(f"  {table_name}: {status}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error deleting records: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("WARNING: This will delete ALL records from the database!")
    print("This operation cannot be undone.\n")
    
    # You can specify a different database path as command line argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'local_database.db'
    
    confirmation = input("Type 'DELETE' to confirm: ")
    if confirmation == 'DELETE':
        success = delete_all_records(db_path)
        if success:
            print("\n[OK] All records deleted successfully!")
        else:
            print("\n[ERROR] Error during deletion process")
    else:
        print("Operation cancelled.")