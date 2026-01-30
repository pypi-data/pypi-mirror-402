#!/bin/bash
# Script to test Zenoh publisher and subscriber

echo "==================================================================="
echo "Zenoh Pub/Sub Test"
echo "==================================================================="

# Start subscriber in background
echo "Starting subscriber..."
uv run python examples/simple_zenoh_subscriber.py > subscriber.log 2>&1 &
SUB_PID=$!

echo "Subscriber PID: $SUB_PID"
echo "Waiting 3 seconds for subscriber to initialize..."
sleep 3

echo ""
echo "Running publisher..."
uv run python examples/simple_zenoh_publisher.py

echo ""
echo "Waiting 2 seconds for message delivery..."
sleep 2

echo ""
echo "Stopping subscriber..."
kill -INT $SUB_PID 2>/dev/null
wait $SUB_PID 2>/dev/null

echo ""
echo "==================================================================="
echo "Subscriber output:"
echo "==================================================================="
cat subscriber.log

rm -f subscriber.log

echo ""
echo "==================================================================="
echo "Test completed!"
echo "==================================================================="
