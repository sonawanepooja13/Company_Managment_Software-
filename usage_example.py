"""
Example usage of Enhanced Data Manager in CRM/Production Software
"""

from enhanced_data_manager import EnhancedDataManager
from system_config import SystemConfig

def example_usage():
    """Example of how to use the enhanced data manager."""
    
    print("=" * 60)
    print("Enhanced Data Manager Usage Example")
    print("=" * 60)
    
    # Initialize data manager (automatically detects server/client role)
    data_manager = EnhancedDataManager()
    
    print(f"System Role: {data_manager.get_system_role().upper()}")
    print(f"MQTT Connected: {data_manager.is_connected()}")
    print()
    
    # Example 1: Customer Data Operations
    print("Example 1: Customer Data Operations")
    print("-" * 60)
    
    customer_data = {
        'company_name': 'Example Company',
        'contact_person': 'John Doe',
        'contact_number': '1234567890',
        'enquiry_received': 'Yes',
        'state': 'Maharashtra',
        'district': 'Mumbai'
    }
    
    # Add/update customer
    if data_manager.upsert_customer(customer_data):
        print("✓ Customer added/updated successfully")
        
        # If client, publish to server
        if data_manager.get_system_role() == 'client':
            if data_manager.publish_to_server('customers', customer_data, 'upsert'):
                print("✓ Customer data published to server")
    else:
        print("✗ Failed to add/update customer")
    
    # Get all customers
    customers = data_manager.get_all_customers()
    print(f"Total customers: {len(customers)}")
    
    print()
    
    # Example 2: Enquiry Status Operations
    print("Example 2: Enquiry Status Operations")
    print("-" * 60)
    
    status_data = {
        'company_name': 'Example Company',
        'status': 'Complete'
    }
    
    # Update enquiry status
    if data_manager.upsert_enquiry_status(status_data):
        print("✓ Enquiry status updated successfully")
        
        # If client, publish to server
        if data_manager.get_system_role() == 'client':
            if data_manager.publish_to_server('enquiry_status', status_data, 'upsert'):
                print("✓ Enquiry status published to server")
    else:
        print("✗ Failed to update enquiry status")
    
    # Get all enquiry statuses
    statuses = data_manager.get_enquiry_statuses()
    print(f"Total enquiry statuses: {len(statuses)}")
    
    print()
    
    # Example 3: Production Batch Operations
    print("Example 3: Production Batch Operations")
    print("-" * 60)
    
    batch_data = {
        'batch_number': 'BATCH-001',
        'product_name': 'Booster Pump Panel',
        'start_date': '2026-09-09',
        'status': 'In Progress'
    }
    
    # Add production batch
    if data_manager.upsert_production_batch(batch_data):
        print("✓ Production batch added successfully")
        
        # If client, publish to server
        if data_manager.get_system_role() == 'client':
            if data_manager.publish_to_server('production_batches', batch_data, 'upsert'):
                print("✓ Production batch published to server")
    else:
        print("✗ Failed to add production batch")
    
    # Get all production batches
    batches = data_manager.get_all_production_batches()
    print(f"Total production batches: {len(batches)}")
    
    print()
    
    # Example 4: Testing Record Operations
    print("Example 4: Testing Record Operations")
    print("-" * 60)
    
    testing_data = {
        'product_id': 'PROD-001',
        'user_name': 'Test User',
        'tested_ok': 'Yes',
        'visual_inspection_data': 'Passed all checks'
    }
    
    # Add testing record
    if data_manager.upsert_testing_record(testing_data):
        print("✓ Testing record added successfully")
        
        # If client, publish to server
        if data_manager.get_system_role() == 'client':
            if data_manager.publish_to_server('testing_records', testing_data, 'upsert'):
                print("✓ Testing record published to server")
    else:
        print("✗ Failed to add testing record")
    
    print()
    
    # Example 5: View Sync Logs
    print("Example 5: View Sync Logs")
    print("-" * 60)
    
    try:
        import sqlite3
        conn = sqlite3.connect(data_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT 5")
        logs = cursor.fetchall()
        
        if logs:
            print("Recent sync operations:")
            for log in logs:
                print(f"  {log}")
        else:
            print("No sync operations logged yet")
        
        conn.close()
    except Exception as e:
        print(f"Error viewing sync logs: {e}")
    
    print()
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    
    # Cleanup
    data_manager.disconnect()


def check_system_configuration():
    """Check and display current system configuration."""
    print("=" * 60)
    print("System Configuration Check")
    print("=" * 60)
    
    config = SystemConfig()
    config.display_config()
    
    print()
    print("Configuration file location: system_config.json")
    print("To reconfigure, run: python setup_system.py")


if __name__ == "__main__":
    print("Choose option:")
    print("1. Check system configuration")
    print("2. Run usage example")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        check_system_configuration()
    elif choice == '2':
        example_usage()
    else:
        print("Invalid choice")