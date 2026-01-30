"""
Color processing utilities for FigWizz.

This module provides functions for parsing, extracting, and manipulating colors
in images. It supports multiple color input formats and provides intelligent
color analysis for automatic color selection.

Key features:
- Parse colors from multiple formats (hex, RGB, color names)
- Extract dominant colors from images
- Generate contrasting colors for borders and text

Example:
    ```python
    from figwizz.colors import parse_color, extract_dominant_color, get_contrasting_color
    from PIL import Image
    
    # Parse different color formats
    rgb = parse_color('#FF5733')
    rgb = parse_color('red')
    rgb = parse_color((255, 87, 51))
    
    # Extract dominant color from image
    img = Image.open('image.png')
    dominant = extract_dominant_color(img)
    
    # Get contrasting color
    contrast = get_contrasting_color(dominant)
    ```
"""

from PIL import ImageColor
import colorsys


__all__ = ['parse_color', 'extract_dominant_color', 'get_contrasting_color']


def parse_color(color_input):
    """
    Parse color input to RGB tuple.
    
    Args:
        color_input: Hex code ('#RRGGBB'), RGB tuple (R, G, B), or color name ('red', 'blue', etc.)
    
    Returns:
        RGB tuple (R, G, B)
    
    Examples:
        ```python
        parse_color('#FF5733')
        # Returns: (255, 87, 51)
        
        parse_color((255, 87, 51))
        # Returns: (255, 87, 51)
        
        parse_color('red')
        # Returns: (255, 0, 0)
        ```
    """
    if isinstance(color_input, str):
        # Try to parse as hex or named color
        try:
            return ImageColor.getrgb(color_input)
        except ValueError:
            raise ValueError(f"Invalid color: {color_input}")
    elif isinstance(color_input, (tuple, list)) and len(color_input) == 3:
        return tuple(color_input)
    else:
        raise ValueError(f"Invalid color format: {color_input}")


def extract_dominant_color(img, num_colors=5):
    """
    Extract the dominant color from an image using color quantization.
    
    Uses color quantization to reduce the image to a small palette and then
    identifies the most frequent color, excluding very light colors that are
    likely backgrounds.
    
    Args:
        img (PIL.Image.Image): PIL Image object to analyze
        num_colors (int, optional): Number of colors to quantize to. Higher values
            provide more precision but slower processing. Defaults to 5.
    
    Returns:
        tuple: RGB tuple (R, G, B) of the dominant color, where each value
            is in range 0-255
    
    Examples:
        ```python
        from figwizz.colors import extract_dominant_color
        from PIL import Image
        
        img = Image.open('photo.jpg')
        dominant = extract_dominant_color(img)
        print(f"Dominant color: RGB{dominant}")
        
        # Use more colors for better precision
        dominant = extract_dominant_color(img, num_colors=10)
        ```
    
    Note:
        - Image is resized to 100x100 for faster processing
        - Very light colors (potential backgrounds) are automatically skipped
        - Returns the most frequent color after filtering
    """
    # Resize image for faster processing
    img_small = img.copy()
    img_small.thumbnail((100, 100))
    
    # Convert to RGB if necessary
    if img_small.mode != 'RGB':
        img_small = img_small.convert('RGB')
    
    # Quantize colors
    img_quant = img_small.quantize(colors=num_colors)
    
    # Get palette and convert to RGB
    palette = img_quant.getpalette()
    
    # Count color frequency
    histogram = img_quant.histogram()
    
    # Find most frequent color (excluding first if it's white/background)
    sorted_colors = sorted(enumerate(histogram), key=lambda x: x[1], reverse=True)
    
    for idx, count in sorted_colors:
        if count > 0:
            # Get RGB values from palette
            r = palette[idx * 3]
            g = palette[idx * 3 + 1]
            b = palette[idx * 3 + 2]
            
            # Skip very light colors (likely background)
            if r + g + b < 700:  # Not pure white-ish
                return (r, g, b)
    
    # Fallback to first color
    return (palette[0], palette[1], palette[2])


def get_contrasting_color(rgb, prefer_dark=True):
    """
    Generate a contrasting color for the given RGB color.
    
    Uses relative luminance calculation to determine if the input color is
    light or dark, then generates an appropriate contrasting color. Useful
    for creating borders, text overlays, or UI elements that need to stand
    out against an image.
    
    Args:
        rgb (tuple): RGB tuple (R, G, B) where each value is in range 0-255
        prefer_dark (bool, optional): If True, prefers dark contrasting colors
            even for dark inputs (creating darker shades). If False, uses
            pure black/white contrast. Defaults to True.
    
    Returns:
        tuple: RGB tuple (R, G, B) of the contrasting color
    
    Examples:
        ```python
        from figwizz.colors import get_contrasting_color
        
        # Get contrast for a light color (returns dark)
        contrast = get_contrasting_color((200, 200, 200))
        # Returns: (40, 40, 40)
        
        # Get contrast for a dark color with prefer_dark=False
        contrast = get_contrasting_color((50, 50, 50), prefer_dark=False)
        # Returns: (255, 255, 255)
        
        # Use with extracted dominant color
        from figwizz.colors import extract_dominant_color
        dominant = extract_dominant_color(img)
        border_color = get_contrasting_color(dominant)
        ```
    
    Note:
        - Uses standard relative luminance formula (0.299*R + 0.587*G + 0.114*B)
        - When prefer_dark=True, creates darker/more saturated versions for dark inputs
        - When prefer_dark=False, returns pure black (0,0,0) or white (255,255,255)
    """
    r, g, b = rgb
    
    # Calculate relative luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    if prefer_dark:
        # If image is light, use dark border; if dark, use darker shade
        if luminance > 0.5:
            # Image is light, return dark color
            return (40, 40, 40)
        else:
            # Image is dark, return slightly darker version
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            v = max(0, v - 0.3)  # Darken
            s = min(1, s + 0.2)  # Increase saturation slightly
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return (int(r * 255), int(g * 255), int(b * 255))
    else:
        # Return contrasting black or white
        if luminance > 0.5:
            return (0, 0, 0)
        else:
            return (255, 255, 255)

