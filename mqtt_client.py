import paho.mqtt.client as mqtt
import json
import threading
import time
from typing import Callable, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce noise from paho-mqtt library
logging.getLogger("paho.mqtt.client").setLevel(logging.WARNING)

class MQTTClient:
    """MQTT client for centralized data communication."""
    
    def __init__(self, broker: str = "network.saark.in", port: int = 1884, 
                 client_id: str = None, username: str = None, password: str = None):
        """
        Initialize MQTT client.
        
        Args:
            broker: MQTT broker address
            port: MQTT broker port
            client_id: Unique client identifier
            username: MQTT username (if required)
            password: MQTT password (if required)
        """
        self.broker = broker
        self.port = port
        self.client_id = client_id or f"client_{int(time.time())}"
        self.username = username
        self.password = password
        
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        
        self.connected = False
        self.message_callbacks = {}
        self.connection_callbacks = []
        
        # Set up authentication if provided
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Start connection in background thread
        self.connect_thread = threading.Thread(target=self._connect_background, daemon=True)
        self.connect_thread.start()
    
    def _connect_background(self):
        """Connect to MQTT broker in background thread."""
        retry_count = 0
        while True:
            try:
                if retry_count == 0:
                    logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
                else:
                    logger.debug(f"Connection retry {retry_count} to MQTT broker {self.broker}:{self.port}...")
                
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
                break
            except Exception as e:
                retry_count += 1
                if retry_count == 1:
                    logger.warning(f"Connection failed: {e}. Retrying...")
                else:
                    logger.debug(f"Connection retry {retry_count} failed: {e}")
                time.sleep(5)
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker as {self.client_id}")
            
            # Call connection callbacks
            for callback in self.connection_callbacks:
                callback(True)
        else:
            logger.error(f"Connection failed with code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker with code {rc}")
        
        # Call connection callbacks
        for callback in self.connection_callbacks:
            callback(False)
    
    def on_publish(self, client, userdata, mid):
        """Callback when message is published."""
        logger.debug(f"Message {mid} published successfully")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscribed to topic."""
        logger.debug(f"Subscribed with mid {mid}, QoS {granted_qos}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            logger.info(f"Received message on topic {topic}")
            
            # Call registered callback for this topic
            for pattern, callback in self.message_callbacks.items():
                if self._topic_matches(pattern, topic):
                    callback(topic, data)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if topic matches pattern (supports wildcards)."""
        if pattern == "#":
            return True
        if pattern.endswith("#"):
            base_pattern = pattern[:-1]
            return topic.startswith(base_pattern)
        if "+" in pattern:
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")
            if len(pattern_parts) != len(topic_parts):
                return False
            return all(p == "+" or p == t for p, t in zip(pattern_parts, topic_parts))
        return pattern == topic
    
    def publish(self, topic: str, data: dict, qos: int = 0, retain: bool = False) -> bool:
        """
        Publish data to MQTT topic.
        
        Args:
            topic: MQTT topic
            data: Data to publish (will be JSON serialized)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain message on broker
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected:
            logger.debug("Not connected to MQTT broker - will retry when connected")
            return False
        
        try:
            payload = json.dumps(data)
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to topic {topic}")
                return True
            else:
                logger.error(f"Failed to publish to topic {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def subscribe(self, topic: str, callback: Callable, qos: int = 0) -> bool:
        """
        Subscribe to MQTT topic with callback.
        
        Args:
            topic: MQTT topic (supports wildcards + and #)
            callback: Function to call when message received
            qos: Quality of Service
            
        Returns:
            True if subscribed successfully, False otherwise
        """
        if not self.connected:
            logger.debug(f"Not connected to MQTT broker - will subscribe when connected: {topic}")
            return False
        
        try:
            result = self.client.subscribe(topic, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.message_callbacks[topic] = callback
                logger.info(f"Subscribed to topic {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to topic {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from topic."""
        if not self.connected:
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.message_callbacks:
                    del self.message_callbacks[topic]
                logger.info(f"Unsubscribed from topic {topic}")
                return True
            else:
                logger.error(f"Failed to unsubscribe from topic {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            return False
    
    def add_connection_callback(self, callback: Callable):
        """Add callback for connection status changes."""
        self.connection_callbacks.append(callback)
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self.connected


# Example usage and testing
if __name__ == "__main__":
    # Create MQTT client
    mqtt_client = MQTTClient(
        broker="network.saark.in",
        port=1884,
        client_id="test_client"
    )
    
    # Wait for connection
    time.sleep(3)
    
    # Test publishing
    if mqtt_client.is_connected():
        print("Testing publish...")
        mqtt_client.publish("test/topic", {"message": "Hello from MQTT client"})
        
        # Test subscription
        def message_callback(topic, data):
            print(f"Received on {topic}: {data}")
        
        mqtt_client.subscribe("test/#", message_callback)
        
        # Keep running for testing
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            mqtt_client.disconnect()
    else:
        print("Failed to connect to MQTT broker")