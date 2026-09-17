"""
MQTT Configuration for centralized data management
"""

# MQTT Broker Configuration
MQTT_BROKER = "network.saark.in"
MQTT_PORT = 1884
MQTT_USERNAME = None  # Set your username if required
MQTT_PASSWORD = None  # Set your password if required

# Database Configuration
CENTRAL_DB_PATH = "central_database.db"

# Topic Structure
TOPICS = {
    'customers': 'crm/customers/+',
    'production_batches': 'production/batches/+',
    'testing_records': 'production/testing/+',
    'enquiry_status': 'crm/enquiry_status/+',
    'sync_status': 'system/sync/+'
}

# Synchronization Settings
SYNC_INTERVAL = 60  # Seconds between sync checks
AUTO_SYNC = True
SYNC_ON_STARTUP = True

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "mqtt_sync.log"

# Client ID Generation
import socket
import time

def generate_client_id():
    """Generate unique client ID based on hostname and timestamp."""
    hostname = socket.gethostname()
    timestamp = int(time.time())
    return f"{hostname}_{timestamp}"

# Use this for unique client identification
CLIENT_ID = generate_client_id()