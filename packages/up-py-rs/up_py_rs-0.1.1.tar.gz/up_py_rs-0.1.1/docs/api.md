# API Reference

Complete API reference for `up-py-rs`.

## Module: `up_py_rs`

### StaticUriProvider

```python
class StaticUriProvider:
    def __init__(self, authority: str, entity_id: int, version: int) -> None
```

Provides URI information for uProtocol entities.

StaticUriProvider creates and manages URIs for identifying entities in the uProtocol network. It combines an authority (device/vehicle name), entity ID, and version to create unique identifiers.

**Parameters:**

- `authority` (str): The authority name identifying the device/vehicle (e.g., "my-vehicle", "sensor-001")
- `entity_id` (int): The entity ID (0 to 2^32-1, typically written in hex like 0xa34b)
- `version` (int): The version number (0 to 255, e.g., 0x01)

**Example:**

```python
from up_py_rs import StaticUriProvider

provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
```

---

### UMessage

```python
class UMessage:
    def extract_string(self) -> Optional[str]
```

Represents a complete uProtocol message.

UMessage encapsulates both the payload and metadata for a uProtocol communication. It is typically received by listener callbacks.

**Methods:**

#### extract_string()

Extract string value from the message payload.

**Returns:** `Optional[str]` - The extracted string if successful, None if the message doesn't contain a string value

**Example:**

```python
def handler(msg):
    text = msg.extract_string()
    if text:
        print(f"Received: {text}")
```

---

## Module: `up_py_rs.communication`

### UPayload

```python
class UPayload:
    @staticmethod
    def from_string(value: str) -> UPayload
    
    @staticmethod
    def from_bytes(data: list[int]) -> UPayload
```

Represents a message payload in uProtocol.

UPayload encapsulates the data being transmitted in a uProtocol message. It can be created from strings or raw bytes.

**Static Methods:**

#### from_string(value: str) -> UPayload

Create a UPayload from a string value.

**Parameters:**

- `value` (str): The string content to wrap in the payload

**Returns:** `UPayload` - A new payload instance containing the string

**Raises:** `Exception` - If the payload creation fails

**Example:**

```python
from up_py_rs.communication import UPayload

payload = UPayload.from_string("Hello, World!")
```

#### from_bytes(data: list[int]) -> UPayload

Create a UPayload from raw bytes.

**Parameters:**

- `data` (list[int]): A list of bytes (0-255) to wrap in the payload

**Returns:** `UPayload` - A new payload instance containing the binary data

**Example:**

```python
from up_py_rs.communication import UPayload

payload = UPayload.from_bytes([72, 101, 108, 108, 111])  # "Hello"
```

---

### SimplePublisher

```python
class SimplePublisher:
    def __init__(self, transport: LocalTransport, uri_provider: StaticUriProvider) -> None
    def publish(self, resource_id: int, payload: Optional[UPayload]) -> None
```

Publisher for sending uProtocol messages.

SimplePublisher provides an easy-to-use interface for publishing messages to specific resources in the uProtocol network.

**Constructor:**

#### \_\_init\_\_(transport: LocalTransport, uri_provider: StaticUriProvider)

Create a new SimplePublisher.

**Parameters:**

- `transport` (LocalTransport): The transport to use for sending messages
- `uri_provider` (StaticUriProvider): The URI provider for the publishing entity

**Raises:** `Exception` - If the runtime creation fails

**Example:**

```python
from up_py_rs.communication import SimplePublisher
from up_py_rs.local_transport import LocalTransport
from up_py_rs import StaticUriProvider

transport = LocalTransport()
provider = StaticUriProvider("device", 0x1234, 0x01)
publisher = SimplePublisher(transport, provider)
```

**Methods:**

#### publish(resource_id: int, payload: Optional[UPayload]) -> None

Publish a message to a specific resource.

**Parameters:**

- `resource_id` (int): The target resource ID (0 to 65535, typically in hex like 0xb4c1)
- `payload` (Optional[UPayload]): The message payload, or None for empty messages

**Raises:** `Exception` - If publishing fails

**Example:**

```python
from up_py_rs.communication import UPayload

# Publish with string payload
payload = UPayload.from_string("Hello")
publisher.publish(0xb4c1, payload)

# Publish without payload
publisher.publish(0xb4c1, None)
```

---

## Module: `up_py_rs.local_transport`

### LocalTransport

```python
class LocalTransport:
    def __init__(self) -> None
    def register_listener(
        self,
        uri_provider: StaticUriProvider,
        resource_id: int,
        callback: Callable[[UMessage], None]
    ) -> None
    def unregister_listener(
        self,
        uri_provider: StaticUriProvider,
        resource_id: int,
        callback: Callable[[UMessage], None]
    ) -> None
```

Provides local (in-process) transport for uProtocol communication.

LocalTransport enables communication between components within the same process without network overhead. It manages listener registration and message routing.

**Constructor:**

#### \_\_init\_\_()

Create a new LocalTransport instance.

**Raises:** `Exception` - If the runtime creation fails

**Example:**

```python
from up_py_rs.local_transport import LocalTransport

transport = LocalTransport()
```

**Methods:**

#### register_listener(uri_provider: StaticUriProvider, resource_id: int, callback: Callable[[UMessage], None]) -> None

Register a listener callback for a specific resource.

**Parameters:**

- `uri_provider` (StaticUriProvider): The URI provider identifying the entity
- `resource_id` (int): The resource ID to listen to (0 to 65535)
- `callback` (Callable[[UMessage], None]): A Python function that accepts a UMessage parameter. Will be called when messages arrive

**Raises:** `Exception` - If registration fails

**Example:**

```python
from up_py_rs import UMessage

def my_handler(msg: UMessage):
    text = msg.extract_string()
    if text:
        print(text)

transport.register_listener(uri_provider, 0xb4c1, my_handler)
```

#### unregister_listener(uri_provider: StaticUriProvider, resource_id: int, callback: Callable[[UMessage], None]) -> None

Unregister a previously registered listener.

**Parameters:**

- `uri_provider` (StaticUriProvider): The URI provider used during registration
- `resource_id` (int): The resource ID to stop listening to
- `callback` (Callable[[UMessage], None]): The same Python function that was registered

**Raises:** `Exception` - If unregistration fails or listener not found

**Note:** Currently may fail due to listener instance comparison issues. Consider letting listeners be cleaned up automatically.

**Example:**

```python
# Unregister the listener
transport.unregister_listener(uri_provider, 0xb4c1, my_handler)
```

---

## Type Aliases and Constants

### Common Types

- **Authority**: `str` - Device/vehicle identifier
- **Entity ID**: `int` - Range: 0 to 2^32-1 (4294967295)
- **Version**: `int` - Range: 0 to 255
- **Resource ID**: `int` - Range: 0 to 65535 (0xFFFF)

### Typical Hex Values

Resource IDs and Entity IDs are often expressed in hexadecimal:

```python
ENTITY_ID = 0xa34b      # 41803 in decimal
RESOURCE_ID = 0xb4c1    # 46273 in decimal
VERSION = 0x01          # 1 in decimal
```

---

## Error Handling

All classes and methods may raise `Exception` on failure. Always wrap critical operations in try-except blocks:

```python
try:
    transport = LocalTransport()
    uri_provider = StaticUriProvider("device", 0x1234, 0x01)
    transport.register_listener(uri_provider, 0xb4c1, handler)
    
    publisher = SimplePublisher(transport, uri_provider)
    payload = UPayload.from_string("test")
    publisher.publish(0xb4c1, payload)
except Exception as e:
    print(f"Error: {e}")
```

---

## Version Information

Access the package version:

```python
import up_py_rs

print(up_py_rs.__version__)
```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete API usage example"""

from up_py_rs import StaticUriProvider, UMessage
from up_py_rs.communication import SimplePublisher, UPayload
from up_py_rs.local_transport import LocalTransport

# Constants
AUTHORITY = "my-vehicle"
ENTITY_ID = 0xa34b
VERSION = 0x01
RESOURCE_ID = 0xb4c1

def message_handler(msg: UMessage) -> None:
    """Callback for received messages"""
    text = msg.extract_string()
    if text:
        print(f"Received: {text}")

def main():
    try:
        # Create components
        uri_provider = StaticUriProvider(AUTHORITY, ENTITY_ID, VERSION)
        transport = LocalTransport()
        
        # Register listener
        transport.register_listener(uri_provider, RESOURCE_ID, message_handler)
        
        # Create publisher and publish
        publisher = SimplePublisher(transport, uri_provider)
        payload = UPayload.from_string("Hello, uProtocol!")
        publisher.publish(RESOURCE_ID, payload)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

---

## See Also

- [Installation Guide](installation.md)
- [Usage Guide](usage.md)
- [uProtocol Specification](https://github.com/eclipse-uprotocol)
