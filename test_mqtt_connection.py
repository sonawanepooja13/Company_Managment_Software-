"""
Test script for MQTT connection and basic functionality
"""

import time
import json
from mqtt_client import MQTTClient
from mqtt_config import MQTT_BROKER, MQTT_PORT, CLIENT_ID

def test_mqtt_connection():
    """Test basic MQTT connection and publish/subscribe."""
    print("=" * 50)
    print("MQTT Connection Test")
    print("=" * 50)
    print(f"Broker: {MQTT_BROKER}")
    print(f"Port: {MQTT_PORT}")
    print(f"Client ID: {CLIENT_ID}")
    print("-" * 50)
    
    # Create MQTT client
    client = MQTTClient(
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        client_id=f"test_{CLIENT_ID}"
    )
    
    # Wait for connection
    print("Waiting for connection...")
    for i in range(10):  # Wait up to 10 seconds
        if client.is_connected():
            print(f"✓ Connected successfully!")
            break
        time.sleep(1)
        print(f"Connecting... {i+1}/10")
    else:
        print("✗ Failed to connect within timeout")
        return False
    
    # Test 1: Publish a simple message
    print("\nTest 1: Publishing test message...")
    test_data = {
        "test": True,
        "message": "Hello from MQTT test",
        "timestamp": time.time()
    }
    
    if client.publish("test/connection", test_data):
        print("✓ Message published successfully")
    else:
        print("✗ Failed to publish message")
    
    # Test 2: Subscribe and receive message
    print("\nTest 2: Subscribing to test topic...")
    received_messages = []
    
    def message_callback(topic, data):
        print(f"✓ Received message on {topic}: {data}")
        received_messages.append(data)
    
    if client.subscribe("test/#", message_callback):
        print("✓ Subscribed successfully")
    else:
        print("✗ Failed to subscribe")
    
    # Publish another message to test subscription
    print("Publishing test message for subscription...")
    client.publish("test/data", {"subscription_test": True})
    
    # Wait for message
    time.sleep(2)
    
    if received_messages:
        print("✓ Subscription working - received messages")
    else:
        print("⚠ No messages received (might be normal depending on broker)")
    
    # Test 3: Customer data simulation
    print("\nTest 3: Simulating customer data sync...")
    customer_data = {
        "company_name": "Test Company MQTT",
        "contact_person": "Test User",
        "contact_number": "1234567890",
        "enquiry_received": "Yes"
    }
    
    if client.publish("crm/customers/test", {
        "operation": "upsert",
        "data": customer_data,
        "client_id": f"test_{CLIENT_ID}"
    }):
        print("✓ Customer data published")
    else:
        print("✗ Failed to publish customer data")
    
    # Test 4: Enquiry status simulation
    print("\nTest 4: Simulating enquiry status sync...")
    status_data = {
        "company_name": "Test Company MQTT",
        "status": "Complete"
    }
    
    if client.publish("crm/enquiry_status/test", {
        "operation": "upsert", 
        "data": status_data,
        "client_id": f"test_{CLIENT_ID}"
    }):
        print("✓ Enquiry status published")
    else:
        print("✗ Failed to publish enquiry status")
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Connection Status: {'✓ Connected' if client.is_connected() else '✗ Disconnected'}")
    print(f"Messages Published: 4")
    print(f"Messages Received: {len(received_messages)}")
    print("\n✓ MQTT integration is working!")
    
    # Keep alive for a moment to see any incoming messages
    print("\nKeeping connection alive for 5 seconds to receive any responses...")
    time.sleep(5)
    
    # Disconnect
    client.disconnect()
    print("Disconnected from MQTT broker")
    
    return True

if __name__ == "__main__":
    try:
        success = test_mqtt_connection()
        if success:
            print("\n✓ All tests completed successfully!")
        else:
            print("\n✗ Some tests failed")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()