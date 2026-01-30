use up_rust::UPayloadFormat;
use up_rust::communication::{
    CallOptions, Publisher, SimplePublisher as RustSimplePublisher, UPayload as RustUPayload,
    SimpleNotifier as RustSimpleNotifier, Notifier
};
use up_rust::{
    LocalUriProvider, StaticUriProvider as RustStaticUriProvider, UListener,
    UMessage as RustUMessage, UTransport, local_transport::LocalTransport as RustLocalTransport,
};

use protobuf::well_known_types::wrappers::StringValue;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use crate::local_transport::{LocalTransport, StaticUriProvider, UUri};

/// Represents a message payload in uProtocol.
///
/// UPayload encapsulates the data being transmitted in a uProtocol message.
/// It can be created from strings or raw bytes.
#[pyclass]
#[derive(Clone)]
pub struct UPayload {
    inner: RustUPayload,
}

#[pymethods]
impl UPayload {
    /// Create a UPayload from a string value.
    ///
    /// Args:
    ///     value (str): The string content to wrap in the payload.
    ///
    /// Returns:
    ///     UPayload: A new payload instance containing the string.
    ///
    /// Raises:
    ///     Exception: If the payload creation fails.
    ///
    /// Example:
    ///     >>> payload = up_py_rs.UPayload.from_string("Hello, World!")
    #[staticmethod]
    fn from_string(value: String) -> PyResult<Self> {
        let string_value = StringValue {
            value,
            ..Default::default()
        };
        let payload = RustUPayload::try_from_protobuf(string_value)
            .map_err(|e| PyException::new_err(format!("Failed to create payload: {}", e)))?;
        Ok(UPayload { inner: payload })
    }

    /// Create a UPayload from raw bytes.
    ///
    /// Args:
    ///     data (list[int]): A list of bytes (0-255) to wrap in the payload.
    ///
    /// Returns:
    ///     UPayload: A new payload instance containing the binary data.
    ///
    /// Example:
    ///     >>> payload = up_py_rs.UPayload.from_bytes([72, 101, 108, 108, 111])
    #[staticmethod]
    fn from_bytes(data: Vec<u8>) -> PyResult<Self> {
        // Create a simple bytes payload with a generic format
        Ok(UPayload {
            inner: RustUPayload::new(
                data,
                UPayloadFormat::UPAYLOAD_FORMAT_PROTOBUF_WRAPPED_IN_ANY,
            ),
        })
    }
}

/// Publisher for sending uProtocol messages.
///
/// SimplePublisher provides an easy-to-use interface for publishing messages
/// to specific resources in the uProtocol network.
#[pyclass]
pub struct SimplePublisher {
    inner: RustSimplePublisher,
    runtime: tokio::runtime::Runtime,
}

#[pymethods]
impl SimplePublisher {
    /// Create a new SimplePublisher.
    ///
    /// Args:
    ///     transport (LocalTransport): The transport to use for sending messages.
    ///     uri_provider (StaticUriProvider): The URI provider for the publishing entity.
    ///
    /// Returns:
    ///     SimplePublisher: A new publisher instance.
    ///
    /// Raises:
    ///     Exception: If the runtime creation fails.
    ///
    /// Example:
    ///     >>> transport = up_py_rs.LocalTransport()
    ///     >>> provider = up_py_rs.StaticUriProvider("device", 0x1234, 0x01)
    ///     >>> publisher = up_py_rs.SimplePublisher(transport, provider)
    #[new]
    fn new(transport: &LocalTransport, uri_provider: &StaticUriProvider) -> PyResult<Self> {
        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyException::new_err(format!("Failed to create runtime: {}", e)))?;
        Ok(SimplePublisher {
            inner: RustSimplePublisher::new(transport.inner.clone(), uri_provider.inner.clone()),
            runtime,
        })
    }

    /// Publish a message to a specific resource.
    ///
    /// Args:
    ///     resource_id (int): The target resource ID (0 to 65535).
    ///     payload (UPayload | None): The message payload, or None for empty messages.
    ///
    /// Raises:
    ///     Exception: If publishing fails.
    ///
    /// Example:
    ///     >>> payload = up_py_rs.UPayload.from_string("Hello")
    ///     >>> publisher.publish(0xb4c1, payload)
    ///     >>> # Or publish without payload:
    ///     >>> publisher.publish(0xb4c1, None)
    fn publish(
        &mut self,
        _py: Python,
        resource_id: u16,
        payload: Option<UPayload>,
    ) -> PyResult<()> {
        let payload_inner = payload.map(|p| p.inner);
        let call_options = CallOptions::for_publish(None, None, None);

        self.runtime.block_on(async {
            self.inner
                .publish(resource_id, call_options, payload_inner)
                .await
                .map_err(|e| PyException::new_err(format!("Failed to publish: {}", e)))
        })
    }
}

/// Internal struct to bridge Python callbacks to Rust UListener trait for notifications
struct PythonNotificationListener {
    callback: PyObject,
}

#[async_trait::async_trait]
impl UListener for PythonNotificationListener {
    async fn on_receive(&self, msg: RustUMessage) {
        Python::with_gil(|py| {
            // Import UMessage from local_transport module
            let py_msg = crate::local_transport::UMessage { inner: msg };
            if let Err(e) = self.callback.call1(py, (py_msg,)) {
                eprintln!("Error calling Python notification callback: {:?}", e);
            }
        });
    }
}

/// A Notifier that uses the uProtocol Transport Layer API to send and receive notifications to/from (other) uEntities.
///
/// SimpleNotifier provides an easy-to-use interface for sending notifications
/// and listening for notifications from other entities in the uProtocol network.
#[pyclass]
pub struct SimpleNotifier {
    inner: RustSimpleNotifier,
    runtime: tokio::runtime::Runtime,
    // Store listeners to enable proper unregistration
    // Key is a string representation of the topic URI
    listeners: Arc<Mutex<HashMap<String, Arc<PythonNotificationListener>>>>,
}

#[pymethods]
impl SimpleNotifier {
    /// Create a new SimpleNotifier.
    ///
    /// Args:
    ///     transport (LocalTransport): The transport to use for sending and receiving notifications.
    ///     uri_provider (StaticUriProvider): The URI provider for the notifying entity.
    ///
    /// Returns:
    ///     SimpleNotifier: A new notifier instance.
    ///
    /// Raises:
    ///     Exception: If the runtime creation fails.
    ///
    /// Example:
    ///     >>> transport = up_py_rs.LocalTransport()
    ///     >>> provider = up_py_rs.StaticUriProvider("my-vehicle", 0xa34b, 0x01)
    ///     >>> notifier = up_py_rs.SimpleNotifier(transport, provider)
    #[new]
    fn new(transport: &LocalTransport, uri_provider: &StaticUriProvider) -> PyResult<Self> {
        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyException::new_err(format!("Failed to create runtime: {}", e)))?;
        Ok(SimpleNotifier {
            inner: RustSimpleNotifier::new(transport.inner.clone(), uri_provider.inner.clone()),
            runtime,
            listeners: Arc::new(Mutex::new(HashMap::new())),
        })
    }

    /// Start listening for notifications on a specific topic.
    ///
    /// Args:
    ///     topic (UUri): The topic URI to listen to.
    ///     callback (callable): A Python function that accepts a UMessage parameter.
    ///                         Will be called when notifications arrive.
    ///
    /// Raises:
    ///     Exception: If listener registration fails.
    ///
    /// Example:
    ///     >>> def notification_handler(msg: UMessage):
    ///     ...     text = msg.extract_string()
    ///     ...     if text:
    ///     ...         print(f"Notification: {text}")
    ///     >>> topic = uri_provider.get_resource_uri(0xd100)
    ///     >>> notifier.start_listening(topic, notification_handler)
    fn start_listening(
        &mut self,
        _py: Python,
        topic: &UUri,
        callback: PyObject,
    ) -> PyResult<()> {
        // Create a key for storing the listener
        let topic_key = format!("{:?}", topic.inner);
        
        // Create the listener wrapper
        let listener = Arc::new(PythonNotificationListener {
            callback: callback.clone(),
        });
        
        // Store the listener for later retrieval
        {
            let mut listeners = self.listeners.lock()
                .map_err(|e| PyException::new_err(format!("Failed to acquire listener lock: {}", e)))?;
            listeners.insert(topic_key, listener.clone());
        }

        self.runtime.block_on(async {
            self.inner
                .start_listening(&topic.inner, listener)
                .await
                .map_err(|e| {
                    PyException::new_err(format!("Failed to start listening: {}", e))
                })
        })
    }

    /// Stop listening for notifications on a specific topic.
    ///
    /// Args:
    ///     topic (UUri): The topic URI to stop listening to.
    ///     callback (callable): The same Python function that was registered.
    ///
    /// Raises:
    ///     Exception: If listener unregistration fails.
    ///
    /// Example:
    ///     >>> notifier.stop_listening(topic, notification_handler)
    fn stop_listening(
        &mut self,
        _py: Python,
        topic: &UUri,
        callback: PyObject,
    ) -> PyResult<()> {
        // Create the same key used during registration
        let topic_key = format!("{:?}", topic.inner);
        
        // Retrieve the stored listener
        let listener = {
            let mut listeners = self.listeners.lock()
                .map_err(|e| PyException::new_err(format!("Failed to acquire listener lock: {}", e)))?;
            listeners.remove(&topic_key)
                .ok_or_else(|| PyException::new_err(
                    format!("No listener registered for topic: {}", topic_key)
                ))?
        };

        self.runtime.block_on(async {
            self.inner
                .stop_listening(&topic.inner, listener)
                .await
                .map_err(|e| {
                    PyException::new_err(format!("Failed to stop listening: {}", e))
                })
        })
    }

    /// Send a notification to a specific destination.
    ///
    /// Args:
    ///     resource_id (int): The notification resource ID (0 to 65535).
    ///     destination (UUri): The destination URI to send the notification to.
    ///     payload (UPayload | None): The notification payload, or None for empty notifications.
    ///
    /// Raises:
    ///     Exception: If notification sending fails.
    ///
    /// Example:
    ///     >>> payload = up_py_rs.UPayload.from_string("Alert!")
    ///     >>> destination = uri_provider.get_source_uri()
    ///     >>> notifier.notify(0xd100, destination, payload)
    fn notify(
        &mut self,
        _py: Python,
        resource_id: u16,
        destination: &UUri,
        payload: Option<UPayload>,
    ) -> PyResult<()> {
        let payload_inner = payload.map(|p| p.inner);
        let call_options = CallOptions::for_notification(None, None, None);

        self.runtime.block_on(async {
            self.inner
                .notify(resource_id, &destination.inner, call_options, payload_inner)
                .await
                .map_err(|e| PyException::new_err(format!("Failed to send notification: {}", e)))
        })
    }
}
