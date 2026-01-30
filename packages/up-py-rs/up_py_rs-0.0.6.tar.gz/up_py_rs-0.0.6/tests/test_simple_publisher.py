import pytest

from up_py_rs import StaticUriProvider
from up_py_rs.communication import SimplePublisher
from up_py_rs.local_transport import LocalTransport


class TestSimplePublisher:
    """Tests SimplePublisher"""

    def test_create_publisher(self):
        """Test creating SimplePublisher instance"""
        uri_provider = StaticUriProvider("my-vehicle", 0xA34B, 0x01)
        transport = LocalTransport()

        publisher = SimplePublisher(transport, uri_provider)

        assert publisher is not None
        assert hasattr(publisher, "publish")


def test_version():
    """Test that the version is accessible"""
    import up_py_rs

    assert hasattr(up_py_rs, "__version__")
    assert up_py_rs.__version__ is not None

if __name__ == '__main__':
    pytest.main([__file__, "-v"])
