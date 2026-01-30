"""
Unified image input/output handling utilities.

This module provides a comprehensive system for handling images in various
input formats and converting between different representations. It eliminates
the need to manually handle different image types throughout the codebase.

Supported input formats:
- File paths (local files)
- URLs (http/https)
- PIL Image objects
- Bytes (raw image data)
- NumPy arrays
- File-like objects (BytesIO, etc.)
- Base64 encoded strings

The normalize_image_input function is used extensively throughout figwizz to
provide a consistent interface for image operations.

Example:
    ```python
    from figwizz.utils.images import normalize_image_input, save_image
    
    # All these work the same way
    img1 = normalize_image_input('path/to/image.png')
    img2 = normalize_image_input('https://example.com/image.jpg')
    img3 = normalize_image_input(bytes_data)
    img4 = normalize_image_input(numpy_array)
    
    # Save with automatic format handling
    save_image(img1, 'output.jpg', quality=95)
    ```
"""

import os
import base64
import tempfile
from io import BytesIO
from pathlib import Path
from PIL import Image
import numpy as np

__all__ = [
    'normalize_image_input',
    'normalize_image_output',
    'save_image',
    'is_image_path',
    'is_url',
]


def is_url(input_str):
    """Check if a string is a URL."""
    if not isinstance(input_str, str):
        return False
    return input_str.startswith(('http://', 'https://'))


def is_image_path(input_str):
    """Check if a string is a valid image file path."""
    if not isinstance(input_str, str):
        return False
    if is_url(input_str):
        return False
    path = Path(input_str)
    return path.exists() and path.is_file()


def normalize_image_input(image_input, return_type='pil'):
    """
    Normalize various image input types to a consistent format.
    
    Supports:
    - Path strings (local file paths)
    - PIL Image objects
    - bytes (raw image data)
    - numpy arrays
    - file-like objects (BytesIO, BufferedReader, etc.)
    - base64 encoded strings
    - URLs (http/https)
    
    Args:
        image_input: Image in any supported format
        return_type: Desired output format ('pil', 'bytes', 'numpy', 'array')
    
    Returns:
        Image in requested format (default: PIL Image)
    
    Raises:
        ValueError: If image_input type is not recognized
        FileNotFoundError: If path doesn't exist
        RuntimeError: If URL fetch fails
    
    Examples:
        ```python
        img = normalize_image_input('/path/to/image.png')
        img = normalize_image_input(bytes_data)
        arr = normalize_image_input(img, return_type='numpy')
        ```
    """
    pil_image = None
    
    # Handle PIL Image
    if isinstance(image_input, Image.Image):
        pil_image = image_input
    
    # Handle path string
    elif isinstance(image_input, (str, Path)):
        input_str = str(image_input)
        
        # Check if it's a URL
        if is_url(input_str):
            pil_image = _load_image_from_url(input_str)
        
        # Check if it's base64
        elif _is_base64(input_str):
            pil_image = _load_image_from_base64(input_str)
        
        # Treat as file path
        else:
            path = Path(input_str)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {input_str}")
            if not path.is_file():
                raise ValueError(f"Path is not a file: {input_str}")
            pil_image = Image.open(input_str)
    
    # Handle bytes
    elif isinstance(image_input, bytes):
        pil_image = Image.open(BytesIO(image_input))
    
    # Handle file-like objects
    elif hasattr(image_input, 'read'):
        # Reset position if possible
        if hasattr(image_input, 'seek'):
            image_input.seek(0)
        pil_image = Image.open(image_input)
    
    # Handle numpy arrays
    elif _is_numpy_array(image_input):
        pil_image = _numpy_to_pil(image_input)
    
    else:
        raise ValueError(
            f"Unsupported image input type: {type(image_input)}. "
            "Supported types: PIL Image, path string, bytes, numpy array, "
            "file-like object, base64 string, or URL."
        )
    
    # Convert to requested output format
    return _convert_image_format(pil_image, return_type)


def normalize_image_output(image, output_format='pil'):
    """
    Convert image to specified output format.
    
    Args:
        image: PIL Image object
        output_format: Desired format ('pil', 'bytes', 'numpy', 'array')
    
    Returns:
        Image in requested format
    """
    return _convert_image_format(image, output_format)


def save_image(image, output_path, format=None, make_opaque=None, **kwargs):
    """
    Save image to file with automatic format detection and handling.
    
    Args:
        image: Image in any supported format (will be normalized to PIL)
        output_path: Path where image should be saved
        format: Image format (e.g., 'PNG', 'JPEG'). Auto-detected from path if None.
        make_opaque: Whether to add white background for formats that don't support transparency.
                     Auto-detected if None (True for JPEG/PDF, False otherwise).
        **kwargs: Additional arguments passed to PIL Image.save()
    
    Returns:
        Path to saved image
    
    Examples:
        ```python
        save_image(img, 'output.png')
        save_image(img, 'output.jpg', quality=95)
        ```
    """
    # Normalize input to PIL Image
    pil_image = normalize_image_input(image, return_type='pil')
    
    # Determine format from path if not specified
    if format is None:
        ext = Path(output_path).suffix.lower()
        if ext:
            format = ext[1:].upper()  # Remove dot and uppercase
        else:
            format = 'PNG'  # Default format
    
    # Normalize format (PIL uses 'JPEG' not 'JPG')
    if format.upper() == 'JPG':
        format = 'JPEG'
    
    # Auto-detect if we should make opaque
    if make_opaque is None:
        make_opaque = format.upper() in ('JPEG', 'JPG', 'PDF')
    
    # Make opaque if needed
    if make_opaque and pil_image.mode in ('RGBA', 'LA'):
        from ..modify import make_image_opaque
        pil_image = make_image_opaque(pil_image)
    
    # Ensure RGB mode for JPEG
    if format.upper() in ('JPEG', 'JPG') and pil_image.mode not in ('RGB', 'L'):
        if pil_image.mode == 'RGBA':
            from ..modify import make_image_opaque
            pil_image = make_image_opaque(pil_image)
        else:
            pil_image = pil_image.convert('RGB')
    
    # Create parent directories if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save image
    pil_image.save(output_path, format=format, **kwargs)
    
    return str(output_path)


# Helper functions


def _is_base64(s):
    """Check if string might be base64 encoded."""
    if not isinstance(s, str):
        return False
    # Base64 strings are typically long and contain only valid base64 characters
    if len(s) < 50:  # Too short to be an image
        return False
    # Check for data URI scheme
    if s.startswith('data:image/'):
        return True
    # Check if it's valid base64 (contains only valid characters)
    import re
    return bool(re.match(r'^[A-Za-z0-9+/]*={0,2}$', s))


def _load_image_from_base64(base64_string):
    """Load PIL Image from base64 string."""
    # Handle data URI scheme
    if base64_string.startswith('data:image/'):
        # Extract the base64 part after the comma
        base64_string = base64_string.split(',', 1)[1]
    
    try:
        image_bytes = base64.b64decode(base64_string)
        return Image.open(BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}")


def _load_image_from_url(url):
    """Load PIL Image from URL."""
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except ImportError:
        raise RuntimeError(
            "requests library is required to load images from URLs. "
            "Install it with: pip install requests"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load image from URL {url}: {e}")


def _is_numpy_array(obj):
    """Check if object is a numpy array."""
    return isinstance(obj, np.ndarray)


def _numpy_to_pil(arr):
    """Convert numpy array to PIL Image."""
    # Handle different array shapes
    if arr.ndim == 2:
        # Grayscale
        return Image.fromarray(arr.astype(np.uint8), mode='L')
    elif arr.ndim == 3:
        if arr.shape[2] == 3:
            # RGB
            return Image.fromarray(arr.astype(np.uint8), mode='RGB')
        elif arr.shape[2] == 4:
            # RGBA
            return Image.fromarray(arr.astype(np.uint8), mode='RGBA')
        else:
            raise ValueError(f"Unsupported array shape: {arr.shape}")
    else:
        raise ValueError(f"Unsupported array dimensions: {arr.ndim}")


def _pil_to_numpy(image):
    """Convert PIL Image to numpy array."""
    return np.array(image)


def _pil_to_bytes(image, format='PNG'):
    """Convert PIL Image to bytes."""
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def _convert_image_format(pil_image, output_format):
    """Convert PIL Image to requested format."""
    output_format = output_format.lower()
    
    if output_format in ('pil', 'pillow'):
        return pil_image
    elif output_format in ('numpy', 'array', 'np'):
        return _pil_to_numpy(pil_image)
    elif output_format == 'bytes':
        return _pil_to_bytes(pil_image)
    else:
        raise ValueError(
            f"Unsupported output format: {output_format}. "
            "Supported formats: 'pil', 'numpy', 'bytes'"
        )

