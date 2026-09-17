# Server/Client Setup Guide

## 🎯 Overview

This guide explains how to configure your computers for centralized data management using MQTT. You'll have **one main server computer** that hosts the central database, and **multiple client computers** that run the CRM/Production software and sync data to the central server.

## 🖥️ Architecture

```
┌─────────────────────────────────────────────────┐
│         MAIN SERVER COMPUTER                     │
│  ┌─────────────────────────────────────────┐   │
│  │  Central Database (SQLite)               │   │
│  │  - All customer data                     │   │
│  │  - Production batches                    │   │
│  │  - Testing records                       │   │
│  │  - Enquiry statuses                       │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  MQTT Client (Server Mode)              │   │
│  │  - Receives data from clients           │   │
│  │  - Broadcasts updates to clients        │   │
│  │  - Maintains central database           │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                      ↕ MQTT (network.saark.in:1884)
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ CLIENT 1      │ │ CLIENT 2      │ │ CLIENT 3      │
│ CRM Software │ │ Production   │ │ CRM Software │
│              │ │ Software     │ │              │
│ Local Cache  │ │ Local Cache  │ │ Local Cache  │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 🚀 Quick Setup

### Step 1: Install Dependencies
On ALL computers (server and clients):
```bash
pip install paho-mqtt
```

### Step 2: Run Setup Script
On EACH computer, run:
```bash
python setup_system.py
```

### Step 3: Configure Main Server
On the computer that will host the central database:
1. Run `python setup_system.py`
2. Choose option **1** (Configure as MAIN SERVER)
3. Enter database path (or use default: `central_database.db`)
4. Note the hostname and IP address displayed

### Step 4: Configure Client Computers
On each user computer:
1. Run `python setup_system.py`
2. Choose option **2** (Configure as CLIENT COMPUTER)
3. Enter the main server's hostname or IP address
4. Complete the setup

### Step 5: Test Connection
On any computer:
1. Run `python setup_system.py`
2. Choose option **3** (Test MQTT Connection)
3. Verify connection to `network.saark.in:1884`

## 📋 Detailed Setup Instructions

### MAIN SERVER Setup

#### Requirements:
- Stable internet connection
- Sufficient disk space for database
- Ideally runs 24/7 (or at least during work hours)
- Backup strategy in place

#### Setup Process:
1. **Choose Server Computer**: Select a reliable computer as the main server
2. **Run Setup Script**: `python setup_system.py`
3. **Select Option 1**: Configure as MAIN SERVER
4. **Database Location**: Choose where to store the central database
5. **Record Information**: Note the hostname and IP address for client setup

#### Server Configuration File:
```json
{
  "system_role": "server",
  "server_info": {
    "hostname": "MAIN-SERVER-PC",
    "ip_address": "192.168.1.100",
    "database_path": "central_database.db"
  },
  "mqtt_config": {
    "broker": "network.saark.in",
    "port": 1884
  }
}
```

#### Server Responsibilities:
- Receives all data from clients via MQTT
- Stores data in central database
- Broadcasts updates to all clients
- Maintains data integrity
- Provides backup and recovery

### CLIENT COMPUTER Setup

#### Requirements:
- Internet connection (can work offline temporarily)
- CRM/Production software installed
- Configuration pointing to main server

#### Setup Process:
1. **Run Setup Script**: `python setup_system.py`
2. **Select Option 2**: Configure as CLIENT COMPUTER
3. **Server Information**: Enter main server's hostname or IP
4. **Complete Setup**: System will configure as client

#### Client Configuration File:
```json
{
  "system_role": "client",
  "server_info": {
    "hostname": "MAIN-SERVER-PC",
    "ip_address": "192.168.1.100"
  },
  "mqtt_config": {
    "broker": "network.saark.in",
    "port": 1884
  }
}
```

#### Client Features:
- Local database cache for offline work
- Automatic sync when connected
- Real-time updates from server
- Conflict resolution
- Graceful degradation

## 🔧 Advanced Configuration

### Manual Configuration

If you prefer manual configuration, edit `system_config.json`:

#### Server Configuration:
```json
{
  "system_role": "server",
  "server_info": {
    "hostname": "your-server-hostname",
    "ip_address": "192.168.1.XXX",
    "database_path": "path/to/database.db"
  }
}
```

#### Client Configuration:
```json
{
  "system_role": "client",
  "server_info": {
    "hostname": "server-hostname",
    "ip_address": "192.168.1.XXX"
  }
}
```

### MQTT Authentication

If your MQTT broker requires authentication:

1. Edit `mqtt_config.py`:
```python
MQTT_USERNAME = "your_username"
MQTT_PASSWORD = "your_password"
```

2. Re-run setup script or restart your software

### Database Location

For server, you can specify custom database location:
- During setup: Enter custom path when prompted
- Manual edit: Update `database_path` in config file

## 📊 Data Flow

### Client to Server:
```
Client (User saves data) 
  → Publish to MQTT topic 
  → Server receives via MQTT 
  → Server stores in central database 
  → Server broadcasts to other clients
```

### Server to Client:
```
Server (receives update from another client)
  → Processes data 
  → Broadcasts via MQTT 
  → Client receives broadcast 
  → Client updates local database 
  → Client UI refreshes
```

## 🔍 Verification

### Check Server Status:
```python
from system_config import SystemConfig
config = SystemConfig()
print(f"Role: {config.config['system_role']}")
config.display_config()
```

### Check MQTT Connection:
```bash
python test_mqtt_connection.py
```

### Monitor Database:
```bash
# On server
sqlite3 central_database.db
.tables
SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT 10;
```

## 🛠️ Troubleshooting

### Connection Issues:
1. **MQTT Broker**: Verify `network.saark.in:1884` is accessible
2. **Network**: Check internet connectivity
3. **Firewall**: Ensure port 1884 is not blocked
4. **Configuration**: Verify system_config.json is correct

### Sync Issues:
1. **Check Logs**: Review sync_log table in database
2. **Verify Role**: Ensure correct server/client configuration
3. **Test Connection**: Run MQTT connection test
4. **Restart**: Restart software after configuration changes

### Database Issues:
1. **Permissions**: Ensure database file is writable
2. **Disk Space**: Check available disk space
3. **Backup**: Restore from backup if corrupted
4. **Integrity**: Run database integrity check

## 🔄 Backup Strategy

### Server Backup:
```bash
# Backup database
cp central_database.db central_database_backup_$(date +%Y%m%d).db

# Or use database dump
sqlite3 central_database.db .dump > backup_$(date +%Y%m%d).sql
```

### Client Backup:
```bash
# Backup local cache
cp local_database.db local_database_backup_$(date +%Y%m%d).db
```

### Automated Backup:
Set up scheduled backups on the server computer.

## 📈 Monitoring

### Server Monitoring:
- Database size and growth
- MQTT connection status
- Sync operation logs
- Client connection status

### Client Monitoring:
- Local database sync status
- MQTT connection status
- Offline work duration
- Data consistency

## 🔒 Security Considerations

### Network Security:
- Use VPN if connecting over internet
- Configure firewall rules
- Monitor access logs

### Data Security:
- Regular backups
- User authentication (if implemented)
- Data encryption (if needed)
- Access control

## 📝 Best Practices

1. **Server Selection**: Choose reliable computer as server
2. **Regular Backups**: Automated daily backups
3. **Monitoring**: Check sync logs regularly
4. **Testing**: Test with 1-2 clients first
5. **Documentation**: Document your setup
6. **Network**: Ensure stable internet connection
7. **Updates**: Update all computers simultaneously

## 🎯 Next Steps

1. **Setup Server**: Configure main server computer
2. **Test MQTT**: Verify broker connectivity
3. **Setup Clients**: Configure user computers
4. **Test Sync**: Add test data and verify sync
5. **Deploy**: Roll out to all users
6. **Monitor**: Regular monitoring and maintenance

## 🆘 Support

For issues:
1. Check system_config.json
2. Review MQTT connection logs
3. Verify network connectivity
4. Test with simple MQTT publish/subscribe
5. Check database sync logs

Your centralized data management system is now ready for deployment!