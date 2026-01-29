"""Utility functions for pysiphon client."""

import tomli
from typing import Tuple
from pathlib import Path
from PIL import Image
import io


def hex_to_bytes(hex_string: str) -> bytes:
    """
    Convert hex string to bytes.
    
    Args:
        hex_string: Hex string like "6D DE AD BE EF" or "6DDEADBEEF"
    
    Returns:
        bytes object
    """
    # Remove whitespace and split into pairs
    hex_clean = hex_string.replace(" ", "").replace("\t", "").replace("\n", "")
    
    # Convert pairs to bytes
    byte_list = []
    for i in range(0, len(hex_clean), 2):
        if i + 1 < len(hex_clean):
            byte_str = hex_clean[i:i+2]
            byte_list.append(int(byte_str, 16))
    
    return bytes(byte_list)


def bytes_to_hex(data: bytes) -> str:
    """
    Convert bytes to hex string format.
    
    Args:
        data: bytes object
    
    Returns:
        Hex string like "6D DE AD BE EF"
    """
    return " ".join(f"{b:02x}" for b in data)


def parse_config_file(filepath: str) -> Tuple[str, str, dict]:
    """
    Parse TOML config file and extract process configuration.
    
    Args:
        filepath: Path to TOML config file
    
    Returns:
        Tuple of (process_name, process_window_name, attributes_dict)
        where attributes_dict maps attribute names to their config
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    config_path = Path(filepath)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    
    # Get process info
    if "process_info" not in config:
        raise ValueError("Missing [process_info] section in config")
    
    process_info = config["process_info"]
    process_name = process_info.get("name", "")
    process_window_name = process_info.get("window_name", "")
    
    if not process_name:
        raise ValueError("Missing 'name' in [process_info]")
    
    # Get attributes
    if "attributes" not in config:
        raise ValueError("Missing [attributes] section in config")
    
    attributes = {}
    for attr_name, attr_config in config["attributes"].items():
        if not isinstance(attr_config, dict):
            continue
        
        attributes[attr_name] = {
            "pattern": attr_config.get("pattern", ""),
            "offsets": attr_config.get("offsets", []),
            "type": attr_config.get("type", ""),
            "length": attr_config.get("length", 0),
            "method": attr_config.get("method", ""),
            "mask": attr_config.get("mask", 0xFF),
        }
    
    return process_name, process_window_name, attributes


def save_frame_image(pixels: bytes, width: int, height: int, filename: str) -> bool:
    """
    Save frame pixels to image file.
    
    Args:
        pixels: Raw BGRA pixel data
        width: Image width
        height: Image height
        filename: Output filename (format auto-detected from extension)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert BGRA to RGBA
        pixel_array = bytearray(pixels)
        for i in range(0, len(pixel_array), 4):
            # Swap B and R channels
            pixel_array[i], pixel_array[i+2] = pixel_array[i+2], pixel_array[i]
        
        # Create PIL Image
        img = Image.frombytes("RGBA", (width, height), bytes(pixel_array))
        
        # Convert to RGB if saving as JPEG (no alpha channel)
        if filename.lower().endswith(('.jpg', '.jpeg')):
            img = img.convert("RGB")
        
        # Save with auto-detected format
        img.save(filename)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def format_bytes_size(size: int) -> str:
    """
    Format byte size in human-readable format.
    
    Args:
        size: Size in bytes
    
    Returns:
        Formatted string like "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

