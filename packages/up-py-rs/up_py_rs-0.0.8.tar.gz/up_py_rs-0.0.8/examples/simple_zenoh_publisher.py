#!/usr/bin/env python3
"""
Python example demonstrating Zenoh transport for up-py-rs.

This example mirrors the functionality of the Rust publisher example from
up-transport-zenoh-rust repository:
- Creates a UPTransportZenoh for network communication
- Uses StaticUriProvider to create resource URIs
- Publishes messages in a loop to demonstrate network transport

Unlike simple_publish.py which uses LocalTransport (in-process only),
this example uses Zenoh to enable communication across network boundaries.

Requirements:
    Install with: pip install up-py-rs[zenoh]
"""

import time
from up_py_rs.communication import SimplePublisher, UPayload
from up_py_rs import StaticUriProvider

try:
    from up_py_rs.zenoh_transport import UPTransportZenoh
except ImportError:
    print("Error: Zenoh transport not available.")
    print("Please install with: pip install up-py-rs[zenoh]")
    exit(1)


# Constants
PUBLISHER_RESOURCE_ID = 0x8001  # Topic resource ID (matching Rust example)
PUBLISHER_ENTITY_ID = 0x3b1da    # Entity ID for publisher
PUBLISHER_VERSION = 1            # Version


def main():
    """Main function demonstrating Zenoh publisher."""
    
    print("uProtocol Zenoh publisher example")
    
    # Create URI provider for this publisher
    uri_provider = StaticUriProvider("publisher", PUBLISHER_ENTITY_ID, PUBLISHER_VERSION)
    
    # Create Zenoh transport
    print("Building Zenoh transport...")
    transport = UPTransportZenoh.builder(uri_provider.get_authority()).build()
    print("Zenoh transport created successfully")
    
    # Create publisher
    publisher = SimplePublisher(transport, uri_provider)
    
    # Publish messages in a loop
    print(f"\nPublishing to resource ID: 0x{PUBLISHER_RESOURCE_ID:x}")
    print("Press Ctrl+C to stop\n")
    
    try:
        for cnt in range(1, 101):  # Publish 100 messages
            data = f"event {cnt}"
            
            # Get topic URI
            topic_uri = uri_provider.get_resource_uri(PUBLISHER_RESOURCE_ID)
            
            print(f"Publishing message [topic: {topic_uri.to_uri()}, payload: {data}]")
            
            # Create payload and publish
            payload = UPayload.from_string(data)
            publisher.publish(PUBLISHER_RESOURCE_ID, payload)
            
            # Wait 1 second between messages
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping publisher...")
    
    print("Done!")


if __name__ == "__main__":
    main()
