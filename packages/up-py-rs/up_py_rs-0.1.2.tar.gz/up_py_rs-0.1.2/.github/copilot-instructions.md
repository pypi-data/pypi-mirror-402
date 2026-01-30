# Up Py Rs

## Project Overview

Up Py Rs is a Python package that provides Python bindings for the Eclipse uProtocol Rust implementation (`up-rust`). It enables Python developers to leverage high-performance Rust implementations of uProtocol communication patterns while maintaining a Pythonic API.

**Tech Stack:**
- Rust (Rust Edition 2024)
- Python 3.8+
- PyO3 (0.20.2) - Rust bindings for Python
- Maturin - Build tool for Rust/Python projects
- Tokio - Async runtime for Rust
- up-rust (0.9.0) - Core uProtocol implementation

## Architecture

### Module Structure

The project bridges Rust and Python through the following structure:

#### Rust Source Files (`src/`)
- **`lib.rs`**: Main module entry point, sets up PyO3 bindings and exports submodules
- **`communication.rs`**: Implements `SimplePublisher`, `SimpleNotifier`, and `UPayload` classes
- **`local_transport.rs`**: Implements `LocalTransport`, `StaticUriProvider`, `UMessage`, and `UUri` classes
- **`ustatus.rs`**: Status and error handling types
- **`uri.rs`**: URI-related functionality (currently empty, planned)
- **`core.rs`**: Core types (currently empty, planned)
- **`utransport.rs`**: Transport trait implementations (currently empty, planned)

#### Python Package (`up_py_rs/`)
- **`__init__.py` & `__init__.pyi`**: Main package exports (`StaticUriProvider`, `UMessage`, `UUri`)
- **`communication.py` & `communication.pyi`**: Re-exports `SimplePublisher`, `SimpleNotifier`, `UPayload`
- **`local_transport.py` & `local_transport.pyi`**: Re-exports `LocalTransport`

### Key Design Patterns

1. **Bridge Pattern**: Python classes wrap Rust implementations using PyO3
2. **Runtime Management**: Each class that performs async operations maintains its own Tokio runtime
3. **Thread Safety**: Uses `Arc<T>` for sharing Rust types across Python/Rust boundary
4. **Callback Bridge**: `PythonListener` struct bridges Python callbacks to Rust's `UListener` trait

## Core Components

### 1. LocalTransport
- Provides in-process message transport without network overhead
- Manages listener registration and message routing
- Thread-safe, uses `Arc<RustLocalTransport>`
- Methods: `register_listener()`, `unregister_listener()`

### 2. StaticUriProvider
- Creates and manages uProtocol URIs for entities
- Combines authority (device/vehicle name), entity ID, and version
- URI format: `authority/entity_id/version/resource_id`
- Methods: `get_resource_uri(resource_id: int) -> UUri`

### 3. SimplePublisher
- Publishes messages to specific resources in the uProtocol network
- Uses `CallOptions::for_publish()` for message configuration
- Blocks on async operations using owned Tokio runtime
- Methods: `publish(resource_id: int, payload: Optional[UPayload])`

### 4. SimpleNotifier
- Sends and receives notifications between uEntities
- Currently under development (methods stubbed)
- Methods: `start_listening(topic: str)`, `stop_listening(topic: str)`

### 5. UPayload
- Encapsulates message data (strings or raw bytes)
- Supports protobuf wrapped format
- Static constructors: `from_string(value: str)`, `from_bytes(data: list[int])`

### 6. UMessage
- Complete uProtocol message with payload and metadata
- Received by listener callbacks
- Methods: `extract_string() -> Optional[str]`

### 7. UUri
- Represents a uProtocol URI
- Currently minimal implementation, planned for expansion

## Development Guidelines

### Code Style

**Rust Code:**
- Follow Rust 2024 edition conventions
- Use comprehensive doc comments with `///`
- Include Args, Returns, Raises, and Example sections in docstrings
- Wrap Rust errors using `PyException::new_err()` with descriptive messages
- Use `#[pyclass]` and `#[pymethods]` for Python-exposed types

**Python Code:**
- Use `.pyi` stub files for type hints
- Keep `.py` files minimal (re-exports only)
- Follow PEP 484 type hints
- Document all public APIs

### Error Handling
- Convert all Rust `Result<T, E>` types to `PyResult<T>`
- Provide context in error messages: `format!("Failed to {action}: {error}")`
- Use `.map_err()` to convert Rust errors to Python exceptions

### Testing
- Place tests in `tests/` directory
- Use pytest for Python testing
- Test both success and failure paths
- Example tests: `test_simple_publisher.py`

### Building and Development

**Build Commands:**
```bash
# Development build (creates extension in-place)
uv run maturin develop

# Production build
uv run maturin build --release

# Build wheels
uv run maturin build --release --out target/wheels
```

**Project Configuration:**
- `pyproject.toml`: Python package metadata, uses Maturin build backend
- `Cargo.toml`: Rust crate configuration, cdylib for Python extension
- `mkdocs.yml`: Documentation configuration

## Common Patterns

### Creating a Publisher
```python
from up_py_rs import StaticUriProvider
from up_py_rs.local_transport import LocalTransport
from up_py_rs.communication import SimplePublisher, UPayload

uri_provider = StaticUriProvider("my-vehicle", 0xa34b, 0x01)
transport = LocalTransport()
publisher = SimplePublisher(transport, uri_provider)

payload = UPayload.from_string("Hello")
publisher.publish(0xb4c1, payload)
```

### Registering a Listener
```python
def message_handler(msg):
    text = msg.extract_string()
    if text:
        print(f"Received: {text}")

transport.register_listener(uri_provider, 0xb4c1, message_handler)
```

### Resource ID Convention
- Use hexadecimal notation: `0xb4c1`, `0xa34b`, `0xd100`
- Resource IDs are 16-bit (0 to 65535)
- Entity IDs are 32-bit
- Versions are 8-bit (0 to 255)

## Current Development Status

### Implemented
- ✅ LocalTransport with listener registration
- ✅ SimplePublisher for message publishing
- ✅ UPayload (string and bytes)
- ✅ StaticUriProvider
- ✅ UMessage with string extraction
- ✅ Basic type stubs (.pyi files)

### In Progress
- 🚧 SimpleNotifier (methods stubbed, implementation needed)
- 🚧 Complete listener lifecycle management
- 🚧 Additional payload extraction methods (protobuf types)

### Planned
- 📋 `uri.rs` - Full URI manipulation utilities
- 📋 `core.rs` - Core uProtocol types
- 📋 `utransport.rs` - Additional transport implementations
- 📋 `UStatus` exposure to Python
- 📋 More comprehensive error types
- 📋 Async/await support in Python (currently blocks on async Rust)

## Known Issues and Limitations

1. **Listener Unregistration**: May fail due to `Arc<PythonListener>` instance comparison issues. Consider automatic cleanup instead.
2. **Async Operations**: Currently blocks on Rust async operations using `runtime.block_on()`. Future versions may support Python async/await.
3. **Error Details**: Some Rust error context may be lost in conversion to Python exceptions.
4. **SimpleNotifier**: Methods are stubs and don't perform actual operations yet.

## Dependencies

**Rust:**
- `up-rust` 0.9.0 (with multiple feature flags)
- `pyo3` 0.20.2 (with abi3-py38, abi3-py312, extension-module)
- `pyo3-asyncio` 0.20.0 (tokio-runtime)
- `tokio` 1.49.0 (full features)
- `async-trait` 0.1.89
- `protobuf` 3.7.2

**Python:**
- Python >= 3.8
- `maturin` >= 1.11.5 (build/dev dependency)
- `pytest` >= 8.3.5 (dev dependency)

## Contributing

When adding new features:
1. Implement in Rust source files with full documentation
2. Export through `lib.rs` pymodule
3. Add Python stub types in `.pyi` files
4. Create re-export wrappers in `.py` files
5. Add examples in `examples/`
6. Update tests in `tests/`
7. Ensure `maturin develop` builds successfully

## Resources

- [Eclipse uProtocol Specification](https://github.com/eclipse-uprotocol/up-spec)
- [up-rust Documentation](https://github.com/eclipse-uprotocol/up-rust)
- [PyO3 Documentation](https://pyo3.rs/)
- [Maturin Documentation](https://www.maturin.rs/) 