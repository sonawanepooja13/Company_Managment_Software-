"""
Script to convert desktop application data to web application format
"""

import sqlite3
import csv
import os
import shutil
import json
from datetime import datetime

class DesktopToWebConverter:
    """Convert desktop application data to web application format."""
    
    def __init__(self, desktop_dir, web_data_dir):
        self.desktop_dir = desktop_dir
        self.web_data_dir = web_data_dir
        self.web_db_path = os.path.join(web_data_dir, 'databases', 'enterprise_database.db')
        
    def convert_customers(self):
        """Convert customer data from desktop CSV to web database."""
        print("Converting customer data...")
        
        desktop_csv = os.path.join(self.desktop_dir, 'customers_detailed.csv')
        
        if not os.path.exists(desktop_csv):
            print("No desktop customer CSV found")
            return
        
        # Create web database
        os.makedirs(os.path.dirname(self.web_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create customers table
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
                created_by INTEGER
            )
        """)
        
        # Read desktop CSV and convert
        with open(desktop_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            converted_count = 0
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO customers (
                            company_name, gst_number, contact_person, designation, website,
                            contact_number, address, state, district, location, company_turnover,
                            owner_name, number_of_staff, products_selected, company_valuation,
                            note, call_conversion_time, company_data_sent, enquiry_received,
                            communication_details, meeting_schedule_time, meeting_agenda,
                            meeting_completed_details, photo_files, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        row.get('company_name', ''), row.get('gst_number', ''),
                        row.get('contact_person', ''), row.get('designation', ''),
                        row.get('website', ''), row.get('contact_number', ''),
                        row.get('address', ''), row.get('state', ''),
                        row.get('district', ''), row.get('location', ''),
                        row.get('company_turnover', ''), row.get('owner_name', ''),
                        row.get('number_of_staff', ''), row.get('products_selected', ''),
                        row.get('company_valuation', ''), row.get('note', ''),
                        row.get('call_conversion_time', ''), row.get('company_data_sent', ''),
                        row.get('enquiry_received', ''), row.get('communication_details', ''),
                        row.get('meeting_schedule_time', ''), row.get('meeting_agenda', ''),
                        row.get('meeting_completed_details', ''), row.get('photo_files', '')
                    ))
                    converted_count += 1
                except Exception as e:
                    print(f"Error importing customer row: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} customers to web database")
    
    def convert_enquiry_status(self):
        """Convert enquiry status from desktop CSV to web database."""
        print("Converting enquiry status...")
        
        desktop_csv = os.path.join(self.desktop_dir, 'enquiry_status.csv')
        
        if not os.path.exists(desktop_csv):
            print("No desktop enquiry status CSV found")
            return
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create enquiry status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enquiry_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'Pending',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER
            )
        """)
        
        # Read desktop CSV and convert
        with open(desktop_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            converted_count = 0
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO enquiry_status (company_name, status, updated_by)
                        VALUES (?, ?, 1)
                        ON CONFLICT(company_name) DO UPDATE SET 
                            status=?, updated_at=CURRENT_TIMESTAMP, updated_by=1
                    """, (row.get('company_name', ''), row.get('status', 'Pending'), row.get('status', 'Pending')))
                    converted_count += 1
                except Exception as e:
                    print(f"Error importing enquiry status row: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} enquiry status records to web database")
    
    def convert_production_data(self):
        """Convert production data from desktop to web database."""
        print("Converting production data...")
        
        desktop_production_dir = os.path.join(self.desktop_dir, 'Production')
        
        if not os.path.exists(desktop_production_dir):
            print("No desktop Production directory found")
            return
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create production batches table
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
                created_by INTEGER
            )
        """)
        
        # Scan for production batch info files
        pattern = os.path.join(desktop_production_dir, '*', 'info.csv')
        info_files = []
        
        for root, dirs, files in os.walk(desktop_production_dir):
            for file in files:
                if file == 'info.csv':
                    info_files.append(os.path.join(root, file))
        
        # Convert each production batch
        converted_count = 0
        for info_file in info_files:
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    row = next(reader, None)
                    if row:
                        cursor.execute("""
                            INSERT INTO production_batches (
                                batch_number, product_name, start_date, expected_completion_date,
                                assigned_personnel, quantity, status, material_list, created_by
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """, (
                            row.get('Batch_Number', ''), row.get('Product_Name', ''),
                            row.get('Start_Date', ''), row.get('Expected_Completion_Date', ''),
                            row.get('Assigned_Personnel', ''), row.get('Quantity', ''),
                            row.get('Status', ''), row.get('Material_List', '')
                        ))
                        converted_count += 1
                        print(f"  ✓ Converted batch: {row.get('Batch_Number', 'Unknown')}")
            except Exception as e:
                print(f"  ✗ Error converting batch: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} production batches to web database")
    
    def convert_testing_records(self):
        """Convert testing records from desktop to web database."""
        print("Converting testing records...")
        
        # Scan for testing log files
        desktop_production_dir = os.path.join(self.desktop_dir, 'Production')
        
        if not os.path.exists(desktop_production_dir):
            print("No desktop Production directory found")
            return
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create testing records table
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
                created_by INTEGER
            )
        """)
        
        # Scan for testing log files
        pattern = os.path.join(desktop_production_dir, '*', 'product_testing_log.csv')
        testing_files = []
        
        for root, dirs, files in os.walk(desktop_production_dir):
            for file in files:
                if file == 'product_testing_log.csv':
                    testing_files.append(os.path.join(root, file))
        
        converted_count = 0
        for testing_file in testing_files:
            try:
                with open(testing_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Build visual inspection data from checklist items
                        visual_items = []
                        checklist_fields = [
                            'No Scratches / Surface Defects',
                            'Dimensions & Fit Verified',
                            'Secure Components / Assembly',
                            'Component Alignment Checked',
                            'No Solder Bridges',
                            'Polarity Orientation Correct'
                        ]
                        for field in checklist_fields:
                            if field in row:
                                status = 'Passed' if row[field] == 'Passed' else 'Failed'
                                visual_items.append(f"{field}: {status}")
                        
                        cursor.execute("""
                            INSERT INTO testing_records (
                                product_id, user_name, timestamp, visual_inspection_data,
                                controller_programming, wifi_programming, tested_ok, repair_status,
                                front_photo, back_photo, last_edited_by
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('Product_ID', ''), row.get('User_Name', ''),
                            row.get('Timestamp', ''), ', '.join(visual_items),
                            row.get('Controller_Programming', ''), row.get('Wifi_Programming', ''),
                            row.get('Tested_OK', ''), row.get('Repair_Status', ''),
                            row.get('Front_Photo', ''), row.get('Back_Photo', ''),
                            row.get('Last_Edited_By', '')
                        ))
                        converted_count += 1
            except Exception as e:
                print(f"  ✗ Error converting testing file: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} testing records to web database")
    
    def convert_hr_data(self):
        """Convert HR data from desktop to web database."""
        print("Converting HR data...")
        
        # Check for HR CSV files
        hr_csv_files = [
            'employees.csv',
            'employee_data.csv',
            'hr_data.csv'
        ]
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                department TEXT,
                designation TEXT,
                joining_date TEXT,
                salary REAL,
                status TEXT DEFAULT 'Active',
                address TEXT,
                skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        converted_count = 0
        for csv_file in hr_csv_files:
            csv_path = os.path.join(self.desktop_dir, csv_file)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                cursor.execute("""
                                    INSERT INTO employees (
                                        employee_id, full_name, email, phone, department,
                                        designation, joining_date, salary, status, address, skills
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    row.get('employee_id', row.get('Employee_ID', '')),
                                    row.get('full_name', row.get('Full_Name', '')),
                                    row.get('email', row.get('Email', '')),
                                    row.get('phone', row.get('Phone', '')),
                                    row.get('department', row.get('Department', '')),
                                    row.get('designation', row.get('Designation', '')),
                                    row.get('joining_date', row.get('Joining_Date', '')),
                                    float(row.get('salary', row.get('Salary', 0))),
                                    row.get('status', row.get('Status', 'Active')),
                                    row.get('address', row.get('Address', '')),
                                    row.get('skills', row.get('Skills', ''))
                                ))
                                converted_count += 1
                            except Exception as e:
                                print(f"  ✗ Error importing employee row: {e}")
                except Exception as e:
                    print(f"  ✗ Error reading HR CSV: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} employee records to web database")
    
    def convert_finance_data(self):
        """Convert finance data from desktop to web database."""
        print("Converting finance data...")
        
        # Check for finance CSV files
        finance_csv_files = [
            'accounts.csv',
            'transactions.csv',
            'finance_data.csv'
        ]
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                account_type TEXT,
                account_number TEXT,
                balance REAL,
                currency TEXT DEFAULT 'INR',
                bank_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                date TEXT,
                type TEXT,
                category TEXT,
                amount REAL,
                description TEXT,
                account_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
        
        converted_count = 0
        for csv_file in finance_csv_files:
            csv_path = os.path.join(self.desktop_dir, csv_file)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                # Determine if this is an account or transaction
                                if 'account_name' in row or 'Account_Name' in row:
                                    cursor.execute("""
                                        INSERT INTO accounts (
                                            account_name, account_type, account_number, balance,
                                            currency, bank_name
                                        ) VALUES (?, ?, ?, ?, ?, ?)
                                    """, (
                                        row.get('account_name', row.get('Account_Name', '')),
                                        row.get('account_type', row.get('Account_Type', '')),
                                        row.get('account_number', row.get('Account_Number', '')),
                                        float(row.get('balance', row.get('Balance', 0))),
                                        row.get('currency', row.get('Currency', 'INR')),
                                        row.get('bank_name', row.get('Bank_Name', ''))
                                    ))
                                elif 'transaction_id' in row or 'Transaction_ID' in row:
                                    cursor.execute("""
                                        INSERT INTO transactions (
                                            transaction_id, date, type, category, amount,
                                            description, account_id
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        row.get('transaction_id', row.get('Transaction_ID', '')),
                                        row.get('date', row.get('Date', '')),
                                        row.get('type', row.get('Type', '')),
                                        row.get('category', row.get('Category', '')),
                                        float(row.get('amount', row.get('Amount', 0))),
                                        row.get('description', row.get('Description', '')),
                                        row.get('account_id', row.get('Account_ID', ''))
                                    ))
                                converted_count += 1
                            except Exception as e:
                                print(f"  ✗ Error importing finance row: {e}")
                except Exception as e:
                    print(f"  ✗ Error reading finance CSV: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} finance records to web database")
    
    def convert_project_data(self):
        """Convert project data from desktop to web database."""
        print("Converting project data...")
        
        # Check for project CSV files
        project_csv_files = [
            'projects.csv',
            'project_data.csv',
            'project_management.csv'
        ]
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                project_code TEXT,
                client_name TEXT,
                start_date TEXT,
                end_date TEXT,
                budget REAL,
                status TEXT DEFAULT 'Planning',
                description TEXT,
                assigned_team TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        converted_count = 0
        for csv_file in project_csv_files:
            csv_path = os.path.join(self.desktop_dir, csv_file)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                cursor.execute("""
                                    INSERT INTO projects (
                                        project_name, project_code, client_name, start_date,
                                        end_date, budget, status, description, assigned_team
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    row.get('project_name', row.get('Project_Name', '')),
                                    row.get('project_code', row.get('Project_Code', '')),
                                    row.get('client_name', row.get('Client_Name', '')),
                                    row.get('start_date', row.get('Start_Date', '')),
                                    row.get('end_date', row.get('End_Date', '')),
                                    float(row.get('budget', row.get('Budget', 0))),
                                    row.get('status', row.get('Status', 'Planning')),
                                    row.get('description', row.get('Description', '')),
                                    row.get('assigned_team', row.get('Assigned_Team', ''))
                                ))
                                converted_count += 1
                            except Exception as e:
                                print(f"  ✗ Error importing project row: {e}")
                except Exception as e:
                    print(f"  ✗ Error reading project CSV: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Converted {converted_count} project records to web database")
    
    def copy_customer_photos(self):
        """Copy customer photos from desktop to web application."""
        print("Copying customer photos...")
        
        desktop_photos_dir = os.path.join(self.desktop_dir, 'Customer_Photos')
        web_photos_dir = os.path.join(self.web_data_dir, 'customer_photos')
        
        if not os.path.exists(desktop_photos_dir):
            print("No desktop customer photos directory found")
            return
        
        # Copy all customer photos
        copied_count = 0
        for company_folder in os.listdir(desktop_photos_dir):
            desktop_company_path = os.path.join(desktop_photos_dir, company_folder)
            web_company_path = os.path.join(web_photos_dir, company_folder)
            
            if os.path.isdir(desktop_company_path):
                os.makedirs(web_company_path, exist_ok=True)
                
                for photo_file in os.listdir(desktop_company_path):
                    src = os.path.join(desktop_company_path, photo_file)
                    dst = os.path.join(web_company_path, photo_file)
                    
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        copied_count += 1
        
        print(f"✓ Copied {copied_count} customer photos to web application")
    
    def copy_production_documents(self):
        """Copy production documents from desktop to web application."""
        print("Copying production documents...")
        
        desktop_production_dir = os.path.join(self.desktop_dir, 'Production')
        web_docs_dir = os.path.join(self.web_data_dir, 'production_docs')
        
        if not os.path.exists(desktop_production_dir):
            print("No desktop Production directory found")
            return
        
        # Copy all production documents
        copied_count = 0
        for root, dirs, files in os.walk(desktop_production_dir):
            for file in files:
                src = os.path.join(root, file)
                
                # Create relative path structure
                rel_path = os.path.relpath(src, desktop_production_dir)
                dst = os.path.join(web_docs_dir, rel_path)
                
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    copied_count += 1
        
        print(f"✓ Copied {copied_count} production documents to web application")
    
    def create_users_table(self):
        """Create users table and default admin user."""
        print("Creating users table...")
        
        conn = sqlite3.connect(self.web_db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin user (password: admin123)
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('admin123')
        
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, role, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('admin', password_hash, 'Administrator', 'admin@example.com', 'admin', 'IT'))
            conn.commit()
            print("✓ Created default admin user (username: admin, password: admin123)")
        except sqlite3.IntegrityError:
            print("✓ Admin user already exists")
        
        conn.close()
    
    def convert_all(self):
        """Convert all desktop data to web application format."""
        print("=" * 60)
        print("Desktop to Web Application Conversion")
        print("=" * 60)
        print(f"Desktop Directory: {self.desktop_dir}")
        print(f"Web Data Directory: {self.web_data_dir}")
        print()
        
        # Convert all data
        self.create_users_table()
        self.convert_customers()
        self.convert_enquiry_status()
        self.convert_production_data()
        self.convert_testing_records()
        self.convert_hr_data()
        self.convert_finance_data()
        self.convert_project_data()
        self.copy_customer_photos()
        self.copy_production_documents()
        
        print()
        print("=" * 60)
        print("Conversion Complete!")
        print("=" * 60)
        print()
        print("Web application data is ready in:", self.web_data_dir)
        print("Default login: admin / admin123")
        print("Start the web application with: python app.py")


if __name__ == "__main__":
    # Get directories
    desktop_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_data')
    
    print(f"Desktop directory: {desktop_dir}")
    print(f"Web data directory: {web_data_dir}")
    
    # Run conversion
    converter = DesktopToWebConverter(desktop_dir, web_data_dir)
    converter.convert_all()