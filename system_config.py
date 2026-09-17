"""
System Configuration for Server/Client Roles
"""

import os
import json
import socket
import platform

class SystemConfig:
    """Manages system configuration for server/client roles."""
    
    CONFIG_FILE = "system_config.json"
    
    def __init__(self):
        self.config = self.load_config()
        self.system_info = self.get_system_info()
    
    def get_system_info(self):
        """Get system identification information."""
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'ip_address': self.get_local_ip(),
            'user': os.getenv('USERNAME') if platform.system() == 'Windows' else os.getenv('USER')
        }
    
    def get_local_ip(self):
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def load_config(self):
        """Load configuration from file or create default."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration."""
        return {
            'system_role': 'client',  # 'server' or 'client'
            'server_info': {
                'hostname': None,
                'ip_address': None,
                'database_path': 'central_database.db'
            },
            'mqtt_config': {
                'broker': 'network.saark.in',
                'port': 1884,
                'username': None,
                'password': None
            },
            'database_config': {
                'local_db_path': 'local_database.db',
                'sync_enabled': True,
                'sync_interval': 60
            },
            'system_info': self.system_info
        }
    
    def save_config(self):
        """Save configuration to file."""
        self.config['system_info'] = self.system_info
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def set_as_server(self, database_path='central_database.db'):
        """Configure this computer as the main server."""
        self.config['system_role'] = 'server'
        self.config['server_info'] = {
            'hostname': self.system_info['hostname'],
            'ip_address': self.system_info['ip_address'],
            'database_path': database_path
        }
        self.config['database_config']['local_db_path'] = database_path
        self.save_config()
        print(f"✓ Configured as SERVER")
        print(f"  Hostname: {self.system_info['hostname']}")
        print(f"  IP Address: {self.system_info['ip_address']}")
        print(f"  Database: {database_path}")
    
    def set_as_client(self, server_hostname=None, server_ip=None):
        """Configure this computer as a client."""
        self.config['system_role'] = 'client'
        self.config['server_info'] = {
            'hostname': server_hostname,
            'ip_address': server_ip,
            'database_path': None  # Clients don't host the database
        }
        self.config['database_config']['local_db_path'] = 'local_database.db'
        self.save_config()
        print(f"✓ Configured as CLIENT")
        if server_hostname:
            print(f"  Server Hostname: {server_hostname}")
        if server_ip:
            print(f"  Server IP: {server_ip}")
    
    def is_server(self):
        """Check if this system is configured as server."""
        return self.config.get('system_role') == 'server'
    
    def is_client(self):
        """Check if this system is configured as client."""
        return self.config.get('system_role') == 'client'
    
    def get_server_info(self):
        """Get server information."""
        return self.config.get('server_info', {})
    
    def get_mqtt_config(self):
        """Get MQTT configuration."""
        return self.config.get('mqtt_config', {})
    
    def get_database_config(self):
        """Get database configuration."""
        return self.config.get('database_config', {})
    
    def display_config(self):
        """Display current configuration."""
        print("=" * 50)
        print("System Configuration")
        print("=" * 50)
        print(f"Role: {self.config['system_role'].upper()}")
        print(f"Hostname: {self.system_info['hostname']}")
        print(f"IP Address: {self.system_info['ip_address']}")
        print(f"Platform: {self.system_info['platform']}")
        print(f"User: {self.system_info['user']}")
        print("-" * 50)
        print("Server Info:")
        server_info = self.config['server_info']
        print(f"  Hostname: {server_info.get('hostname', 'Not set')}")
        print(f"  IP Address: {server_info.get('ip_address', 'Not set')}")
        print(f"  Database Path: {server_info.get('database_path', 'Not set')}")
        print("-" * 50)
        print("MQTT Config:")
        mqtt_config = self.config['mqtt_config']
        print(f"  Broker: {mqtt_config.get('broker', 'Not set')}")
        print(f"  Port: {mqtt_config.get('port', 'Not set')}")
        print(f"  Username: {mqtt_config.get('username', 'Not set')}")
        print("=" * 50)


def setup_wizard():
    """Interactive setup wizard for system configuration."""
    print("=" * 50)
    print("System Setup Wizard")
    print("=" * 50)
    print()
    
    config = SystemConfig()
    print("Current System Information:")
    print(f"  Hostname: {config.system_info['hostname']}")
    print(f"  IP Address: {config.system_info['ip_address']}")
    print(f"  Platform: {config.system_info['platform']}")
    print()
    
    print("Select system role:")
    print("1. Main Server (Hosts central database)")
    print("2. Client Computer (Connects to server)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        print("\nConfiguring as MAIN SERVER...")
        db_path = input("Enter database path (default: central_database.db): ").strip()
        if not db_path:
            db_path = 'central_database.db'
        
        config.set_as_server(db_path)
        
    elif choice == '2':
        print("\nConfiguring as CLIENT...")
        server_hostname = input("Enter server hostname (optional): ").strip()
        server_ip = input("Enter server IP address (optional): ").strip()
        
        config.set_as_client(server_hostname or None, server_ip or None)
        
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\n" + "=" * 50)
    print("Configuration Complete!")
    print("=" * 50)
    config.display_config()


if __name__ == "__main__":
    setup_wizard()