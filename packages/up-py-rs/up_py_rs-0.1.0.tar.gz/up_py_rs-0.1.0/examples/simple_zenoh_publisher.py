#!/usr/bin/env python3
"""
Simple Zenoh Publisher Example

This example demonstrates how to create a publisher using the Zenoh transport.
The Zenoh transport enables network communication, allowing messages to be
sent across process and machine boundaries.

This example shows:
1. Creating a Zenoh transport with default configuration
2. Creating a URI provider for the publishing entity
3. Creating a publisher that works with Zenoh transport
4. Publishing messages over the network using Zenoh protocol
"""

import time
from up_py_rs import StaticUriProvider
from up_py_rs.zenoh_transport import UPTransportZenoh
from up_py_rs.communication import SimplePublisher, UPayload

def main():
    print("uProtocol Zenoh Publisher Example")
    print("=" * 60)
    
    # Create Zenoh transport
    print("\n1. Building Zenoh transport...")
    transport = UPTransportZenoh.builder("my-vehicle").build()
    print("   ✓ Zenoh transport created")
    
    # Create URI provider for our entity
    print("\n2. Creating URI provider...")
    authority = "my-vehicle"
    entity_id = 0xa34b  # Example entity ID
    version = 0x01
    uri_provider = StaticUriProvider(authority, entity_id, version)
    print(f"   ✓ URI provider created: {authority}/{hex(entity_id)}/{hex(version)}")
    
    # Create SimplePublisher with Zenoh transport
    print("\n3. Creating publisher with Zenoh transport...")
    publisher = SimplePublisher(transport, uri_provider)
    print("   ✓ Publisher created successfully")
    
    # Publish messages
    print("\n4. Publishing messages...")
    resource_id = 0x8001
    
    # Publish 5 messages
    for i in range(5):
        message = f"Hello from Zenoh publisher! Message #{i+1}"
        payload = UPayload.from_string(message)
        
        print(f"   📤 Publishing: {message}")
        publisher.publish(resource_id, payload)
        
        time.sleep(1)  # Wait 1 second between messages
    
    print("\n✓ Successfully published 5 messages via Zenoh!")
    print("\nTo receive these messages, run:")
    print("  uv run python examples/simple_zenoh_subscriber.py")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
