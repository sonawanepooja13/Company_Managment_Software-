"""
Web Application for CRM/Production Management System
Flask-based web interface with separate data storage
"""

import os
import json
import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import csv

# Configuration
class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    UPLOAD_FOLDER = 'web_data/uploads'
    CUSTOMER_PHOTOS = 'web_data/customer_photos'
    PRODUCTION_DOCS = 'web_data/production_docs'
    REPORTS_FOLDER = 'web_data/reports'
    EXPORTS_FOLDER = 'web_data/exports'
    DATABASE_FOLDER = 'web_data/databases'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'csv'}

app = Flask(__name__)
app.config.from_object(Config)

# Create data directories
def create_data_directories():
    """Create all necessary data directories."""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['CUSTOMER_PHOTOS'],
        app.config['PRODUCTION_DOCS'],
        app.config['REPORTS_FOLDER'],
        app.config['EXPORTS_FOLDER'],
        app.config['DATABASE_FOLDER']
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Data directories created successfully")

# Database initialization
def init_databases():
    """Initialize all databases in the separate data folder."""
    db_path = os.path.join(app.config['DATABASE_FOLDER'], 'main_database.db')
    
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
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
    
    conn.commit()
    conn.close()
    print("Databases initialized successfully")

# Helper functions
def get_db_connection():
    """Get database connection."""
    db_path = os.path.join(app.config['DATABASE_FOLDER'], 'main_database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    """Home page - Dashboard."""
    return render_template('dashboard.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

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

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update customer."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE customers SET
                company_name=?, gst_number=?, contact_person=?, designation=?,
                website=?, contact_number=?, address=?, state=?, district=?,
                location=?, company_turnover=?, owner_name=?, number_of_staff=?,
                products_selected=?, company_valuation=?, note=?, call_conversion_time=?,
                company_data_sent=?, enquiry_received=?, communication_details=?,
                meeting_schedule_time=?, meeting_agenda=?, meeting_completed_details=?,
                photo_files=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            data.get('company_name'), data.get('gst_number'), data.get('contact_person'),
            data.get('designation'), data.get('website'), data.get('contact_number'),
            data.get('address'), data.get('state'), data.get('district'), data.get('location'),
            data.get('company_turnover'), data.get('owner_name'), data.get('number_of_staff'),
            data.get('products_selected'), data.get('company_valuation'), data.get('note'),
            data.get('call_conversion_time'), data.get('company_data_sent'),
            data.get('enquiry_received'), data.get('communication_details'),
            data.get('meeting_schedule_time'), data.get('meeting_agenda'),
            data.get('meeting_completed_details'), data.get('photo_files'), customer_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Customer updated successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM customers WHERE id=?', (customer_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Customer deleted successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# File Upload Routes
@app.route('/api/upload/customer_photo', methods=['POST'])
def upload_customer_photo():
    """Upload customer photo."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    
    file = request.files['file']
    company_name = request.form.get('company_name', 'unknown')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create company-specific folder
        company_folder = os.path.join(app.config['CUSTOMER_PHOTOS'], secure_filename(company_name))
        os.makedirs(company_folder, exist_ok=True)
        
        file_path = os.path.join(company_folder, filename)
        file.save(file_path)
        
        return jsonify({
            "success": True, 
            "file_path": file_path,
            "message": "Photo uploaded successfully"
        })
    
    return jsonify({"success": False, "error": "File type not allowed"}), 400

@app.route('/web_data/customer_photos/<company_name>/<filename>')
def serve_customer_photo(company_name, filename):
    """Serve customer photo."""
    company_folder = secure_filename(company_name)
    return send_from_directory(
        os.path.join(app.config['CUSTOMER_PHOTOS'], company_folder), 
        filename
    )

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
        conn.close()
        
        return jsonify({"success": True, "batch_id": batch_id, "message": "Production batch added successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Enquiry Management Routes
@app.route('/api/enquiry_status', methods=['GET'])
def get_enquiry_status():
    """Get all enquiry statuses."""
    conn = get_db_connection()
    statuses = conn.execute('SELECT * FROM enquiry_status').fetchall()
    conn.close()
    return jsonify([dict(row) for row in statuses])

@app.route('/api/enquiry_status', methods=['POST'])
def update_enquiry_status():
    """Update enquiry status."""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO enquiry_status (company_name, status, updated_by)
            VALUES (?, ?, 1)
            ON CONFLICT(company_name) DO UPDATE SET 
                status=?, updated_at=CURRENT_TIMESTAMP, updated_by=1
        """, (data.get('company_name'), data.get('status'), data.get('status')))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Enquiry status updated successfully"})
    
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

# Export Routes
@app.route('/api/export/customers', methods=['GET'])
def export_customers():
    """Export customers to CSV."""
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers').fetchall()
    conn.close()
    
    # Create CSV file
    export_path = os.path.join(app.config['EXPORTS_FOLDER'], f'customers_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    
    with open(export_path, 'w', newline='', encoding='utf-8') as f:
        if customers:
            writer = csv.DictWriter(f, fieldnames=customers[0].keys())
            writer.writeheader()
            writer.writerows([dict(row) for row in customers])
    
    return send_file(export_path, as_attachment=True, download_name='customers_export.csv')

# Data Management Routes
@app.route('/api/data/backup', methods=['POST'])
def backup_data():
    """Create database backup."""
    import shutil
    from datetime import datetime
    
    db_path = os.path.join(app.config['DATABASE_FOLDER'], 'main_database.db')
    backup_path = os.path.join(app.config['DATABASE_FOLDER'], f'backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    try:
        shutil.copy2(db_path, backup_path)
        return jsonify({"success": True, "message": "Backup created successfully", "backup_path": backup_path})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/data/stats', methods=['GET'])
def get_data_stats():
    """Get data statistics."""
    conn = get_db_connection()
    
    customer_count = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    batch_count = conn.execute('SELECT COUNT(*) FROM production_batches').fetchone()[0]
    testing_count = conn.execute('SELECT COUNT(*) FROM testing_records').fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "customers": customer_count,
        "production_batches": batch_count,
        "testing_records": testing_count,
        "timestamp": datetime.datetime.now().isoformat()
    })

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
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
        """, ('a', password_hash, 'Administrator', 'admin@example.com', 'admin'))
        conn.commit()
        print("Default admin user created (username: a, password: a)")
    except sqlite3.IntegrityError:
        print("Admin user already exists")
    
    conn.close()

if __name__ == '__main__':
    init_app()
    print("Starting Web Application...")
    print("Data folder: web_data/")
    print("Access at: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)