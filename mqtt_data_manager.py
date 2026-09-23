

#newly 
import json
import sqlite3
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional
import logging
from mqtt_client import MQTTClient

logger = logging.getLogger(__name__)

class CentralDataManager:
    """Centralized data manager using MQTT for synchronization."""
    
    def __init__(self, mqtt_broker: str = "network.saark.in", mqtt_port: int = 1884,
                 db_path: str = "central_database.db", 
                 mqtt_username: str = None, mqtt_password: str = None,
                 client_id: str = None):
        """
        Initialize centralized data manager.
        
        Args:
            mqtt_broker: MQTT broker address
            mqtt_port: MQTT broker port
            db_path: Path to local SQLite database
            mqtt_username: MQTT username (if required)
            mqtt_password: MQTT password (if required)
            client_id: Unique client identifier
        """
        self.db_path = db_path
        self.client_id = client_id or f"data_manager_{int(datetime.now().timestamp())}"
        
        # Initialize MQTT client
        self.mqtt_client = MQTTClient(
            broker=mqtt_broker,
            port=mqtt_port,
            client_id=self.client_id,
            username=mqtt_username,
            password=mqtt_password
        )
        
        # Initialize local database
        self.init_database()
        
        # Subscribe to data update topics
        self.setup_mqtt_subscriptions()
        
        logger.info(f"CentralDataManager initialized with client ID: {self.client_id}")
    
    def init_database(self):
        """Initialize local SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
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
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create production data table
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
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
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
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES production_batches(id)
                )
            """)
            
            # Create enquiry status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enquiry_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'Pending',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sync log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT,
                    table_name TEXT,
                    record_id INTEGER,
                    direction TEXT, -- 'sent' or 'received'
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def setup_mqtt_subscriptions(self):
        """Set up MQTT subscriptions for data synchronization."""
        # Subscribe to customer data updates
        self.mqtt_client.subscribe("crm/customers/+", self.handle_customer_update)
        
        # Subscribe to production data updates
        self.mqtt_client.subscribe("production/batches/+", self.handle_production_update)
        
        # Subscribe to testing records
        self.mqtt_client.subscribe("production/testing/+", self.handle_testing_update)
        
        # Subscribe to enquiry status updates
        self.mqtt_client.subscribe("crm/enquiry_status/+", self.handle_enquiry_status_update)
        
        logger.info("MQTT subscriptions set up")
    
    def handle_customer_update(self, topic: str, data: dict):
        """Handle incoming customer data update."""
        try:
            operation = data.get('operation', 'upsert')
            customer_data = data.get('data', {})
            
            if operation == 'delete':
                self.delete_customer(customer_data.get('company_name'))
            else:
                self.upsert_customer(customer_data)
                
            self.log_sync_operation('customers', operation, 'received', 'success')
            
        except Exception as e:
            logger.error(f"Error handling customer update: {e}")
            self.log_sync_operation('customers', operation, 'received', 'error')
    
    def handle_production_update(self, topic: str, data: dict):
        """Handle incoming production batch update."""
        try:
            operation = data.get('operation', 'upsert')
            batch_data = data.get('data', {})
            
            if operation == 'delete':
                self.delete_production_batch(batch_data.get('batch_number'))
            else:
                self.upsert_production_batch(batch_data)
                
            self.log_sync_operation('production_batches', operation, 'received', 'success')
            
        except Exception as e:
            logger.error(f"Error handling production update: {e}")
            self.log_sync_operation('production_batches', operation, 'received', 'error')
    
    def handle_testing_update(self, topic: str, data: dict):
        """Handle incoming testing record update."""
        try:
            operation = data.get('operation', 'upsert')
            testing_data = data.get('data', {})
            
            if operation == 'delete':
                self.delete_testing_record(testing_data.get('product_id'))
            else:
                self.upsert_testing_record(testing_data)
                
            self.log_sync_operation('testing_records', operation, 'received', 'success')
            
        except Exception as e:
            logger.error(f"Error handling testing update: {e}")
            self.log_sync_operation('testing_records', operation, 'received', 'error')
    
    def handle_enquiry_status_update(self, topic: str, data: dict):
        """Handle incoming enquiry status update."""
        try:
            operation = data.get('operation', 'upsert')
            status_data = data.get('data', {})
            
            if operation == 'delete':
                self.delete_enquiry_status(status_data.get('company_name'))
            else:
                self.upsert_enquiry_status(status_data)
                
            self.log_sync_operation('enquiry_status', operation, 'received', 'success')
            
        except Exception as e:
            logger.error(f"Error handling enquiry status update: {e}")
            self.log_sync_operation('enquiry_status', operation, 'received', 'error')
    
    def upsert_customer(self, customer_data: dict) -> bool:
        """Insert or update customer record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE company_name = ?", 
                         (customer_data.get('company_name'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_fields = [f"{k} = ?" for k in customer_data.keys() if k != 'company_name']
                update_values = [v for k, v in customer_data.items() if k != 'company_name']
                update_values.append(customer_data['company_name'])
                
                query = f"""
                    UPDATE customers 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP, last_synced = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                """
                cursor.execute(query, update_values)
            else:
                # Insert new record
                fields = list(customer_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO customers ({', '.join(fields)}, last_synced)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                """
                cursor.execute(query, list(customer_data.values()))
            
            conn.commit()
            conn.close()
            logger.info(f"Customer {customer_data.get('company_name')} upserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting customer: {e}")
            return False
    
    def delete_customer(self, company_name: str) -> bool:
        """Delete customer record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE company_name = ?", (company_name,))
            conn.commit()
            conn.close()
            logger.info(f"Customer {company_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            return False
    
    def upsert_production_batch(self, batch_data: dict) -> bool:
        """Insert or update production batch record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if batch exists
            cursor.execute("SELECT id FROM production_batches WHERE batch_number = ?", 
                         (batch_data.get('batch_number'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_fields = [f"{k} = ?" for k in batch_data.keys() if k != 'batch_number']
                update_values = [v for k, v in batch_data.items() if k != 'batch_number']
                update_values.append(batch_data['batch_number'])
                
                query = f"""
                    UPDATE production_batches 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP, last_synced = CURRENT_TIMESTAMP
                    WHERE batch_number = ?
                """
                cursor.execute(query, update_values)
            else:
                # Insert new record
                fields = list(batch_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO production_batches ({', '.join(fields)}, last_synced)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                """
                cursor.execute(query, list(batch_data.values()))
            
            conn.commit()
            conn.close()
            logger.info(f"Production batch {batch_data.get('batch_number')} upserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting production batch: {e}")
            return False
    
    def delete_production_batch(self, batch_number: str) -> bool:
        """Delete production batch record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM production_batches WHERE batch_number = ?", (batch_number,))
            conn.commit()
            conn.close()
            logger.info(f"Production batch {batch_number} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting production batch: {e}")
            return False
    
    def upsert_testing_record(self, testing_data: dict) -> bool:
        """Insert or update testing record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if testing record exists
            cursor.execute("SELECT id FROM testing_records WHERE product_id = ?", 
                         (testing_data.get('product_id'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_fields = [f"{k} = ?" for k in testing_data.keys() if k != 'product_id']
                update_values = [v for k, v in testing_data.items() if k != 'product_id']
                update_values.append(testing_data['product_id'])
                
                query = f"""
                    UPDATE testing_records 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP, last_synced = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """
                cursor.execute(query, update_values)
            else:
                # Insert new record
                fields = list(testing_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO testing_records ({', '.join(fields)}, last_synced)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                """
                cursor.execute(query, list(testing_data.values()))
            
            conn.commit()
            conn.close()
            logger.info(f"Testing record {testing_data.get('product_id')} upserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting testing record: {e}")
            return False
    
    def delete_testing_record(self, product_id: str) -> bool:
        """Delete testing record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM testing_records WHERE product_id = ?", (product_id,))
            conn.commit()
            conn.close()
            logger.info(f"Testing record {product_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting testing record: {e}")
            return False
    
    def upsert_enquiry_status(self, status_data: dict) -> bool:
        """Insert or update enquiry status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if status exists
            cursor.execute("SELECT id FROM enquiry_status WHERE company_name = ?", 
                         (status_data.get('company_name'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE enquiry_status 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP, last_synced = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                """, (status_data.get('status'), status_data.get('company_name')))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO enquiry_status (company_name, status, last_synced)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (status_data.get('company_name'), status_data.get('status')))
            
            conn.commit()
            conn.close()
            logger.info(f"Enquiry status for {status_data.get('company_name')} upserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting enquiry status: {e}")
            return False
    
    def delete_enquiry_status(self, company_name: str) -> bool:
        """Delete enquiry status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM enquiry_status WHERE company_name = ?", (company_name,))
            conn.commit()
            conn.close()
            logger.info(f"Enquiry status for {company_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting enquiry status: {e}")
            return False
    
    def publish_customer_update(self, customer_data: dict, operation: str = 'upsert') -> bool:
        """Publish customer data update via MQTT."""
        topic = f"crm/customers/{customer_data.get('company_name', 'unknown')}"
        payload = {
            'operation': operation,
            'data': customer_data,
            'timestamp': datetime.now().isoformat(),
            'client_id': self.client_id
        }
        return self.mqtt_client.publish(topic, payload)
    
    def publish_production_update(self, batch_data: dict, operation: str = 'upsert') -> bool:
        """Publish production batch update via MQTT."""
        topic = f"production/batches/{batch_data.get('batch_number', 'unknown')}"
        payload = {
            'operation': operation,
            'data': batch_data,
            'timestamp': datetime.now().isoformat(),
            'client_id': self.client_id
        }
        return self.mqtt_client.publish(topic, payload)
    
    def publish_testing_update(self, testing_data: dict, operation: str = 'upsert') -> bool:
        """Publish testing record update via MQTT."""
        topic = f"production/testing/{testing_data.get('product_id', 'unknown')}"
        payload = {
            'operation': operation,
            'data': testing_data,
            'timestamp': datetime.now().isoformat(),
            'client_id': self.client_id
        }
        return self.mqtt_client.publish(topic, payload)
    
    def publish_enquiry_status_update(self, status_data: dict, operation: str = 'upsert') -> bool:
        """Publish enquiry status update via MQTT."""
        topic = f"crm/enquiry_status/{status_data.get('company_name', 'unknown')}"
        payload = {
            'operation': operation,
            'data': status_data,
            'timestamp': datetime.now().isoformat(),
            'client_id': self.client_id
        }
        return self.mqtt_client.publish(topic, payload)
    
    def log_sync_operation(self, table_name: str, operation: str, direction: str, status: str):
        """Log synchronization operation."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_log (operation, table_name, direction, status)
                VALUES (?, ?, ?, ?)
            """, (operation, table_name, direction, status))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging sync operation: {e}")
    
    def get_all_customers(self) -> List[dict]:
        """Get all customers from local database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY updated_at DESC")
            customers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return customers
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return []
    
    def get_all_production_batches(self) -> List[dict]:
        """Get all production batches from local database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM production_batches ORDER BY updated_at DESC")
            batches = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return batches
        except Exception as e:
            logger.error(f"Error getting production batches: {e}")
            return []
    
    def get_enquiry_statuses(self) -> dict:
        """Get all enquiry statuses."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT company_name, status FROM enquiry_status")
            statuses = {row['company_name']: row['status'] for row in cursor.fetchall()}
            conn.close()
            return statuses
        except Exception as e:
            logger.error(f"Error getting enquiry statuses: {e}")
            return {}
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.mqtt_client.disconnect()
        logger.info("CentralDataManager disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.mqtt_client.is_connected()