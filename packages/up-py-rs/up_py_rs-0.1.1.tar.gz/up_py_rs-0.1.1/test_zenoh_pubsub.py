#!/usr/bin/env python3
"""
Test script to run publisher and subscriber simultaneously.
"""

import subprocess
import time
import sys

def main():
    print("Testing Zenoh Publisher/Subscriber Communication")
    print("=" * 70)
    
    # Start subscriber in background
    print("\n1. Starting subscriber...")
    subscriber = subprocess.Popen(
        ["uv", "run", "python", "examples/simple_zenoh_subscriber.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Wait for subscriber to initialize
    print("   Waiting for subscriber to initialize...")
    time.sleep(3)
    
    # Run publisher
    print("\n2. Running publisher...")
    publisher_result = subprocess.run(
        ["uv", "run", "python", "examples/simple_zenoh_publisher.py"],
        capture_output=True,
        text=True
    )
    
    print(publisher_result.stdout)
    
    if publisher_result.returncode != 0:
        print("Publisher error:", publisher_result.stderr, file=sys.stderr)
    
    # Wait a bit more for messages to be received
    print("\n3. Waiting for message delivery...")
    time.sleep(2)
    
    # Stop subscriber
    print("\n4. Stopping subscriber...")
    subscriber.terminate()
    subscriber_out, subscriber_err = subscriber.communicate(timeout=5)
    
    print("\nSubscriber output:")
    print("-" * 70)
    print(subscriber_out)
    if subscriber_err:
        print("Subscriber errors:", subscriber_err, file=sys.stderr)
    
    print("\n" + "=" * 70)
    print("Test completed!")

if __name__ == "__main__":
    main()
