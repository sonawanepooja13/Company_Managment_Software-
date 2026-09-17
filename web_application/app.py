"""
Complete Enterprise Web Application
Converted from full desktop application with all modules
"""

import os
import json
import sqlite3
import datetime
import csv
import shutil
import glob
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configuration
class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WEB_DATA_DIR = os.path.join(BASE_DIR, 'web_data')
    DATABASE_DIR = os.path.join(WEB_DATA_DIR, 'databases')
    CUSTOMER_PHOTOS_DIR = os.path.join(WEB_DATA_DIR, 'customer_photos')
    PRODUCTION_DOCS_DIR = os.path.join(WEB_DATA_DIR, 'production_docs')
    REPORTS_DIR = os.path.join(WEB_DATA_DIR, 'reports')
    EXPORTS_DIR = os.path.join(WEB_DATA_DIR, 'exports')
    PRODUCTION_DIR = os.path.join(WEB_DATA_DIR, 'Production')
    WAREHOUSE_DIR = os.path.join(WEB_DATA_DIR, 'warehouse')
    FINANCE_DIR = os.path.join(WEB_DATA_DIR, 'finance')
    HR_DIR = os.path.join(WEB_DATA_DIR, 'hr')
    PROJECTS_DIR = os.path.join(WEB_DATA_DIR, 'projects')
    RND_DIR = os.path.join(WEB_DATA_DIR, 'rnd')
    LEGAL_DIR = os.path.join(WEB_DATA_DIR, 'legal')
    QC_DIR = os.path.join(WEB_DATA_DIR, 'qc')
    IT_DIR = os.path.join(WEB_DATA_DIR, 'it')
    SUPPLY_CHAIN_DIR = os.path.join(WEB_DATA_DIR, 'supply_chain')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'csv', 'txt', 'doc', 'docx'}

app = Flask(__name__)
app.config.from_object(Config)

# Create data directories
def create_data_directories():
    """Create all necessary data directories."""
    directories = [
        app.config['WEB_DATA_DIR'],
        app.config['DATABASE_DIR'],
        app.config['CUSTOMER_PHOTOS_DIR'],
        app.config['PRODUCTION_DOCS_DIR'],
        app.config['REPORTS_DIR'],
        app.config['EXPORTS_DIR'],
        app.config['PRODUCTION_DIR'],
        app.config['WAREHOUSE_DIR'],
        app.config['FINANCE_DIR'],
        app.config['HR_DIR'],
        app.config['PROJECTS_DIR'],
        app.config['RND_DIR'],
        app.config['LEGAL_DIR'],
        app.config['QC_DIR'],
        app.config['IT_DIR'],
        app.config['SUPPLY_CHAIN_DIR']
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Web data directories created successfully")

# Database initialization
def init_databases():
    """Initialize all databases for complete enterprise system."""
    db_path = os.path.join(app.config['DATABASE_DIR'], 'enterprise_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table
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
    
    # Customers table (CRM)
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
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    
    # Enquiry status table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiry_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'Pending',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES users(id)
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
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
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
            created_by INTEGER,
            FOREIGN KEY (batch_id) REFERENCES production_batches(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    
    # Materials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_name TEXT NOT NULL,
            material_code TEXT,
            category TEXT,
            supplier TEXT,
            unit_price REAL,
            unit TEXT,
            stock_quantity INTEGER,
            minimum_stock INTEGER,
            location TEXT,
            specifications TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Price list table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_code TEXT,
            category TEXT,
            price REAL,
            currency TEXT DEFAULT 'INR',
            effective_date TEXT,
            expiry_date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Warehouse items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_code TEXT,
            category TEXT,
            quantity INTEGER,
            location TEXT,
            supplier TEXT,
            unit_price REAL,
            last_restocked TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Employees table (HR)
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
    
    # Projects table
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
    
    # Accounts table
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
    
    # Transactions table
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
    
    # R&D projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rnd_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            project_code TEXT,
            research_area TEXT,
            lead_researcher TEXT,
            start_date TEXT,
            expected_completion TEXT,
            budget REAL,
            status TEXT DEFAULT 'Research',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Legal documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legal_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT NOT NULL,
            document_type TEXT,
            document_number TEXT,
            issue_date TEXT,
            expiry_date TEXT,
            status TEXT DEFAULT 'Active',
            description TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # QC/QA records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qc_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE NOT NULL,
            product_id TEXT,
            batch_id INTEGER,
            inspection_date TEXT,
            inspector TEXT,
            quality_parameters TEXT,
            result TEXT,
            defects TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES production_batches(id)
        )
    """)
    
    # IT assets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_name TEXT NOT NULL,
            asset_tag TEXT UNIQUE,
            asset_type TEXT,
            serial_number TEXT,
            assigned_to TEXT,
            department TEXT,
            purchase_date TEXT,
            warranty_expiry TEXT,
            status TEXT DEFAULT 'Active',
            specifications TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Supply chain table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supply_chain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            supplier_code TEXT,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            rating REAL,
            category TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Vendors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            vendor_code TEXT,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            payment_terms TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Maintenance requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            equipment_name TEXT,
            issue_description TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            reported_by TEXT,
            assigned_to TEXT,
            reported_date TEXT,
            completed_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Help desk tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS help_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            reported_by TEXT,
            assigned_to TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # BOM table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bill_of_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bom_id TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            version TEXT,
            components TEXT,
            total_cost REAL,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sync log table (for MQTT integration)
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
    print("Enterprise databases initialized successfully")

# Helper functions
def get_db_connection():
    """Get database connection."""
    db_path = os.path.join(app.config['DATABASE_DIR'], 'enterprise_database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page - Dashboard."""
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    """Login page."""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """User login."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['department'] = user['department']
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

# Module-specific routes will be added here
# (CRM, Production, Warehouse, HR, Finance, Projects, R&D, Legal, QC, IT, Supply Chain, etc.)

# Customer Management Routes
@app.route('/customers')
def customers_page():
    """Customer management page."""
    return render_template('customers.html')

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers."""
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    """Add new customer."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
            data.get('company_name'), data.get('gst_number'), data.get('contact_person'),
            data.get('designation'), data.get('website'), data.get('contact_number'),
            data.get('address'), data.get('state'), data.get('district'), data.get('location'),
            data.get('company_turnover'), data.get('owner_name'), data.get('number_of_staff'),
            data.get('products_selected'), data.get('company_valuation'), data.get('note'),
            data.get('call_conversion_time'), data.get('company_data_sent'),
            data.get('enquiry_received'), data.get('communication_details'),
            data.get('meeting_schedule_time'), data.get('meeting_agenda'),
            data.get('meeting_completed_details'), data.get('photo_files')
        ))
        
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "customer_id": customer_id, "message": "Customer added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Production Management Routes
@app.route('/production')
def production_page():
    """Production management page."""
    return render_template('production.html')

@app.route('/api/production/batches', methods=['GET'])
def get_production_batches():
    """Get all production batches."""
    conn = get_db_connection()
    batches = conn.execute('SELECT * FROM production_batches ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in batches])

@app.route('/api/production/batches', methods=['POST'])
def add_production_batch():
    """Add new production batch."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO production_batches (
                batch_number, product_name, start_date, expected_completion_date,
                assigned_personnel, quantity, status, material_list, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            data.get('batch_number'), data.get('product_name'), data.get('start_date'),
            data.get('expected_completion_date'), data.get('assigned_personnel'),
            data.get('quantity'), data.get('status'), data.get('material_list')
        ))
        
        conn.commit()
        batch_id = cursor.lastrowid
        
        # Create production folder
        batch_folder = os.path.join(app.config['PRODUCTION_DIR'], data.get('batch_number'))
        os.makedirs(batch_folder, exist_ok=True)
        
        conn.close()
        
        return jsonify({"success": True, "batch_id": batch_id, "message": "Production batch added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Data Management Routes
@app.route('/api/data/stats', methods=['GET'])
def get_data_stats():
    """Get data statistics."""
    conn = get_db_connection()
    
    customer_count = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    batch_count = conn.execute('SELECT COUNT(*) FROM production_batches').fetchone()[0]
    employee_count = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    project_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    warehouse_count = conn.execute('SELECT COUNT(*) FROM warehouse_items').fetchone()[0]
    account_count = conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "customers": customer_count,
        "production_batches": batch_count,
        "employees": employee_count,
        "projects": project_count,
        "warehouse_items": warehouse_count,
        "accounts": account_count,
        "timestamp": datetime.datetime.now().isoformat()
    })

# Warehouse Management Routes
@app.route('/warehouse')
def warehouse_page():
    """Warehouse management page."""
    return render_template('warehouse.html')

@app.route('/api/warehouse/items', methods=['GET'])
def get_warehouse_items():
    """Get all warehouse items."""
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM warehouse_items ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in items])

@app.route('/api/warehouse/items', methods=['POST'])
def add_warehouse_item():
    """Add warehouse item."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO warehouse_items (
                item_name, item_code, category, quantity, location, 
                supplier, unit_price, last_restocked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('item_name'), data.get('item_code'), data.get('category'),
            data.get('quantity'), data.get('location'), data.get('supplier'),
            data.get('unit_price'), data.get('last_restocked')
        ))
        
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "item_id": item_id, "message": "Warehouse item added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# HR Management Routes
@app.route('/hr')
def hr_page():
    """HR management page."""
    return render_template('hr.html')

@app.route('/api/hr/employees', methods=['GET'])
def get_employees():
    """Get all employees."""
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in employees])

@app.route('/api/hr/employees', methods=['POST'])
def add_employee():
    """Add employee."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO employees (
                employee_id, full_name, email, phone, department, designation,
                joining_date, salary, status, address, skills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('employee_id'), data.get('full_name'), data.get('email'),
            data.get('phone'), data.get('department'), data.get('designation'),
            data.get('joining_date'), data.get('salary'), data.get('status'),
            data.get('address'), data.get('skills')
        ))
        
        conn.commit()
        employee_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "employee_id": employee_id, "message": "Employee added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Project Management Routes
@app.route('/projects')
def projects_page():
    """Project management page."""
    return render_template('projects.html')

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in projects])

@app.route('/api/projects', methods=['POST'])
def add_project():
    """Add project."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO projects (
                project_name, project_code, client_name, start_date, end_date,
                budget, status, description, assigned_team
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('project_name'), data.get('project_code'), data.get('client_name'),
            data.get('start_date'), data.get('end_date'), data.get('budget'),
            data.get('status'), data.get('description'), data.get('assigned_team')
        ))
        
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "project_id": project_id, "message": "Project added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Finance Management Routes
@app.route('/finance')
def finance_page():
    """Finance management page."""
    return render_template('finance.html')

@app.route('/api/finance/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts."""
    conn = get_db_connection()
    accounts = conn.execute('SELECT * FROM accounts ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in accounts])

@app.route('/api/finance/accounts', methods=['POST'])
def add_account():
    """Add account."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (
                account_name, account_type, account_number, balance, 
                currency, bank_name
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('account_name'), data.get('account_type'), data.get('account_number'),
            data.get('balance'), data.get('currency'), data.get('bank_name')
        ))
        
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "account_id": account_id, "message": "Account added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/finance/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions."""
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions ORDER BY date DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in transactions])

@app.route('/api/finance/transactions', methods=['POST'])
def add_transaction():
    """Add transaction."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, date, type, category, amount, 
                description, account_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('transaction_id'), data.get('date'), data.get('type'),
            data.get('category'), data.get('amount'), data.get('description'),
            data.get('account_id')
        ))
        
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "transaction_id": transaction_id, "message": "Transaction added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Materials Management Routes
@app.route('/materials')
def materials_page():
    """Materials management page."""
    return render_template('materials.html')

@app.route('/api/materials', methods=['GET'])
def get_materials():
    """Get all materials."""
    conn = get_db_connection()
    materials = conn.execute('SELECT * FROM materials ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in materials])

@app.route('/api/materials', methods=['POST'])
def add_material():
    """Add material."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO materials (
                material_name, material_code, category, supplier, 
                unit_price, unit, stock_quantity, minimum_stock, 
                location, specifications
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('material_name'), data.get('material_code'), data.get('category'),
            data.get('supplier'), data.get('unit_price'), data.get('unit'),
            data.get('stock_quantity'), data.get('minimum_stock'), data.get('location'),
            data.get('specifications')
        ))
        
        conn.commit()
        material_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "material_id": material_id, "message": "Material added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Price List Routes
@app.route('/pricing')
def pricing_page():
    """Price list management page."""
    return render_template('pricing.html')

@app.route('/api/pricing', methods=['GET'])
def get_price_list():
    """Get price list."""
    conn = get_db_connection()
    prices = conn.execute('SELECT * FROM price_list ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in prices])

@app.route('/api/pricing', methods=['POST'])
def add_price():
    """Add price."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO price_list (
                product_name, product_code, category, price, 
                currency, effective_date, expiry_date, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('product_name'), data.get('product_code'), data.get('category'),
            data.get('price'), data.get('currency'), data.get('effective_date'),
            data.get('expiry_date'), data.get('description')
        ))
        
        conn.commit()
        price_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "price_id": price_id, "message": "Price added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Supply Chain & Logistics Routes
@app.route('/supply-chain')
def supply_chain_page():
    """Supply chain management page."""
    return render_template('supply_chain.html')

@app.route('/api/supply-chain', methods=['GET'])
def get_supply_chain():
    """Get all supply chain data."""
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM supply_chain ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in suppliers])

@app.route('/api/supply-chain', methods=['POST'])
def add_supply_chain():
    """Add supply chain entry."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO supply_chain (
                supplier_name, supplier_code, contact_person, phone, 
                email, address, rating, category, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('supplier_name'), data.get('supplier_code'), data.get('contact_person'),
            data.get('phone'), data.get('email'), data.get('address'),
            data.get('rating'), data.get('category'), data.get('status')
        ))
        
        conn.commit()
        supplier_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "supplier_id": supplier_id, "message": "Supplier added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# R&D Engineering Routes
@app.route('/rnd')
def rnd_page():
    """R&D engineering page."""
    return render_template('rnd.html')

@app.route('/api/rnd/projects', methods=['GET'])
def get_rnd_projects():
    """Get all R&D projects."""
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM rnd_projects ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in projects])

@app.route('/api/rnd/projects', methods=['POST'])
def add_rnd_project():
    """Add R&D project."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO rnd_projects (
                project_name, project_code, research_area, lead_researcher,
                start_date, expected_completion, budget, status, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('project_name'), data.get('project_code'), data.get('research_area'),
            data.get('lead_researcher'), data.get('start_date'), data.get('expected_completion'),
            data.get('budget'), data.get('status'), data.get('description')
        ))
        
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "project_id": project_id, "message": "R&D project added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# QC/QA Management Routes
@app.route('/qc')
def qc_page():
    """QC/QA management page."""
    return render_template('qc.html')

@app.route('/api/qc/records', methods=['GET'])
def get_qc_records():
    """Get all QC records."""
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM qc_records ORDER BY inspection_date DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in records])

@app.route('/api/qc/records', methods=['POST'])
def add_qc_record():
    """Add QC record."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO qc_records (
                record_id, product_id, batch_id, inspection_date, inspector,
                quality_parameters, result, defects, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('record_id'), data.get('product_id'), data.get('batch_id'),
            data.get('inspection_date'), data.get('inspector'), data.get('quality_parameters'),
            data.get('result'), data.get('defects'), data.get('status')
        ))
        
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "record_id": record_id, "message": "QC record added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# IT Workspace Routes
@app.route('/it')
def it_page():
    """IT workspace page."""
    return render_template('it.html')

@app.route('/api/it/assets', methods=['GET'])
def get_it_assets():
    """Get all IT assets."""
    conn = get_db_connection()
    assets = conn.execute('SELECT * FROM it_assets ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in assets])

@app.route('/api/it/assets', methods=['POST'])
def add_it_asset():
    """Add IT asset."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO it_assets (
                asset_name, asset_tag, asset_type, serial_number,
                assigned_to, department, purchase_date, warranty_expiry,
                status, specifications
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('asset_name'), data.get('asset_tag'), data.get('asset_type'),
            data.get('serial_number'), data.get('assigned_to'), data.get('department'),
            data.get('purchase_date'), data.get('warranty_expiry'), data.get('status'),
            data.get('specifications')
        ))
        
        conn.commit()
        asset_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "asset_id": asset_id, "message": "IT asset added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Legal Compliance Routes
@app.route('/legal')
def legal_page():
    """Legal compliance page."""
    return render_template('legal.html')

@app.route('/api/legal/documents', methods=['GET'])
def get_legal_documents():
    """Get all legal documents."""
    conn = get_db_connection()
    documents = conn.execute('SELECT * FROM legal_documents ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in documents])

@app.route('/api/legal/documents', methods=['POST'])
def add_legal_document():
    """Add legal document."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO legal_documents (
                document_name, document_type, document_number, issue_date,
                expiry_date, status, description, file_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('document_name'), data.get('document_type'), data.get('document_number'),
            data.get('issue_date'), data.get('expiry_date'), data.get('status'),
            data.get('description'), data.get('file_path')
        ))
        
        conn.commit()
        document_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "document_id": document_id, "message": "Legal document added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Maintenance Routes
@app.route('/maintenance')
def maintenance_page():
    """Maintenance page."""
    return render_template('maintenance.html')

@app.route('/api/maintenance/requests', methods=['GET'])
def get_maintenance_requests():
    """Get all maintenance requests."""
    conn = get_db_connection()
    requests = conn.execute('SELECT * FROM maintenance_requests ORDER BY reported_date DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in requests])

@app.route('/api/maintenance/requests', methods=['POST'])
def add_maintenance_request():
    """Add maintenance request."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO maintenance_requests (
                request_id, equipment_name, issue_description, priority,
                status, reported_by, assigned_to, reported_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('request_id'), data.get('equipment_name'), data.get('issue_description'),
            data.get('priority'), data.get('status'), data.get('reported_by'),
            data.get('assigned_to'), data.get('reported_date')
        ))
        
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "request_id": request_id, "message": "Maintenance request added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Help Desk Routes
@app.route('/help')
def help_page():
    """Help desk page."""
    return render_template('help.html')

@app.route('/api/help/tickets', methods=['GET'])
def get_help_tickets():
    """Get all help tickets."""
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM help_tickets ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in tickets])

@app.route('/api/help/tickets', methods=['POST'])
def add_help_ticket():
    """Add help ticket."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO help_tickets (
                ticket_id, subject, description, priority, status,
                reported_by, assigned_to, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('ticket_id'), data.get('subject'), data.get('description'),
            data.get('priority'), data.get('status'), data.get('reported_by'),
            data.get('assigned_to'), data.get('category')
        ))
        
        conn.commit()
        ticket_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "ticket_id": ticket_id, "message": "Help ticket added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# BOM Engine Routes
@app.route('/bom')
def bom_page():
    """BOM engine page."""
    return render_template('bom.html')

@app.route('/api/bom', methods=['GET'])
def get_bom():
    """Get all BOMs."""
    conn = get_db_connection()
    boms = conn.execute('SELECT * FROM bill_of_materials ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in boms])

@app.route('/api/bom', methods=['POST'])
def add_bom():
    """Add BOM."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO bill_of_materials (
                bom_id, product_name, version, components, total_cost, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('bom_id'), data.get('product_name'), data.get('version'),
            data.get('components'), data.get('total_cost'), data.get('created_by')
        ))
        
        conn.commit()
        bom_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "bom_id": bom_id, "message": "BOM added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Panel Manufacturing Routes
@app.route('/panel-manufacturing')
def panel_manufacturing_page():
    """Panel manufacturing page."""
    return render_template('panel_manufacturing.html')

# Outward Routes
@app.route('/outward')
def outward_page():
    """Outward page."""
    return render_template('outward.html')

# Vendor Registration Routes
@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors."""
    conn = get_db_connection()
    vendors = conn.execute('SELECT * FROM vendors ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in vendors])

@app.route('/api/vendors', methods=['POST'])
def add_vendor():
    """Add vendor."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO vendors (
                vendor_name, vendor_code, contact_person, phone,
                email, address, payment_terms, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('vendor_name'), data.get('vendor_code'), data.get('contact_person'),
            data.get('phone'), data.get('email'), data.get('address'),
            data.get('payment_terms'), data.get('status')
        ))
        
        conn.commit()
        vendor_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"success": True, "vendor_id": vendor_id, "message": "Vendor added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Admin Tools Routes
@app.route('/admin')
def admin_page():
    """Admin tools page."""
    return render_template('admin.html')

# Data Management Routes
@app.route('/data-management')
def data_management_page():
    """Data management page."""
    return render_template('data_management.html')

# Settings Routes
@app.route('/settings')
def settings_page():
    """Settings page."""
    return render_template('settings.html')

# Initialize app
def init_app():
    """Initialize the application."""
    create_data_directories()
    init_databases()
    
    # Create default admin user
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = generate_password_hash('a')
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('a', password_hash, 'Administrator', 'admin@example.com', 'admin', 'IT'))
        conn.commit()
        print("Default admin user created (username: a, password: a)")
    except sqlite3.IntegrityError:
        print("Admin user already exists")
    
    conn.close()

if __name__ == '__main__':
    init_app()
    print("Starting Enterprise Web Application...")
    print("Data folder: web_data/")
    print("Access at: http://127.0.0.1:5000")
    print("Default login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)