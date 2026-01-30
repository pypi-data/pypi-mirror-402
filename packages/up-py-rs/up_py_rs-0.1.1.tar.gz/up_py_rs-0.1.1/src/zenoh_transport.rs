//! Zenoh Transport implementation for Python bindings
//!
//! This module provides Python bindings for the up-transport-zenoh-rust implementation,
//! allowing Python applications to use Zenoh as a network transport for uProtocol.

use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use std::sync::Arc;
use tokio::runtime::Runtime;
use up_rust::{UListener, UMessage, UStatus, UTransport, UUri};
use up_transport_zenoh::{zenoh_config, UPTransportZenoh as RustUPTransportZenoh};

/// Python wrapper for the Rust UPTransportZenoh
///
/// Provides network transport capabilities using the Zenoh protocol.
/// Unlike LocalTransport which only works within a single process,
/// UPTransportZenoh enables communication across network boundaries.
#[pyclass(name = "UPTransportZenoh")]
pub struct UPTransportZenoh {
    pub(crate) transport: Arc<RustUPTransportZenoh>,
    runtime: Runtime,
}

#[pymethods]
impl UPTransportZenoh {
    /// Create a new builder for UPTransportZenoh
    ///
    /// Args:
    ///     authority: The authority name (e.g., "my-vehicle", "device-123")
    ///
    /// Returns:
    ///     UPTransportZenohBuilder: A builder instance to configure the transport
    ///
    /// Example:
    ///     ```python
    ///     builder = UPTransportZenoh.builder("my-vehicle")
    ///     transport = builder.build()
    ///     ```
    #[staticmethod]
    fn builder(authority: &str) -> PyResult<UPTransportZenohBuilder> {
        Ok(UPTransportZenohBuilder {
            authority: authority.to_string(),
            runtime: Runtime::new()
                .map_err(|e| PyException::new_err(format!("Failed to create runtime: {e}")))?,
        })
    }

    /// Send a UMessage via Zenoh transport
    ///
    /// Args:
    ///     message: The UMessage to send
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     Exception: If sending fails
    ///
    /// Example:
    ///     ```python
    ///     transport.send(message)
    ///     ```
    fn send(&self, message: crate::local_transport::UMessage) -> PyResult<()> {
        let rust_message = message.inner.clone();
        let transport = self.transport.clone();
        
        self.runtime
            .block_on(async move { transport.as_ref().send(rust_message).await })
            .map_err(|e| PyException::new_err(format!("Failed to send message: {e}")))
    }

    /// Register a listener for messages matching the source filter
    ///
    /// Args:
    ///     source_filter: The URI to listen for messages from
    ///     listener: Python callable that receives UMessage objects
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     Exception: If registration fails
    ///
    /// Example:
    ///     ```python
    ///     def handle_message(msg):
    ///         print(f"Received: {msg.extract_string()}")
    ///     
    ///     transport.register_listener(source_uri, handle_message)
    ///     ```
    fn register_listener(
        &self,
        source_filter: crate::local_transport::UUri,
        listener: PyObject,
    ) -> PyResult<()> {
        let rust_listener = Arc::new(PythonListener::new(listener));
        let transport = self.transport.clone();
        let rust_uri = source_filter.inner.clone();

        self.runtime
            .block_on(async move {
                transport
                    .as_ref()
                    .register_listener(&rust_uri, None, rust_listener)
                    .await
            })
            .map_err(|e| PyException::new_err(format!("Failed to register listener: {e}")))
    }

    /// Unregister a listener for the given source filter
    ///
    /// Args:
    ///     source_filter: The URI to stop listening to
    ///     listener: The Python callable that was registered
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     Exception: If unregistration fails
    ///
    /// Note:
    ///     Due to listener instance comparison issues, this may not work as expected.
    ///     Consider letting listeners be cleaned up automatically.
    ///
    /// Example:
    ///     ```python
    ///     transport.unregister_listener(source_uri, handle_message)
    ///     ```
    fn unregister_listener(
        &self,
        source_filter: crate::local_transport::UUri,
        listener: PyObject,
    ) -> PyResult<()> {
        let rust_listener = Arc::new(PythonListener::new(listener));
        let transport = self.transport.clone();
        let rust_uri = source_filter.inner.clone();

        self.runtime
            .block_on(async move {
                transport
                    .as_ref()
                    .unregister_listener(&rust_uri, None, rust_listener)
                    .await
            })
            .map_err(|e| PyException::new_err(format!("Failed to unregister listener: {e}")))
    }
}

/// Builder for UPTransportZenoh
///
/// Provides a fluent API for configuring and creating a Zenoh transport instance.
#[pyclass(name = "UPTransportZenohBuilder")]
pub struct UPTransportZenohBuilder {
    authority: String,
    runtime: Runtime,
}

#[pymethods]
impl UPTransportZenohBuilder {
    /// Build the UPTransportZenoh instance
    ///
    /// Returns:
    ///     UPTransportZenoh: The configured transport instance
    ///
    /// Raises:
    ///     Exception: If building fails
    ///
    /// Example:
    ///     ```python
    ///     transport = UPTransportZenoh.builder("my-vehicle").build()
    ///     ```
    fn build(mut slf: PyRefMut<Self>) -> PyResult<UPTransportZenoh> {
        let authority = slf.authority.clone();
        
        let transport = slf.runtime.block_on(async move {
            RustUPTransportZenoh::builder(&authority)
                .map_err(|e| format!("Failed to create builder: {e}"))?
                .with_config(zenoh_config::Config::default())
                .build()
                .await
                .map_err(|e| format!("Failed to build transport: {e}"))
        }).map_err(|e: String| PyException::new_err(e))?;

        Ok(UPTransportZenoh {
            transport: Arc::new(transport),
            runtime: Runtime::new()
                .map_err(|e| PyException::new_err(format!("Failed to create runtime: {e}")))?,
        })
    }
}

/// Bridges Python callable to Rust UListener trait
struct PythonListener {
    callback: PyObject,
}

impl PythonListener {
    fn new(callback: PyObject) -> Self {
        Self { callback }
    }
}

#[async_trait::async_trait]
impl UListener for PythonListener {
    async fn on_receive(&self, msg: UMessage) {
        Python::with_gil(|py| {
            let py_msg = crate::local_transport::UMessage {
                inner: msg,
            };
            if let Err(e) = self.callback.call1(py, (py_msg,)) {
                eprintln!("Error calling Python listener: {:?}", e);
            }
        });
    }
}
