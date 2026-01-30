"""
Image modification and transformation utilities.

This module provides functions for modifying images, including adding
opaque backgrounds and cropping to n-sided polygon shapes (hexagons, etc.).

Example:
    ```python
    from figwizz.modify import ngon_crop, make_image_opaque
    
    # Create hexagon-shaped crop
    hexagon = ngon_crop('image.png', sides=6, border_size=5)
    
    # Make RGBA image opaque
    opaque_img = make_image_opaque(rgba_image)
    ```
"""

from copy import copy
from PIL import Image, ImageDraw, ImageChops
import math

from .colors import parse_color, extract_dominant_color, get_contrasting_color
from .utils.images import normalize_image_input

__all__ = ['make_image_opaque', 'ngon_crop']

def make_image_opaque(img_input, bg_color=(255, 255, 255)):
    """
    Make an image opaque by adding a solid background color.
    
    Converts images with transparency (RGBA, LA) to fully opaque images by
    compositing them over a solid background color. Essential for formats that
    don't support transparency like JPEG or PDF.
    
    Args:
        img_input: Image in any supported format (path, PIL Image, bytes, numpy
            array, URL, etc.). Will be normalized to PIL format automatically.
        bg_color (tuple, optional): Background color as RGB tuple (R, G, B) where
            each value is 0-255. Defaults to (255, 255, 255) for white.
    
    Returns:
        PIL.Image.Image: PIL Image object in RGB mode with solid background
    
    Examples:
        ```python
        from figwizz import make_image_opaque
        from PIL import Image
        
        # Make PNG with transparency opaque with white background
        img = Image.open('transparent_logo.png')
        opaque_img = make_image_opaque(img)
        opaque_img.save('opaque_logo.jpg')  # Can save as JPEG now
        
        # Use custom background color (light gray)
        opaque_img = make_image_opaque('logo.png', bg_color=(240, 240, 240))
        
        # Works with any input type
        from PIL import Image
        opaque_img = make_image_opaque('https://example.com/transparent.png')
        ```
    
    Note:
        - Preserves original image if it has no transparency
        - Automatically converts to RGB mode for consistent output
        - Alpha channel is used as mask for proper compositing
        - Particularly useful before converting to JPEG or PDF
        - Works with both RGBA (color + alpha) and LA (grayscale + alpha) modes
    """
    # Normalize input to PIL Image
    img = normalize_image_input(img_input)
    img = copy(img)
    
    # Check if the image has an alpha channel
    if img.mode in ('RGBA', 'LA') or ('transparency' in img.info):
        # Create a new image with a white background
        background = Image.new(img.mode[:-1], img.size, bg_color)
        # Paste the image on the background (masking with itself)
        background.paste(img, img.split()[-1])
        img = background  # ... using the alpha channel as mask
    
    # Convert image to RGB 
    if img.mode != 'RGB':
        img = img.convert('RGB')
            
    return img # image updated with nontrasparent background


def ngon_crop(img_input, sides=6, crop_size=None, shift_x=0, shift_y=0,
              rotation=0, border_size=0, border_color="auto", padding=0, 
              background_color=None):
    """
    Crop an image to an n-sided polygon (n-gon), with optional border and background.
    
    Useful for creating tidyverse-style hexicons and other polygonal image crops.
    
    Args:
        img_input: Image in any supported format (path, PIL Image, bytes, numpy array, etc.).
        sides: Number of sides of the polygon (default: 6 for hexagon).
        crop_size: Size of the output image as (width, height). If None, uses a square 
                   based on the smallest dimension of the input image.
        shift_x: Horizontal shift in pixels (default: 0). Positive values shift right.
        shift_y: Vertical shift in pixels (default: 0). Positive values shift down.
        rotation: Rotation angle in degrees (default: 0).
        border_size: Width of the border in pixels (default: 0, no border).
        border_color: Border color. Can be:
            - "auto": Automatically select contrasting color from image
            - Hex code: e.g., "#FF5733"
            - RGB tuple: e.g., (255, 87, 51)
            - Color name: e.g., "red", "blue"
        padding: Padding in pixels around the image content before cropping (default: 0).
                 This allows the n-gon to reshape without cutting into the image.
        background_color: Background color inside the polygon (default: None for transparent).
            Can be hex code, RGB tuple, or color name. Area outside polygon remains transparent.
    
    Returns:
        PIL Image object with transparent background outside polygon and polygon crop applied.
    
    Examples:
        ```python
        # Create a hexagon with auto border
        img = ngon_crop("input.png", sides=6, border_size=5, border_color="auto")
        
        # Create an octagon with red border and padding
        img = ngon_crop("input.png", sides=8, border_size=3, border_color="red", padding=20)
        
        # Create a pentagon with no border
        img = ngon_crop("input.png", sides=5)
        
        # Create a hexagon with white background inside
        img = ngon_crop("input.png", sides=6, background_color="white")
        
        # Create a hexagon with custom background color
        img = ngon_crop("input.png", sides=6, background_color="#F0F0F0")
        ```
    """
    # Normalize input to PIL Image
    img = normalize_image_input(img_input)
    img = copy(img)
    
    # Convert to RGBA if necessary
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')
    elif img.mode == 'RGB':
        img = img.convert('RGBA')
    
    # Apply padding if requested
    if padding > 0:
        padded_width = img.width + 2 * padding
        padded_height = img.height + 2 * padding
        padded_img = Image.new('RGBA', (padded_width, padded_height), (0, 0, 0, 0))
        padded_img.paste(img, (padding, padding), img)
        img = padded_img
    
    # Determine output size
    if crop_size is None:
        # Default: use smallest dimension to create a square output
        min_dim = min(img.size)
        output_size = (min_dim, min_dim)
    else:
        output_size = crop_size
    
    # Resize image to fit output size while maintaining aspect ratio
    if img.size != output_size:
        img.thumbnail(output_size, Image.Resampling.LANCZOS)
    
    # Create a new RGBA image with transparent background
    width, height = output_size
    result = Image.new('RGBA', output_size, (0, 0, 0, 0))
    
    # Calculate polygon vertices
    center_x, center_y = width / 2, height / 2
    center_x += shift_x
    center_y += shift_y
    radius = min(width, height) / 2 - border_size
    
    # Generate polygon points
    angle_offset = math.radians(rotation)
    vertices = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides + angle_offset
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y))
    
    # Create mask for the polygon
    mask = Image.new('L', output_size, 0)
    draw = ImageDraw.Draw(mask)
    # Fill polygon area with white (visible), background stays black (transparent)
    draw.polygon(vertices, fill=255)
    
    # Add background color inside polygon if requested
    if background_color is not None:
        bg_rgb = parse_color(background_color)
        background_layer = Image.new('RGBA', output_size, bg_rgb + (255,))
        background_layer.putalpha(mask)
        result.paste(background_layer, (0, 0), background_layer)
    
    # Paste the image centered on the result, preserving its alpha
    img_x = (width - img.width) // 2
    img_y = (height - img.height) // 2
    result.paste(img, (img_x, img_y), img)
    
    # Combine the polygon mask with the image's existing alpha channel
    # This preserves both the polygon shape and any transparency in the original image
    original_alpha = result.split()[3]  # Get alpha channel
    combined_alpha = ImageChops.multiply(original_alpha, mask)
    result.putalpha(combined_alpha)
    
    # Add border if requested
    if border_size > 0:
        # Determine border color
        if border_color == "auto":
            # Extract dominant color and get contrasting color
            dominant = extract_dominant_color(img)
            border_rgb = get_contrasting_color(dominant, prefer_dark=True)
        else:
            border_rgb = parse_color(border_color)
        
        # Create a mask for the border ring (outer polygon minus inner polygon)
        border_mask = Image.new('L', output_size, 0)
        border_mask_draw = ImageDraw.Draw(border_mask)
        
        # Draw the outer border polygon
        border_radius = min(width, height) / 2
        border_vertices = []
        for i in range(sides):
            angle = 2 * math.pi * i / sides + angle_offset
            x = center_x + border_radius * math.cos(angle)
            y = center_y + border_radius * math.sin(angle)
            border_vertices.append((x, y))
        
        # Fill outer polygon with white (visible)
        border_mask_draw.polygon(border_vertices, fill=255)
        
        # Cut out the inner polygon by filling it with black (transparent)
        border_mask_draw.polygon(vertices, fill=0)
        
        # Create border layer with the border color
        border_layer = Image.new('RGBA', output_size, border_rgb + (255,))
        border_layer.putalpha(border_mask)
        
        # Create final result: border layer on bottom, cropped image on top
        bordered = Image.new('RGBA', output_size, (0, 0, 0, 0))
        bordered.paste(border_layer, (0, 0), border_layer)
        bordered.paste(result, (0, 0), result)
        result = bordered
    
    return result