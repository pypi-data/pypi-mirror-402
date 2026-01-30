"""
Icon workflow and convenience functions.

This module provides high-level workflows for creating icons from images,
particularly tidyverse-style hexagonal icons (hexicons) commonly used in
the R community for package logos.

The make_hexicon function is a convenient wrapper around the ngon_crop
function with sensible defaults for creating hexagonal icons.

Example:
    ```python
    from figwizz import make_hexicon
    
    # Create a simple hexicon
    hexicon = make_hexicon('logo.png')
    hexicon.save('hexicon.png')
    
    # Create hexicon with border
    hexicon = make_hexicon('logo.png', border_size=5, border_color='auto')
    ```
"""

import os
from PIL import Image

from ..utils.images import normalize_image_input
from ..modify import ngon_crop

__all__ = ['make_hexicon']

def make_hexicon(input_image, size=None, **kwargs):
    """
    Make a tidyverse-style Hexicon from an input image.
    
    Args:
        input_image: Image in any supported format (path, PIL Image, bytes, numpy array, URL, etc.).
        size: Size of the output image as (width, height). If None, uses a square 
              based on the smallest dimension of the input image.
        **kwargs: Additional keyword arguments for ngon_crop.
            shift_x: Horizontal shift in pixels (default: 0). Positive values shift right.
            shift_y: Vertical shift in pixels (default: 0). Positive values shift down.
            rotation: Rotation angle in degrees (default: 0).
            border_size: Width of the border in pixels (default: 0, no border).
            border_color: Border color. Can be:
                - "auto": Automatically select contrasting color from image
                - Hex code: e.g., "#FF5733"
                - RGB tuple: e.g., (255, 87, 51)
                - Color name: e.g., "red", "blue"
            background_color: Background color inside the hexagon (default: None for transparent).
                Can be hex code, RGB tuple, or color name. Area outside hexagon remains transparent.
    Returns:
        PIL Image object with the hexicon applied.
        
    Examples:
        ```python
        # Make a hexicon with no border
        img = make_hexicon("input.png")
        
        # Make a hexicon with red border and padding
        img = make_hexicon("input.png", border_size=3, border_color="red", padding=20)
        
        # Make hexicon with slight upwards shift
        img = make_hexicon("input.png", shift_y=10)
        
        # Make hexicon with white background inside
        img = make_hexicon("input.png", background_color="white")
        ```
    """
    # Normalize input to PIL Image
    image = normalize_image_input(input_image)
    
    return ngon_crop(image, sides=6, crop_size=size, **kwargs)