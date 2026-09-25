"""
Enhanced Data Manager that supports both Server and Client modes
"""

import sqlite3
import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
from mqtt_client import MQTTClient
from system_config import SystemConfig

logger = logging.getLogger(__name__)

class EnhancedDataManager:
    """Enhanced data manager supporting server and client modes."""
    
    def __init__(self):
        """Initialize data manager based on system configuration."""
        self.config = SystemConfig()
        self.system_role = self.config.config['system_role']
        
        logger.info(f"Initializing as {self.system_role.upper()}")
        
        # Initialize based on role
        if self.system_role == 'server':
            self.init_server_mode()
        else:
            self.init_client_mode()
    
    def init_server_mode(self):
        """Initialize as main server."""
        logger.info("Starting in SERVER mode")
        
        # Get server configuration
        server_info = self.config.get_server_info()
        mqtt_config = self.config.get_mqtt_config()
        db_config = self.config.get_database_config()
        
        # Database path
        self.db_path = server_info.get('database_path', 'central_database.db')
        
        # Initialize central database
        self.init_central_database()
        
        # Initialize MQTT client (server also acts as MQTT client for syncing)
        self.mqtt_client = MQTTClient(
            broker=mqtt_config.get('broker', 'network.saark.in'),
            port=mqtt_config.get('port', 1884),
            client_id=f"server_{self.config.system_info['hostname']}",
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password')
        )
        
        # Subscribe to all data topics for central collection
        self.setup_server_subscriptions()
        
        logger.info(f"Server initialized with database: {self.db_path}")
    
    def init_client_mode(self):
        """Initialize as client."""
        logger.info("Starting in CLIENT mode")
        
        # Get client configuration
        mqtt_config = self.config.get_mqtt_config()
        db_config = self.config.get_database_config()
        
        # Database path (local cache)
        self.db_path = db_config.get('local_db_path', 'local_database.db')
        
        # Initialize local database
        self.init_local_database()
        
        # Initialize MQTT client
        self.mqtt_client = MQTTClient(
            broker=mqtt_config.get('broker', 'network.saark.in'),
            port=mqtt_config.get('port', 1884),
            client_id=f"client_{self.config.system_info['hostname']}",
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password')
        )
        
        # Subscribe to data updates from server
        self.setup_client_subscriptions()
        
        logger.info(f"Client initialized with local database: {self.db_path}")
    
    def init_central_database(self):
        """Initialize central database on server."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create all tables (comprehensive schema)
            self.create_all_tables(cursor)
            
            conn.commit()
            conn.close()
            logger.info("Central database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing central database: {e}")
            raise
    
    def init_local_database(self):
        """Initialize local database on client."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create local cache tables
            self.create_all_tables(cursor)
            
            # Add client-specific sync tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    last_synced_timestamp TEXT,
                    last_synced_from_server TEXT,
                    sync_status TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Local database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing local database: {e}")
            raise
    
    def create_all_tables(self, cursor):
        """Create all database tables."""
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
    
    def setup_server_subscriptions(self):
        """Server subscribes to all client updates."""
        # Subscribe to all data topics
        self.mqtt_client.subscribe("crm/customers/+", self.handle_server_customer_update)
        self.mqtt_client.subscribe("production/batches/+", self.handle_server_production_update)
        self.mqtt_client.subscribe("production/testing/+", self.handle_server_testing_update)
        self.mqtt_client.subscribe("crm/enquiry_status/+", self.handle_server_enquiry_update)
        
        logger.info("Server subscribed to all client data topics")
    
    def setup_client_subscriptions(self):
        """Client subscribes to server broadcasts."""
        # Subscribe to server broadcasts for data updates
        self.mqtt_client.subscribe("server/broadcast/+", self.handle_server_broadcast)
        
        logger.info("Client subscribed to server broadcasts")
    
    def handle_server_customer_update(self, topic: str, data: dict):
        """Server handles customer update from client."""
        try:
            operation = data.get('operation', 'upsert')
            customer_data = data.get('data', {})
            source_client = data.get('client_id', 'unknown')
            
            # Add server timestamp
            customer_data['server_timestamp'] = datetime.now().isoformat()
            customer_data['updated_by'] = source_client
            
            if operation == 'delete':
                self.delete_customer(customer_data.get('company_name'))
            else:
                self.upsert_customer(customer_data)
            
            # Broadcast to other clients
            self.broadcast_to_clients('customers', customer_data, operation)
            
            self.log_sync_operation('customers', operation, 'received', 'success', source_client)
            
        except Exception as e:
            logger.error(f"Error handling server customer update: {e}")
            self.log_sync_operation('customers', operation, 'received', 'error', source_client, str(e))
    
    def handle_server_production_update(self, topic: str, data: dict):
        """Server handles production update from client."""
        try:
            operation = data.get('operation', 'upsert')
            batch_data = data.get('data', {})
            source_client = data.get('client_id', 'unknown')
            
            # Add server timestamp
            batch_data['server_timestamp'] = datetime.now().isoformat()
            batch_data['updated_by'] = source_client
            
            if operation == 'delete':
                self.delete_production_batch(batch_data.get('batch_number'))
            else:
                self.upsert_production_batch(batch_data)
            
            # Broadcast to other clients
            self.broadcast_to_clients('production_batches', batch_data, operation)
            
            self.log_sync_operation('production_batches', operation, 'received', 'success', source_client)
            
        except Exception as e:
            logger.error(f"Error handling server production update: {e}")
            self.log_sync_operation('production_batches', operation, 'received', 'error', source_client, str(e))
    
    def handle_server_testing_update(self, topic: str, data: dict):
        """Server handles testing update from client."""
        try:
            operation = data.get('operation', 'upsert')
            testing_data = data.get('data', {})
            source_client = data.get('client_id', 'unknown')
            
            # Add server timestamp
            testing_data['server_timestamp'] = datetime.now().isoformat()
            testing_data['updated_by'] = source_client
            
            if operation == 'delete':
                self.delete_testing_record(testing_data.get('product_id'))
            else:
                self.upsert_testing_record(testing_data)
            
            # Broadcast to other clients
            self.broadcast_to_clients('testing_records', testing_data, operation)
            
            self.log_sync_operation('testing_records', operation, 'received', 'success', source_client)
            
        except Exception as e:
            logger.error(f"Error handling server testing update: {e}")
            self.log_sync_operation('testing_records', operation, 'received', 'error', source_client, str(e))
    
    def handle_server_enquiry_update(self, topic: str, data: dict):
        """Server handles enquiry status update from client."""
        try:
            operation = data.get('operation', 'upsert')
            status_data = data.get('data', {})
            source_client = data.get('client_id', 'unknown')
            
            # Add server timestamp
            status_data['server_timestamp'] = datetime.now().isoformat()
            status_data['updated_by'] = source_client
            
            if operation == 'delete':
                self.delete_enquiry_status(status_data.get('company_name'))
            else:
                self.upsert_enquiry_status(status_data)
            
            # Broadcast to other clients
            self.broadcast_to_clients('enquiry_status', status_data, operation)
            
            self.log_sync_operation('enquiry_status', operation, 'received', 'success', source_client)
            
        except Exception as e:
            logger.error(f"Error handling server enquiry update: {e}")
            self.log_sync_operation('enquiry_status', operation, 'received', 'error', source_client, str(e))
    
    def handle_server_broadcast(self, topic: str, data: dict):
        """Client handles broadcast from server."""
        try:
            table_name = data.get('table_name')
            operation = data.get('operation')
            record_data = data.get('data')
            
            logger.info(f"Received server broadcast for {table_name}: {operation}")
            
            # Update local database
            if table_name == 'customers':
                if operation == 'delete':
                    self.delete_customer(record_data.get('company_name'))
                else:
                    self.upsert_customer(record_data)
            elif table_name == 'production_batches':
                if operation == 'delete':
                    self.delete_production_batch(record_data.get('batch_number'))
                else:
                    self.upsert_production_batch(record_data)
            elif table_name == 'testing_records':
                if operation == 'delete':
                    self.delete_testing_record(record_data.get('product_id'))
                else:
                    self.upsert_testing_record(record_data)
            elif table_name == 'enquiry_status':
                if operation == 'delete':
                    self.delete_enquiry_status(record_data.get('company_name'))
                else:
                    self.upsert_enquiry_status(record_data)
            
            self.log_sync_operation(table_name, operation, 'received', 'success', 'server')
            
        except Exception as e:
            logger.error(f"Error handling server broadcast: {e}")
    
    def broadcast_to_clients(self, table_name: str, data: dict, operation: str):
        """Server broadcasts data updates to all clients."""
        if self.system_role != 'server':
            return
        
        broadcast_topic = f"server/broadcast/{table_name}"
        payload = {
            'table_name': table_name,
            'operation': operation,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'server_id': self.config.system_info['hostname']
        }
        
        self.mqtt_client.publish(broadcast_topic, payload)
        logger.info(f"Broadcasted {operation} for {table_name} to clients")
    
    def publish_to_server(self, table_name: str, data: dict, operation: str = 'upsert'):
        """Client publishes data to server."""
        if self.system_role != 'client':
            return False
        
        # Add client identification
        data['created_by'] = self.config.system_info['hostname']
        data['updated_by'] = self.config.system_info['hostname']
        
        if table_name == 'customers':
            topic = f"crm/customers/{data.get('company_name', 'unknown')}"
        elif table_name == 'production_batches':
            topic = f"production/batches/{data.get('batch_number', 'unknown')}"
        elif table_name == 'testing_records':
            topic = f"production/testing/{data.get('product_id', 'unknown')}"
        elif table_name == 'enquiry_status':
            topic = f"crm/enquiry_status/{data.get('company_name', 'unknown')}"
        else:
            return False
        
        payload = {
            'operation': operation,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'client_id': self.config.system_info['hostname']
        }
        
        result = self.mqtt_client.publish(topic, payload)
        
        if result:
            self.log_sync_operation(table_name, operation, 'sent', 'success', 'server')
        else:
            self.log_sync_operation(table_name, operation, 'sent', 'error', 'server')
        
        return result
    
    # Database operations (same for both server and client)
    def upsert_customer(self, customer_data: dict) -> bool:
        """Insert or update customer record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM customers WHERE company_name = ?", 
                         (customer_data.get('company_name'),))
            existing = cursor.fetchone()
            
            if existing:
                update_fields = [f"{k} = ?" for k in customer_data.keys() if k != 'company_name']
                update_values = [v for k, v in customer_data.items() if k != 'company_name']
                update_values.append(customer_data['company_name'])
                
                query = f"""
                    UPDATE customers 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                """
                cursor.execute(query, update_values)
            else:
                fields = list(customer_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO customers ({', '.join(fields)})
                    VALUES ({placeholders})
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
            
            cursor.execute("SELECT id FROM production_batches WHERE batch_number = ?", 
                         (batch_data.get('batch_number'),))
            existing = cursor.fetchone()
            
            if existing:
                update_fields = [f"{k} = ?" for k in batch_data.keys() if k != 'batch_number']
                update_values = [v for k, v in batch_data.items() if k != 'batch_number']
                update_values.append(batch_data['batch_number'])
                
                query = f"""
                    UPDATE production_batches 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE batch_number = ?
                """
                cursor.execute(query, update_values)
            else:
                fields = list(batch_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO production_batches ({', '.join(fields)})
                    VALUES ({placeholders})
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
            
            cursor.execute("SELECT id FROM testing_records WHERE product_id = ?", 
                         (testing_data.get('product_id'),))
            existing = cursor.fetchone()
            
            if existing:
                update_fields = [f"{k} = ?" for k in testing_data.keys() if k != 'product_id']
                update_values = [v for k, v in testing_data.items() if k != 'product_id']
                update_values.append(testing_data['product_id'])
                
                query = f"""
                    UPDATE testing_records 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """
                cursor.execute(query, update_values)
            else:
                fields = list(testing_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                query = f"""
                    INSERT INTO testing_records ({', '.join(fields)})
                    VALUES ({placeholders})
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
            
            cursor.execute("SELECT id FROM enquiry_status WHERE company_name = ?", 
                         (status_data.get('company_name'),))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE enquiry_status 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                """, (status_data.get('status'), status_data.get('company_name')))
            else:
                cursor.execute("""
                    INSERT INTO enquiry_status (company_name, status)
                    VALUES (?, ?)
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
    
    def log_sync_operation(self, table_name: str, operation: str, direction: str, 
                          status: str, target: str = None, error_message: str = None):
        """Log synchronization operation."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_log (operation, table_name, record_id, direction, status, source_client, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (operation, table_name, target or 'unknown', direction, status, 
                  self.config.system_info['hostname'], error_message))
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
        logger.info("EnhancedDataManager disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.mqtt_client.is_connected()
    
    def get_system_role(self) -> str:
        """Get current system role."""
        return self.system_role