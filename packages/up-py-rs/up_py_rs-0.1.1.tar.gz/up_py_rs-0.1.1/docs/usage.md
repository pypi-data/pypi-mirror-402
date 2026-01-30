# Usage Guide

This guide demonstrates how to use `up-py-rs` for uProtocol communication in Python.

## Quick Start

Here's a simple example that demonstrates publishing and receiving messages:

```python
from up_py_rs.communication import SimplePublisher, UPayload
from up_py_rs.local_transport import LocalTransport
from up_py_rs import StaticUriProvider

# Create URI provider
uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)

# Create local transport
transport = LocalTransport()

# Define a message handler
def message_handler(msg):
    text = msg.extract_string()
    if text:
        print(f"Received: {text}")

# Register listener
transport.register_listener(uri_provider, 0xb4c1, message_handler)

# Create publisher
publisher = SimplePublisher(transport, uri_provider)

# Publish a message
payload = UPayload.from_string("Hello, uProtocol!")
publisher.publish(0xb4c1, payload)
```

## Core Concepts

### StaticUriProvider

The `StaticUriProvider` creates and manages URIs for identifying entities in the uProtocol network:

```python
from up_py_rs import StaticUriProvider

# Parameters: authority, entity_id, version
uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
```

**Parameters:**
- `authority`: Device/vehicle identifier (string)
- `entity_id`: Entity ID, typically in hex format (0 to 2^32-1)
- `version`: Version number (0 to 255)

### LocalTransport

`LocalTransport` enables in-process communication without network overhead:

```python
from up_py_rs.local_transport import LocalTransport

transport = LocalTransport()
```

### Registering Listeners

Register a callback function to receive messages for a specific resource:

```python
def my_handler(msg):
    """Callback receives UMessage objects"""
    text = msg.extract_string()
    if text:
        print(f"Message: {text}")

# Register for resource ID 0xb4c1
transport.register_listener(uri_provider, 0xb4c1, my_handler)
```

**Important Notes:**
- The callback receives a `UMessage` object
- Use `msg.extract_string()` to get string payloads
- Resource IDs are typically 16-bit hex values (0 to 65535)

### Publishing Messages

Create a publisher and send messages:

```python
from up_py_rs.communication import SimplePublisher, UPayload

# Create publisher
publisher = SimplePublisher(transport, uri_provider)

# Create payload from string
payload = UPayload.from_string("Hello World")

# Publish to resource ID
publisher.publish(0xb4c1, payload)
```

### Creating Payloads

#### String Payload

```python
from up_py_rs.communication import UPayload

payload = UPayload.from_string("Hello from Python!")
```

#### Binary Payload

```python
# Create from list of bytes
data = [72, 101, 108, 108, 111]  # "Hello"
payload = UPayload.from_bytes(data)
```

#### Empty Payload

```python
# Publish without payload
publisher.publish(0xb4c1, None)
```

## Complete Example

Here's a complete working example:

```python
#!/usr/bin/env python3
"""
Complete example of up-py-rs usage
"""

from up_py_rs.communication import SimplePublisher, UPayload
from up_py_rs.local_transport import LocalTransport
from up_py_rs import StaticUriProvider

# Define constants
AUTHORITY = "my-vehicle"
ENTITY_ID = 0xa34b
VERSION = 0x01
RESOURCE_ID = 0xb4c1

def message_handler(msg):
    """Handle received messages"""
    text = msg.extract_string()
    if text:
        print(f"📨 Received: {text}")
    else:
        print("📨 Received message with no string content")

def main():
    # Initialize components
    print("🚀 Initializing uProtocol components...")
    uri_provider = StaticUriProvider(AUTHORITY, ENTITY_ID, VERSION)
    transport = LocalTransport()
    
    # Register listener
    print(f"👂 Registering listener for resource {hex(RESOURCE_ID)}...")
    transport.register_listener(uri_provider, RESOURCE_ID, message_handler)
    
    # Create publisher
    print("📢 Creating publisher...")
    publisher = SimplePublisher(transport, uri_provider)
    
    # Publish messages
    print("📤 Publishing messages...")
    
    # Message 1: String
    payload1 = UPayload.from_string("Hello from Python!")
    publisher.publish(RESOURCE_ID, payload1)
    
    # Message 2: Another string
    payload2 = UPayload.from_string("uProtocol rocks! 🎉")
    publisher.publish(RESOURCE_ID, payload2)
    
    # Message 3: Binary data
    binary_data = [0x48, 0x69, 0x21]  # "Hi!"
    payload3 = UPayload.from_bytes(binary_data)
    publisher.publish(RESOURCE_ID, payload3)
    
    print("✅ Done!")

if __name__ == "__main__":
    main()
```

## Best Practices

### Resource ID Management

Use constants for resource IDs to avoid magic numbers:

```python
# Good
TEMPERATURE_SENSOR = 0xb4c1
PRESSURE_SENSOR = 0xb4c2

publisher.publish(TEMPERATURE_SENSOR, payload)

# Avoid
publisher.publish(0xb4c1, payload)  # What is 0xb4c1?
```

### Error Handling

Wrap uProtocol operations in try-except blocks:

```python
try:
    transport = LocalTransport()
    transport.register_listener(uri_provider, resource_id, handler)
    publisher = SimplePublisher(transport, uri_provider)
    publisher.publish(resource_id, payload)
except Exception as e:
    print(f"Error: {e}")
```

### Callback Design

Keep listener callbacks lightweight and fast:

```python
def quick_handler(msg):
    """Quick, non-blocking handler"""
    text = msg.extract_string()
    if text:
        # Process quickly or queue for later
        queue.put(text)

# Avoid blocking operations in callbacks
def slow_handler(msg):
    """❌ Avoid: blocks the transport"""
    time.sleep(5)  # Bad: blocks message processing
    # ... slow processing
```

## Advanced Usage

### Multiple Listeners

You can register multiple listeners for different resources:

```python
def sensor_handler(msg):
    print(f"Sensor: {msg.extract_string()}")

def control_handler(msg):
    print(f"Control: {msg.extract_string()}")

# Register different handlers for different resources
transport.register_listener(uri_provider, 0xb4c1, sensor_handler)
transport.register_listener(uri_provider, 0xb4c2, control_handler)
```

### Multiple Authorities

Create different URI providers for different authorities:

```python
vehicle_provider = StaticUriProvider("vehicle-001", 0xa34b, 0x01)
cloud_provider = StaticUriProvider("cloud-service", 0xa34c, 0x01)

# Use different providers for different publishers
vehicle_publisher = SimplePublisher(transport, vehicle_provider)
cloud_publisher = SimplePublisher(transport, cloud_provider)
```

## Troubleshooting

### Messages Not Being Received

1. Ensure the listener is registered before publishing
2. Verify the resource ID matches
3. Check that the URI provider parameters match

### Import Errors

Make sure the package is installed:
```bash
pip install up-py-rs
```

### Type Errors

Use the correct types for parameters:
- Authority: string
- Entity ID: integer (0 to 2^32-1)
- Version: integer (0 to 255)
- Resource ID: integer (0 to 65535)

## Next Steps

- Check the [API Reference](api.md) for detailed API documentation
- See the [examples](https://github.com/sachinkum0009/up-py-rs/tree/main/examples) directory for more examples
- Read about [uProtocol](https://github.com/eclipse-uprotocol) to understand the underlying concepts
