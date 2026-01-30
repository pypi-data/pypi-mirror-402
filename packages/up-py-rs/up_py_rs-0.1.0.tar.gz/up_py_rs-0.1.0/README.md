# up-py-rs

[![CI Status](https://github.com/sachinkum0009/up-py/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/sachinkum0009/up-py-rs/actions)
[![PyPI version](https://img.shields.io/pypi/v/up-py-rs.svg)](https://pypi.org/project/up-py-rs/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Python bindings for the [Eclipse uProtocol](https://github.com/eclipse-uprotocol/up-spec) Rust implementation ([up-rust](https://github.com/eclipse-uprotocol/up-rust)). This package provides high-performance Python APIs for uProtocol communication patterns by leveraging Rust's speed and safety.

## Features

- 🚀 **High Performance**: Rust-powered implementations with minimal Python overhead
- 🔒 **Type Safe**: Full type hints and stub files for excellent IDE support
- 📡 **Complete uProtocol Support**: Publishers, Notifiers, and Transport implementations
- 🐍 **Pythonic API**: Easy-to-use interfaces that feel natural in Python
- ⚡ **Async Ready**: Built on Tokio async runtime for efficient I/O operations

## Installation

Install from PyPI:

```bash
# Basic installation (includes LocalTransport and core features)
pip install up-py-rs

# With Zenoh network transport
pip install up-py-rs[zenoh]

# With all optional features
pip install up-py-rs[all]
```

Or using uv:

```bash
uv add up-py-rs
# or with extras
uv add up-py-rs --extra zenoh
```

### Optional Dependencies

up-py-rs supports modular installation through extras:

| Extra | Description | Install Command |
|-------|-------------|-----------------|
| `zenoh` | Zenoh network transport | `pip install up-py-rs[zenoh]` |
| `discovery` | Service discovery support | `pip install up-py-rs[discovery]` |
| `subscription` | Advanced subscription management | `pip install up-py-rs[subscription]` |
| `twin` | Digital twin support | `pip install up-py-rs[twin]` |
| `cloudevents` | CloudEvents format support | `pip install up-py-rs[cloudevents]` |
| `all` | All optional features | `pip install up-py-rs[all]` |
| `test` | Testing utilities | `pip install up-py-rs[test]` |

**Note**: Currently all Rust features are included in the wheel. Extras are provided for documentation and future Python runtime dependencies.

## Quick Start

### Simple Publisher (Local Transport)

For in-process communication without network overhead:

```python
from up_py_rs import StaticUriProvider
from up_py_rs.local_transport import LocalTransport
from up_py_rs.communication import SimplePublisher, UPayload

# Setup
uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
transport = LocalTransport()
publisher = SimplePublisher(transport, uri_provider)

# Publish a message
payload = UPayload.from_string("Hello from Python!")
publisher.publish(0xb4c1, payload)
```

### Zenoh Publisher (Network Transport)

For distributed communication across network boundaries:

```python
from up_py_rs import StaticUriProvider
from up_py_rs.zenoh_transport import UPTransportZenoh
from up_py_rs.communication import SimplePublisher, UPayload

# Setup Zenoh transport
uri_provider = StaticUriProvider("publisher", 0x3b1da, 1)
transport = UPTransportZenoh.builder("publisher").build()
publisher = SimplePublisher(transport, uri_provider)

# Publish messages
for i in range(1, 11):
    payload = UPayload.from_string(f"event {i}")
    publisher.publish(0x8001, payload)
```

**Note**: Requires `pip install up-py-rs[zenoh]`

### Simple Notifier

```python
from up_py_rs import StaticUriProvider
from up_py_rs.local_transport import LocalTransport
from up_py_rs.communication import SimpleNotifier, UPayload

def notification_handler(msg):
    text = msg.extract_string()
    if text:
        print(f"Received: {text}")

# Setup
uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
transport = LocalTransport()
notifier = SimpleNotifier(transport, uri_provider)

# Register listener
topic = uri_provider.get_resource_uri(0xd100)
notifier.start_listening(topic, notification_handler)

# Send notification
payload = UPayload.from_string("Alert!")
destination = uri_provider.get_source_uri()
notifier.notify(0xd100, destination, payload)

# Cleanup
notifier.stop_listening(topic, notification_handler)
```

## Components

### LocalTransport
In-process message transport for testing and local communication without network overhead. Best for single-process applications and testing.

### UPTransportZenoh
Zenoh-based network transport for distributed communication across network boundaries. Enables pub/sub patterns between different processes, devices, or vehicles. Requires `zenoh` extra.

### StaticUriProvider
Creates and manages uProtocol URIs for identifying entities in the network.

### SimplePublisher
High-level API for publishing messages to specific resources. Works with any transport (Local or Zenoh).

### SimpleNotifier
Send and receive notifications between uEntities with listener callbacks.

### UPayload
Message payload wrapper supporting strings and raw bytes with protobuf format.

## Development

### Building from Source

Requirements:
- Python 3.8+
- Rust toolchain (for building)
- uv or pip

```bash
# Clone the repository
git clone https://github.com/sachinkum0009/up-py-rs.git
cd up-py-rs

# Build in development mode
uv run maturin develop

# Run tests
uv run pytest

# Run examples
uv run python examples/simple_publish.py
uv run python examples/simple_notify.py

# Run Zenoh examples (requires zenoh extra)
uv add up-py-rs --extra zenoh

# Terminal 1: Start subscriber
uv run python examples/simple_zenoh_subscriber.py

# Terminal 2: Start publisher
uv run python examples/simple_zenoh_publisher.py
```

### Building Wheels

```bash
# Build release wheel
uv run maturin build --release

# Build and publish to PyPI
uv run maturin publish
```

## Architecture

up-py-rs bridges Python and Rust using [PyO3](https://pyo3.rs/):

- **Rust Core**: High-performance implementations from [up-rust](https://github.com/eclipse-uprotocol/up-rust)
- **PyO3 Bindings**: Zero-cost abstractions between Python and Rust
- **Python API**: Pythonic interfaces with full type hints

Each async operation maintains its own Tokio runtime for thread-safe execution across the Python/Rust boundary.

## Contributing

Contributions are welcome! Please see the [contribution guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links

- [Eclipse uProtocol Specification](https://github.com/eclipse-uprotocol/up-spec)
- [up-rust (Rust Implementation)](https://github.com/eclipse-uprotocol/up-rust)
- [PyO3 Documentation](https://pyo3.rs/)
- [Issue Tracker](https://github.com/sachinkum0009/up-py-rs/issues)

## Acknowledgments

Built with:
- [Eclipse uProtocol](https://github.com/eclipse-uprotocol) - The underlying protocol specification
- [PyO3](https://pyo3.rs/) - Rust bindings for Python
- [Maturin](https://www.maturin.rs/) - Build tool for Rust/Python projects
