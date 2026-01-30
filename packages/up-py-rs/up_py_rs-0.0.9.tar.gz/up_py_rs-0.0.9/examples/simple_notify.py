"""
Simple Notify Example

This example demonstrates how to use SimpleNotifier to send and receive
notifications in uProtocol. It creates a notifier, registers a listener,
sends a notification to itself, and then cleans up.
"""

from up_py_rs.communication import SimpleNotifier, UPayload
from up_py_rs import StaticUriProvider
from up_py_rs.local_transport import LocalTransport


def console_printer(msg):
    """
    Callback function that prints received notification messages.
    
    Args:
        msg: The UMessage containing the notification payload.
    """
    text = msg.extract_string()
    if text:
        print(f"Received notification: {text}")


def main():
    ORIGIN_RESOURCE_ID = 0xd100
    
    uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
    
    transport = LocalTransport()
    
    notifier = SimpleNotifier(transport, uri_provider)
    
    topic = uri_provider.get_resource_uri(ORIGIN_RESOURCE_ID)
    
    print("Starting to listen for notifications...")
    notifier.start_listening(topic, console_printer)
    
    payload = UPayload.from_string("Hello from Python!")
    
    destination = uri_provider.get_source_uri()
    print("Sending notification...")
    notifier.notify(ORIGIN_RESOURCE_ID, destination, payload)
    
    # Stop listening (cleanup)
    print("Stopping listener...")
    notifier.stop_listening(topic, console_printer)
    
    print("Done!")


if __name__ == '__main__':
    main()
