"""
pysiphon - Python gRPC client for Siphon service.

Provides programmatic API and CLI for memory manipulation, input control,
screen capture, and recording capabilities.
"""

from .client import SiphonClient
from .utils import hex_to_bytes, bytes_to_hex, parse_config_file

__version__ = "0.1.0"
__all__ = ["SiphonClient", "hex_to_bytes", "bytes_to_hex", "parse_config_file"]

