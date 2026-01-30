"""
Image format conversion utilities.

This module provides functions for converting images between different formats,
handling various input types (paths, bytes, PIL Images, etc.), and processing
SVG files.

Example:
    ```python
    from figwizz.convert import convert_image
    convert_image('input.png', 'jpg')
    # Returns: 'input.jpg'
    ```
"""

import os, base64
from PIL import Image
from io import BytesIO

from .modify import make_image_opaque
from .utils.images import normalize_image_input, save_image

__all__ = [
    'convert_image', 
    'bytes_to_image',
    'svg_to_image',
    'process_images']

# Input / Image Conversion ----------------------------------------

def convert_image(source_path, target_format, delete_original=False):
    """
    Convert an image file to another format.
    
    Supports conversion between all major image formats including PNG, JPEG, PDF,
    WEBP, TIFF, and more. Automatically handles transparency for formats that
    don't support it (like JPEG).
    
    Args:
        source_path (str or any): Path to the source image file, or any supported
            image input type (PIL Image, bytes, numpy array, URL, etc.)
        target_format (str): Target format to convert to. Supported formats include:
            'jpg'/'jpeg', 'png', 'pdf', 'webp', 'tiff', 'bmp', 'gif'
        delete_original (bool, optional): Whether to remove the original file after
            conversion. Only applies if source_path is a file path string.
            Defaults to False.
            
    Returns:
        str: Path to the converted image file
    
    Examples:
        ```python
        from figwizz import convert_image
        
        # Convert PNG to JPEG
        convert_image('image.png', 'jpg')
        # Creates: image.jpg
        
        # Convert to PDF and delete original
        convert_image('image.png', 'pdf', delete_original=True)
        # Creates: image.pdf (and deletes image.png)
        
        # Convert from URL
        convert_image('https://example.com/image.png', 'jpg')
        ```
    
    Note:
        - Automatically adds white background for JPEG/PDF (no transparency support)
        - Leading dot in format is automatically handled ('jpg' or '.jpg' both work)
        - For non-path inputs, creates file with default name 'converted_image.{format}'
        - Output file is created in the same directory as the input file
    """
    # Normalize input to PIL Image
    img = normalize_image_input(source_path)
    
    # Ensure the target format does not start with a dot
    if target_format.startswith('.'):
        target_format = target_format[1:]
    
    # Determine output path
    if isinstance(source_path, str) and not source_path.startswith(('http://', 'https://', 'data:')):
        base = os.path.splitext(source_path)[0]
        target_path = f"{base}.{target_format.lower()}"
    else:
        # For non-path inputs, use a temp name
        target_path = f"converted_image.{target_format.lower()}"
    
    # Use unified save_image function
    result_path = save_image(img, target_path, format=target_format.upper())
    
    # Delete original if requested and it's a file path
    if delete_original and isinstance(source_path, str):
        if os.path.exists(source_path):
            os.remove(source_path)

    return result_path

def bytes_to_image(bytes_input):
    """
    Convert bytes to a PIL Image object.
    
    Handles both raw bytes and base64-encoded string representations of images.
    This is particularly useful for handling image data from APIs, databases,
    or network transfers.
    
    Args:
        bytes_input (bytes or str): Image data in bytes or base64-encoded string format.
            If string, will be decoded from base64 first.
    
    Returns:
        PIL.Image.Image: PIL Image object ready for manipulation or saving
    
    Raises:
        ValueError: If bytes_input is not a valid bytes or string type
    
    Examples:
        ```python
        from figwizz import bytes_to_image
        import requests
        
        # From raw bytes
        response = requests.get('https://example.com/image.jpg')
        img = bytes_to_image(response.content)
        img.show()
        
        # From base64 string
        import base64
        with open('image.jpg', 'rb') as f:
            b64_string = base64.b64encode(f.read()).decode()
        img = bytes_to_image(b64_string)
        
        # Save the image
        img.save('output.png')
        ```
    
    Note:
        - Automatically detects and handles base64-encoded strings
        - Returns a PIL Image object that can be manipulated or saved
        - Works with any image format supported by PIL (PNG, JPEG, etc.)
    """
    # check bytes type (e.g. base64, bytes, etc.)
    if isinstance(bytes_input, str):
        bytes_input = base64.b64decode(bytes_input)
    elif isinstance(bytes_input, bytes):
        pass
    else: # raise error for invalid bytes input
        raise ValueError(f"Invalid bytes input: {type(bytes_input)}")
    
    # convert bytes to image
    return Image.open(BytesIO(bytes_input))

def svg_to_image(svg_content, output_path,
                 width=None, height=None, scale=None):
    """
    Convert SVG content to a raster image.
    
    Requires the optional cairosvg library for SVG conversion. This function
    is useful for converting vector graphics to raster formats like PNG, JPEG,
    or PDF while maintaining quality through scaling options.
    
    Args:
        svg_content (bytes): Raw SVG file content as bytes
        output_path (str): Path to save the output file. File extension determines
            output format. Supported: .png, .jpg, .jpeg, .pdf
        width (int, optional): Output width in pixels. If None, uses SVG's natural
            width. Defaults to None.
        height (int, optional): Output height in pixels. If None, uses SVG's natural
            height. Defaults to None.
        scale (float, optional): Scale factor for the output (e.g., 2.0 for 2x
            resolution, 3.0 for 3x). Useful for high-DPI displays. Defaults to None.
    
    Returns:
        bool: True if conversion was successful, False if cairosvg is not installed
            or conversion failed
    
    Raises:
        ValueError: If output_path has an unsupported file extension
    
    Examples:
        ```python
        from figwizz.convert import svg_to_image
        
        # Read SVG file
        with open('icon.svg', 'rb') as f:
            svg_data = f.read()
        
        # Convert to PNG with default size
        svg_to_image(svg_data, 'icon.png')
        
        # Convert to high-resolution PNG
        svg_to_image(svg_data, 'icon.png', scale=3.0)
        
        # Convert with specific dimensions
        svg_to_image(svg_data, 'icon.png', width=512, height=512)
        
        # Convert to JPEG
        svg_to_image(svg_data, 'icon.jpg', scale=2.0)
        ```
    
    Note:
        - Requires cairosvg: `pip install cairosvg`
        - Returns False with a warning if cairosvg is not installed
        - Scale and width/height can be used together
        - Maintains SVG quality during conversion
        - Prints informative error messages on failure
    """
    
    if output_path.split('.')[-1] not in ['png', 'jpg', 'jpeg', 'pdf']:
        raise ValueError(f"Invalid output path: {output_path}. ",
                         "Output path must end with .png, .jpg, .jpeg, or .pdf.")
        
    output_ext = output_path.split('.')[-1]
    
    try:
        import cairosvg  # type: ignore
    except ImportError:
        print("  Warning: cairosvg not installed, cannot convert SVG to PNG")
        print("  Install with: pip install cairosvg")
        return False
    
    try:
        print('  Converting SVG to {output_ext.upper()}...')
        cairosvg.svg2png(
            bytestring=svg_content,
            write_to=str(output_path),
            output_width=width,
            output_height=height,
            scale=scale
        )
        return True
    except Exception as e:
        print(f"  Error converting SVG to {output_ext.upper()}: {e}")
        return False

# Batch Processing ------------------------------------------------

def _process_image_path(image_path):
    """Process an image path to a PIL Image object.
    
    Args:
        image_path: Path to the image file.
    """
    return Image.open(image_path)

def _process_image_bytes(image_bytes):
    """Process image bytes to a PIL Image object.
    
    Args:
        image_bytes: Bytes of the image.
    """
    return bytes_to_image(image_bytes)

def _process_image_pil(image):
    """Process a PIL Image object.
    
    Args:
        image: PIL Image object.
    """
    return image

def _process_image_list(images):
    """Process a list of images to a list of PIL Image objects.
    
    Args:
        images: List of images.
    """
    return [_process_image_pil(image) for image in images]

def process_images(images, target_format, **kwargs):
    """Process an image to a target format.
    
    Args:
        image: PIL image object, path, bytes, or list thereof.
        target_format: Target format to convert to (e.g., 'jpg', 'png', 'pdf').
        **kwargs: Additional keyword arguments.
    """
    # TODO: Implement this function. Default output format should be a PIL Image object.
    # Check if images is a list or single image
    raise NotImplementedError("process_images is not implemented yet.")