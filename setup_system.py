"""
Setup script for configuring main server and client computers
"""

import sys
import os

def main():
    print("=" * 60)
    print("CRM/Production System Setup")
    print("=" * 60)
    print()
    print("This script will help you configure your computer as either:")
    print("1. MAIN SERVER - Hosts the central database")
    print("2. CLIENT COMPUTER - Connects to the main server")
    print()
    
    print("Your computer information:")
    from system_config import SystemConfig
    config = SystemConfig()
    
    print(f"  Hostname: {config.system_info['hostname']}")
    print(f"  IP Address: {config.system_info['ip_address']}")
    print(f"  Platform: {config.system_info['platform']}")
    print()
    
    print("Current configuration:")
    if os.path.exists(SystemConfig.CONFIG_FILE):
        config.display_config()
        print()
        print("Do you want to reconfigure? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("Setup cancelled. Current configuration preserved.")
            return
    else:
        print("No existing configuration found.")
        print()
    
    print("=" * 60)
    print("Setup Options:")
    print("=" * 60)
    print("1. Configure as MAIN SERVER")
    print("2. Configure as CLIENT COMPUTER")
    print("3. Test MQTT Connection")
    print("4. View Current Configuration")
    print("5. Exit")
    print()
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == '1':
        setup_server(config)
    elif choice == '2':
        setup_client(config)
    elif choice == '3':
        test_connection()
    elif choice == '4':
        config.display_config()
    elif choice == '5':
        print("Exiting setup.")
    else:
        print("Invalid choice. Please run the script again.")


def setup_server(config):
    """Configure computer as main server."""
    print("\n" + "=" * 60)
    print("MAIN SERVER Configuration")
    print("=" * 60)
    print()
    print("This computer will:")
    print("  - Host the central database")
    print("  - Receive data from all client computers")
    print("  - Broadcast updates to all clients")
    print("  - Act as the main data repository")
    print()
    
    db_path = input("Enter database path (default: central_database.db): ").strip()
    if not db_path:
        db_path = 'central_database.db'
    
    print()
    print("Configuring as MAIN SERVER...")
    config.set_as_server(db_path)
    
    print()
    print("✓ Server configuration complete!")
    print()
    print("Next steps:")
    print("1. Run your CRM/Production software on this computer")
    print("2. Configure other computers as CLIENTS")
    print("3. Use this server's information for client setup:")
    print(f"   Hostname: {config.system_info['hostname']}")
    print(f"   IP Address: {config.system_info['ip_address']}")


def setup_client(config):
    """Configure computer as client."""
    print("\n" + "=" * 60)
    print("CLIENT COMPUTER Configuration")
    print("=" * 60)
    print()
    print("This computer will:")
    print("  - Connect to the main server via MQTT")
    print("  - Send data to the central database")
    print("  - Receive updates from the server")
    print("  - Maintain a local cache of data")
    print()
    
    server_hostname = input("Enter MAIN SERVER hostname (optional): ").strip()
    server_ip = input("Enter MAIN SERVER IP address (optional): ").strip()
    
    if not server_hostname and not server_ip:
        print("Warning: No server information provided.")
        print("The system will work but won't track the specific server.")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print()
    print("Configuring as CLIENT...")
    config.set_as_client(server_hostname or None, server_ip or None)
    
    print()
    print("✓ Client configuration complete!")
    print()
    print("Next steps:")
    print("1. Run your CRM/Production software on this computer")
    print("2. Data will automatically sync with the main server")
    print("3. You can work offline - data will sync when connected")


def test_connection():
    """Test MQTT connection."""
    print("\n" + "=" * 60)
    print("MQTT Connection Test")
    print("=" * 60)
    print()
    
    try:
        from mqtt_client import MQTTClient
        from mqtt_config import MQTT_BROKER, MQTT_PORT
        
        print(f"Testing connection to: {MQTT_BROKER}:{MQTT_PORT}")
        print()
        
        client = MQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="setup_test")
        
        print("Waiting for connection...")
        import time
        for i in range(10):
            if client.is_connected():
                print(f"✓ Connected successfully!")
                break
            time.sleep(1)
            print(f"Connecting... {i+1}/10")
        else:
            print("✗ Failed to connect within timeout")
            print()
            print("Troubleshooting:")
            print("1. Check if broker is running: network.saark.in:1884")
            print("2. Verify network connectivity")
            print("3. Check firewall settings")
            print("4. Ensure port 1884 is accessible")
            return
        
        # Test publish
        print()
        print("Testing publish...")
        if client.publish("test/setup", {"test": "setup_script"}):
            print("✓ Publish successful")
        else:
            print("✗ Publish failed")
        
        print()
        print("✓ MQTT connection is working!")
        client.disconnect()
        
    except ImportError:
        print("✗ MQTT client not available. Install with: pip install paho-mqtt")
    except Exception as e:
        print(f"✗ Connection test failed: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()