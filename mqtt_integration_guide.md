# MQTT Integration Guide for Centralized Data Management

## Overview
This system uses MQTT for real-time data synchronization between multiple computers running your CRM/Production software. All data is synchronized to a central database via your MQTT broker at `network.saark.in:1884`.

## Architecture

```
User Computer 1 → MQTT → Central Database
User Computer 2 → MQTT → Central Database  
User Computer 3 → MQTT → Central Database
                    ↓
              Main Computer (Optional)
```

## Setup Instructions

### 1. Install Required Packages
```bash
pip install paho-mqtt
```

### 2. Configuration
Edit `mqtt_config.py` if needed:
- MQTT_BROKER: "network.saark.in" (already set)
- MQTT_PORT: 1884 (already set)
- MQTT_USERNAME: Set if your broker requires authentication
- MQTT_PASSWORD: Set if your broker requires authentication

### 3. Database Setup
The system automatically creates a local SQLite database (`central_database.db`) that:
- Stores all data locally for offline access
- Syncs with MQTT when connected
- Maintains sync logs for debugging

## MQTT Topic Structure

### Customer Data
- **Topic**: `crm/customers/{company_name}`
- **Operations**: `upsert`, `delete`
- **Data**: Full customer record

### Production Data
- **Topic**: `production/batches/{batch_number}`
- **Operations**: `upsert`, `delete`
- **Data**: Production batch information

### Testing Records
- **Topic**: `production/testing/{product_id}`
- **Operations**: `upsert`, `delete`
- **Data**: Testing and inspection records

### Enquiry Status
- **Topic**: `crm/enquiry_status/{company_name}`
- **Operations**: `upsert`, `delete`
- **Data**: Enquiry status information

## Integration Points

### CRM Tab Integration
The CRM tab automatically:
- Publishes customer data when saved
- Publishes enquiry status updates
- Subscribes to remote updates
- Maintains local CSV file compatibility

### Production Window Integration
Production window can be integrated to:
- Publish batch information
- Publish testing records
- Subscribe to production updates

## Usage Examples

### Basic MQTT Client Usage
```python
from mqtt_client import MQTTClient

# Create client
client = MQTTClient(broker="network.saark.in", port=1884, client_id="my_app")

# Wait for connection
import time
time.sleep(3)

# Publish data
client.publish("test/topic", {"message": "Hello World"})

# Subscribe to updates
def my_callback(topic, data):
    print(f"Received: {data}")

client.subscribe("test/#", my_callback)
```

### Data Manager Usage
```python
from mqtt_data_manager import CentralDataManager

# Create manager
manager = CentralDataManager(
    mqtt_broker="network.saark.in",
    mqtt_port=1884,
    db_path="my_database.db"
)

# Wait for connection
import time
time.sleep(3)

# Save customer data (auto-syncs via MQTT)
customer_data = {
    'company_name': 'Test Company',
    'contact_person': 'John Doe',
    'contact_number': '1234567890',
    # ... other fields
}
manager.upsert_customer(customer_data)

# Get all customers
customers = manager.get_all_customers()
```

## Features

### Automatic Synchronization
- Data automatically syncs when MQTT is connected
- Local database works offline
- Conflict resolution based on timestamp

### Real-time Updates
- Subscribe to topics for instant updates
- Automatic UI refresh when data changes
- Status indicators for sync state

### Error Handling
- Automatic reconnection on connection loss
- Graceful degradation when offline
- Detailed logging for debugging

### Security
- Authentication support (username/password)
- SSL/TLS support (if broker supports it)
- Client-specific identification

## Troubleshooting

### Connection Issues
1. Check broker status: `network.saark.in:1884`
2. Verify network connectivity
3. Check firewall settings
4. Review `mqtt_sync.log` for errors

### Data Not Syncing
1. Verify MQTT connection status
2. Check topic subscriptions
3. Review sync logs in database
4. Test with simple publish/subscribe

### Performance Issues
1. Reduce QoS level (default is 0)
2. Batch operations instead of individual updates
3. Consider message compression for large data

## Monitoring

### Check Connection Status
```python
if manager.is_connected():
    print("Connected to MQTT broker")
else:
    print("Not connected")
```

### View Sync Logs
```python
# Query sync log table
SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT 10;
```

### Monitor Database
```python
# Check last sync times
SELECT company_name, last_synced FROM customers ORDER BY last_synced DESC;
```

## Best Practices

1. **Unique Client IDs**: Each installation should have a unique client ID
2. **Error Handling**: Always check connection status before operations
3. **Data Validation**: Validate data before publishing
4. **Backup Strategy**: Regular database backups
5. **Network Stability**: Handle connection drops gracefully

## Future Enhancements

- Web dashboard for monitoring
- Mobile app integration
- Advanced conflict resolution
- Data encryption
- User authentication
- Role-based access control

## Support

For issues or questions:
1. Check logs in `mqtt_sync.log`
2. Verify broker status
3. Test with provided example scripts
4. Review database sync logs

## License

This MQTT integration is part of your CRM/Production management system.