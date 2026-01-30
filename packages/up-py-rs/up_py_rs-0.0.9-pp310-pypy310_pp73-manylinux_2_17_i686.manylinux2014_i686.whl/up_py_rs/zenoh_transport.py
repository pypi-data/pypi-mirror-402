"""Zenoh Transport for uProtocol

This module provides network transport capabilities using the Zenoh protocol.
Zenoh enables efficient, real-time communication across network boundaries.

Classes:
    UPTransportZenoh: Main transport class for Zenoh-based communication
    UPTransportZenohBuilder: Builder for configuring Zenoh transport

Example:
    >>> from up_py_rs.zenoh_transport import UPTransportZenoh
    >>> transport = UPTransportZenoh.builder("my-vehicle").build()
    >>> # Use transport.send() to publish messages
"""

try:
    from up_py_rs import zenoh_transport as _zenoh_transport

    UPTransportZenoh = _zenoh_transport.UPTransportZenoh
    UPTransportZenohBuilder = _zenoh_transport.UPTransportZenohBuilder

    __all__ = ["UPTransportZenoh", "UPTransportZenohBuilder"]
except ImportError as e:
    raise ImportError(
        "Zenoh transport not available. Install with: pip install up-py-rs[zenoh]"
    ) from e
