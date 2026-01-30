#!/usr/bin/env python3
"""
Simple Zenoh Subscriber Example

This example demonstrates how to receive messages using the Zenoh transport.
It mirrors the publisher example and will receive messages sent over the
Zenoh network.

This example shows:
1. Creating a Zenoh transport with default configuration
2. Creating a URI provider for the subscribing entity
3. Registering a listener to receive messages
4. Handling incoming messages
"""

import time
from up_py_rs import StaticUriProvider
from up_py_rs.zenoh_transport import UPTransportZenoh

def message_handler(msg):
    """Callback function to handle received messages."""
    text = msg.extract_string()
    if text:
        print(f"   📥 Received: {text}")
    else:
        print("   📥 Received message (non-string payload)")

def main():
    print("uProtocol Zenoh Subscriber Example")
    print("=" * 60)
    
    # Create Zenoh transport
    print("\n1. Building Zenoh transport...")
    transport = UPTransportZenoh.builder("my-vehicle").build()
    print("   ✓ Zenoh transport created")
    
    # Create URI provider (must match publisher's)
    print("\n2. Creating URI provider...")
    authority = "my-vehicle"
    entity_id = 0xa34b  # Must match publisher
    version = 0x01
    uri_provider = StaticUriProvider(authority, entity_id, version)
    print(f"   ✓ URI provider created: {authority}/{hex(entity_id)}/{hex(version)}")
    
    # Register listener for the same resource ID as publisher
    print("\n3. Registering listener...")
    resource_id = 0x8001
    transport.register_listener(uri_provider.get_resource_uri(resource_id), message_handler)
    print(f"   ✓ Listener registered for resource ID: {hex(resource_id)}")
    
    print("\n4. Waiting for messages...")
    print("   (Press Ctrl+C to stop)\n")
    
    # Keep running to receive messages
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n✓ Subscriber stopped")
        print("=" * 60)

if __name__ == "__main__":
    main()
