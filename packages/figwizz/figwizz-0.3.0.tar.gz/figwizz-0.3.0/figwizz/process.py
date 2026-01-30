"""
Image processing utilities.

This module provides functions for processing images, including:
- Resizing
- Cropping
- Rotating
- Flipping
- Applying filters
- Applying masks
- Applying transformations

Example:
    ```python
    from figwizz.process import (
        load_image, resize_image, crop_image, rotate_image,
        flip_image, apply_filter, apply_mask, apply_transform
    )
    
    # Load and resize
    img = load_image('photo.png')
    resized = resize_image(img, width=800)
    
    # Apply filters
    blurred = apply_filter(img, 'blur', radius=2)
    sharpened = apply_filter(img, 'sharpen')
    
    # Geometric transforms
    rotated = rotate_image(img, angle=45)
    flipped = flip_image(img, direction='horizontal')
    cropped = crop_image(img, box=(100, 100, 500, 500))
    ```
"""

from copy import copy
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import math

from .utils.images import normalize_image_input, normalize_image_output

__all__ = [
    'load_image',
    'resize_image',
    'crop_image',
    'rotate_image',
    'flip_image',
    'apply_filter',
    'apply_mask',
    'apply_transform',
]


def load_image(input_path, output_type='pil'):
    """
    Load an image from various input sources.
    
    This is a convenience wrapper around normalize_image_input that provides
    a simple interface for loading images from files, URLs, bytes, etc.
    
    Args:
        input_path: Image source. Can be:
            - File path (string or Path)
            - URL (http/https)
            - PIL Image object
            - Bytes (raw image data)
            - NumPy array
            - File-like object (BytesIO, etc.)
            - Base64 encoded string
        output_type: Desired output format. Options:
            - 'pil' (default): PIL Image object
            - 'numpy' or 'array': NumPy array
            - 'bytes': Raw bytes
    
    Returns:
        Image in the requested format (default: PIL Image)
    
    Examples:
        ```python
        # Load from file
        img = load_image('photo.png')
        
        # Load from URL
        img = load_image('https://example.com/image.jpg')
        
        # Load as numpy array
        arr = load_image('photo.png', output_type='numpy')
        ```
    """
    return normalize_image_input(input_path, return_type=output_type)


def resize_image(img_input, width=None, height=None, scale=None, 
                 maintain_aspect=True, resample=Image.Resampling.LANCZOS):
    """
    Resize an image to specified dimensions or scale factor.
    
    Supports resizing by explicit dimensions, scaling factor, or fitting
    to a maximum dimension while maintaining aspect ratio.
    
    Args:
        img_input: Image in any supported format (path, PIL Image, bytes, etc.)
        width: Target width in pixels. If only width is provided and 
            maintain_aspect is True, height is calculated automatically.
        height: Target height in pixels. If only height is provided and
            maintain_aspect is True, width is calculated automatically.
        scale: Scale factor (e.g., 0.5 for half size, 2.0 for double).
            Takes precedence over width/height if provided.
        maintain_aspect: If True (default), preserve aspect ratio. When both
            width and height are given, the image fits within those bounds.
        resample: PIL resampling filter. Default is LANCZOS for high quality.
            Options: NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX, HAMMING.
    
    Returns:
        PIL.Image.Image: Resized PIL Image
    
    Examples:
        ```python
        # Resize to specific width, auto-calculate height
        img = resize_image('photo.png', width=800)
        
        # Resize to exact dimensions (may distort)
        img = resize_image('photo.png', width=800, height=600, maintain_aspect=False)
        
        # Scale by factor
        img = resize_image('photo.png', scale=0.5)  # Half size
        
        # Fit within bounds while maintaining aspect ratio
        img = resize_image('photo.png', width=800, height=600)
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    orig_width, orig_height = img.size
    
    # Handle scale factor
    if scale is not None:
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)
        return img.resize((new_width, new_height), resample)
    
    # Need at least one dimension
    if width is None and height is None:
        raise ValueError("Must specify width, height, or scale")
    
    if maintain_aspect:
        # Calculate missing dimension or fit within bounds
        aspect_ratio = orig_width / orig_height
        
        if width is not None and height is not None:
            # Fit within bounds
            target_ratio = width / height
            if aspect_ratio > target_ratio:
                # Image is wider, constrain by width
                new_width = width
                new_height = int(width / aspect_ratio)
            else:
                # Image is taller, constrain by height
                new_height = height
                new_width = int(height * aspect_ratio)
        elif width is not None:
            new_width = width
            new_height = int(width / aspect_ratio)
        else:  # height is not None
            new_height = height
            new_width = int(height * aspect_ratio)
    else:
        # Use explicit dimensions
        new_width = width if width is not None else orig_width
        new_height = height if height is not None else orig_height
    
    return img.resize((new_width, new_height), resample)


def crop_image(img_input, box=None, center=None, size=None):
    """
    Crop an image to a rectangular region.
    
    Supports cropping by explicit box coordinates or by center point and size.
    
    Args:
        img_input: Image in any supported format
        box: Tuple of (left, top, right, bottom) pixel coordinates defining
            the crop region. Origin is top-left corner.
        center: Tuple of (x, y) center point for the crop. Used with size.
        size: Tuple of (width, height) for crop dimensions. Used with center.
            If center is not provided, crops from center of image.
    
    Returns:
        PIL.Image.Image: Cropped PIL Image
    
    Examples:
        ```python
        # Crop by explicit coordinates
        img = crop_image('photo.png', box=(100, 100, 500, 400))
        
        # Crop around center point
        img = crop_image('photo.png', center=(250, 250), size=(200, 200))
        
        # Crop from image center
        img = crop_image('photo.png', size=(400, 300))
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    if box is not None:
        return img.crop(box)
    
    if size is not None:
        crop_width, crop_height = size
        
        if center is not None:
            cx, cy = center
        else:
            # Use image center
            cx = img.width // 2
            cy = img.height // 2
        
        left = max(0, cx - crop_width // 2)
        top = max(0, cy - crop_height // 2)
        right = min(img.width, left + crop_width)
        bottom = min(img.height, top + crop_height)
        
        return img.crop((left, top, right, bottom))
    
    raise ValueError("Must specify either box or size for cropping")


def rotate_image(img_input, angle, expand=True, fill_color=None, center=None,
                 resample=Image.Resampling.BICUBIC):
    """
    Rotate an image by a specified angle.
    
    Args:
        img_input: Image in any supported format
        angle: Rotation angle in degrees. Positive values rotate counter-clockwise.
        expand: If True (default), expand output to hold the entire rotated image.
            If False, maintain original dimensions (corners may be cropped).
        fill_color: Color for areas outside the rotated image. Can be:
            - None (default): Transparent for RGBA, black for RGB
            - RGB tuple: e.g., (255, 255, 255) for white
            - RGBA tuple: e.g., (255, 255, 255, 0) for transparent
        center: Tuple of (x, y) rotation center. Default is image center.
        resample: PIL resampling filter. Default is BICUBIC.
    
    Returns:
        PIL.Image.Image: Rotated PIL Image
    
    Examples:
        ```python
        # Rotate 45 degrees, expanding canvas
        img = rotate_image('photo.png', angle=45)
        
        # Rotate 90 degrees, maintaining size
        img = rotate_image('photo.png', angle=90, expand=False)
        
        # Rotate with white background fill
        img = rotate_image('photo.png', angle=30, fill_color=(255, 255, 255))
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    # Determine fill color based on image mode
    if fill_color is None:
        if img.mode == 'RGBA':
            fill_color = (0, 0, 0, 0)
        elif img.mode == 'RGB':
            fill_color = (0, 0, 0)
        elif img.mode == 'L':
            fill_color = 0
        else:
            fill_color = 0
    
    return img.rotate(
        angle,
        expand=expand,
        fillcolor=fill_color,
        center=center,
        resample=resample
    )


def flip_image(img_input, direction='horizontal'):
    """
    Flip an image horizontally or vertically.
    
    Args:
        img_input: Image in any supported format
        direction: Flip direction. Options:
            - 'horizontal' or 'h': Mirror left-to-right
            - 'vertical' or 'v': Mirror top-to-bottom
            - 'both': Flip in both directions (180 degree rotation)
    
    Returns:
        PIL.Image.Image: Flipped PIL Image
    
    Examples:
        ```python
        # Horizontal flip (mirror)
        img = flip_image('photo.png', direction='horizontal')
        
        # Vertical flip
        img = flip_image('photo.png', direction='vertical')
        
        # Both directions
        img = flip_image('photo.png', direction='both')
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    direction = direction.lower()
    
    if direction in ('horizontal', 'h'):
        return ImageOps.mirror(img)
    elif direction in ('vertical', 'v'):
        return ImageOps.flip(img)
    elif direction == 'both':
        return ImageOps.mirror(ImageOps.flip(img))
    else:
        raise ValueError(
            f"Invalid direction: {direction}. "
            "Use 'horizontal', 'vertical', or 'both'."
        )


def apply_filter(img_input, filter_type, **kwargs):
    """
    Apply a filter effect to an image.
    
    Supports various blur, sharpening, edge detection, and enhancement filters.
    
    Args:
        img_input: Image in any supported format
        filter_type: Type of filter to apply. Options:
            - 'blur': Gaussian blur (radius parameter)
            - 'box_blur': Box blur (radius parameter)
            - 'sharpen': Sharpen edges
            - 'smooth': Smooth/soften image
            - 'detail': Enhance details
            - 'edge': Edge detection
            - 'contour': Contour effect
            - 'emboss': Emboss effect
            - 'brightness': Adjust brightness (factor parameter, 1.0 = no change)
            - 'contrast': Adjust contrast (factor parameter, 1.0 = no change)
            - 'saturation': Adjust color saturation (factor parameter, 1.0 = no change)
            - 'grayscale': Convert to grayscale
            - 'invert': Invert colors
        **kwargs: Filter-specific parameters:
            - radius: Blur radius for blur filters (default: 2)
            - factor: Enhancement factor for brightness/contrast/saturation
    
    Returns:
        PIL.Image.Image: Filtered PIL Image
    
    Examples:
        ```python
        # Apply gaussian blur
        img = apply_filter('photo.png', 'blur', radius=5)
        
        # Sharpen image
        img = apply_filter('photo.png', 'sharpen')
        
        # Increase brightness
        img = apply_filter('photo.png', 'brightness', factor=1.3)
        
        # Convert to grayscale
        img = apply_filter('photo.png', 'grayscale')
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    filter_type = filter_type.lower()
    
    # Blur filters
    if filter_type == 'blur':
        radius = kwargs.get('radius', 2)
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    elif filter_type == 'box_blur':
        radius = kwargs.get('radius', 2)
        return img.filter(ImageFilter.BoxBlur(radius=radius))
    
    # Sharpening and smoothing
    elif filter_type == 'sharpen':
        return img.filter(ImageFilter.SHARPEN)
    
    elif filter_type == 'smooth':
        return img.filter(ImageFilter.SMOOTH)
    
    elif filter_type == 'detail':
        return img.filter(ImageFilter.DETAIL)
    
    # Edge detection effects
    elif filter_type == 'edge':
        return img.filter(ImageFilter.FIND_EDGES)
    
    elif filter_type == 'contour':
        return img.filter(ImageFilter.CONTOUR)
    
    elif filter_type == 'emboss':
        return img.filter(ImageFilter.EMBOSS)
    
    # Enhancement filters
    elif filter_type == 'brightness':
        factor = kwargs.get('factor', 1.0)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)
    
    elif filter_type == 'contrast':
        factor = kwargs.get('factor', 1.0)
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)
    
    elif filter_type == 'saturation':
        factor = kwargs.get('factor', 1.0)
        # Need RGB mode for color enhancement
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)
    
    elif filter_type == 'sharpness':
        factor = kwargs.get('factor', 1.0)
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)
    
    # Color transforms
    elif filter_type == 'grayscale':
        if img.mode == 'RGBA':
            # Preserve alpha channel
            r, g, b, a = img.split()
            gray = img.convert('L')
            return Image.merge('LA', (gray, a)).convert('RGBA')
        return img.convert('L')
    
    elif filter_type == 'invert':
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb = Image.merge('RGB', (r, g, b))
            inverted = ImageOps.invert(rgb)
            return Image.merge('RGBA', (*inverted.split(), a))
        elif img.mode == 'RGB':
            return ImageOps.invert(img)
        else:
            return ImageOps.invert(img.convert('RGB'))
    
    else:
        available = [
            'blur', 'box_blur', 'sharpen', 'smooth', 'detail',
            'edge', 'contour', 'emboss', 'brightness', 'contrast',
            'saturation', 'sharpness', 'grayscale', 'invert'
        ]
        raise ValueError(
            f"Unknown filter type: {filter_type}. "
            f"Available filters: {', '.join(available)}"
        )


def apply_mask(img_input, mask_input, invert=False):
    """
    Apply a mask to an image, controlling transparency.
    
    The mask determines which parts of the image are visible. White areas
    of the mask are fully visible, black areas are transparent.
    
    Args:
        img_input: Image in any supported format
        mask_input: Mask image in any supported format. Should be grayscale
            or will be converted. White = visible, Black = transparent.
        invert: If True, invert the mask (black = visible, white = transparent)
    
    Returns:
        PIL.Image.Image: PIL Image with mask applied as alpha channel (RGBA mode)
    
    Examples:
        ```python
        # Apply a circular mask
        img = apply_mask('photo.png', 'circle_mask.png')
        
        # Apply inverted mask
        img = apply_mask('photo.png', 'mask.png', invert=True)
        ```
    """
    img = normalize_image_input(img_input)
    mask = normalize_image_input(mask_input)
    img = copy(img)
    
    # Convert mask to grayscale
    if mask.mode != 'L':
        mask = mask.convert('L')
    
    # Resize mask to match image if needed
    if mask.size != img.size:
        mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    
    # Invert mask if requested
    if invert:
        mask = ImageOps.invert(mask)
    
    # Ensure image is RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Apply mask as alpha channel
    img.putalpha(mask)
    
    return img


def apply_transform(img_input, transform_type, **kwargs):
    """
    Apply geometric or perspective transforms to an image.
    
    Args:
        img_input: Image in any supported format
        transform_type: Type of transform. Options:
            - 'transpose': Transpose rows and columns (rotate 90 + flip)
            - 'perspective': Apply perspective transform (coefficients parameter)
            - 'affine': Apply affine transform (matrix parameter)
            - 'pad': Add padding around image (padding, fill_color parameters)
            - 'fit': Resize to fit dimensions, adding letterbox if needed
            - 'autocontrast': Automatically adjust contrast (cutoff parameter)
            - 'equalize': Histogram equalization
            - 'posterize': Reduce color depth (bits parameter)
            - 'solarize': Solarize effect (threshold parameter)
        **kwargs: Transform-specific parameters
    
    Returns:
        PIL.Image.Image: Transformed PIL Image
    
    Examples:
        ```python
        # Add padding
        img = apply_transform('photo.png', 'pad', padding=50, fill_color='white')
        
        # Fit to dimensions with letterbox
        img = apply_transform('photo.png', 'fit', size=(800, 600), fill_color='black')
        
        # Auto-adjust contrast
        img = apply_transform('photo.png', 'autocontrast')
        
        # Posterize (reduce colors)
        img = apply_transform('photo.png', 'posterize', bits=4)
        ```
    """
    img = normalize_image_input(img_input)
    img = copy(img)
    
    transform_type = transform_type.lower()
    
    if transform_type == 'transpose':
        return img.transpose(Image.Transpose.TRANSPOSE)
    
    elif transform_type == 'perspective':
        coefficients = kwargs.get('coefficients')
        if coefficients is None:
            raise ValueError("Perspective transform requires 'coefficients' parameter")
        return img.transform(
            img.size,
            Image.Transform.PERSPECTIVE,
            coefficients,
            Image.Resampling.BICUBIC
        )
    
    elif transform_type == 'affine':
        matrix = kwargs.get('matrix')
        if matrix is None:
            raise ValueError("Affine transform requires 'matrix' parameter (6 values)")
        return img.transform(
            img.size,
            Image.Transform.AFFINE,
            matrix,
            Image.Resampling.BICUBIC
        )
    
    elif transform_type == 'pad':
        padding = kwargs.get('padding', 10)
        fill_color = kwargs.get('fill_color', (0, 0, 0, 0) if img.mode == 'RGBA' else (0, 0, 0))
        
        # Handle single padding value or (horizontal, vertical) tuple
        if isinstance(padding, int):
            pad_x, pad_y = padding, padding
        else:
            pad_x, pad_y = padding
        
        new_width = img.width + 2 * pad_x
        new_height = img.height + 2 * pad_y
        
        padded = Image.new(img.mode, (new_width, new_height), fill_color)
        padded.paste(img, (pad_x, pad_y), img if img.mode == 'RGBA' else None)
        return padded
    
    elif transform_type == 'fit':
        size = kwargs.get('size')
        if size is None:
            raise ValueError("Fit transform requires 'size' parameter as (width, height)")
        fill_color = kwargs.get('fill_color', (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 0))
        
        target_width, target_height = size
        
        # Calculate scaling to fit
        scale = min(target_width / img.width, target_height / img.height)
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        
        # Resize image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create canvas and paste centered
        canvas = Image.new(img.mode, size, fill_color)
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        canvas.paste(resized, (paste_x, paste_y), resized if img.mode == 'RGBA' else None)
        return canvas
    
    elif transform_type == 'autocontrast':
        cutoff = kwargs.get('cutoff', 0)
        # AutoContrast doesn't work with RGBA
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb = Image.merge('RGB', (r, g, b))
            adjusted = ImageOps.autocontrast(rgb, cutoff=cutoff)
            return Image.merge('RGBA', (*adjusted.split(), a))
        return ImageOps.autocontrast(img, cutoff=cutoff)
    
    elif transform_type == 'equalize':
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb = Image.merge('RGB', (r, g, b))
            equalized = ImageOps.equalize(rgb)
            return Image.merge('RGBA', (*equalized.split(), a))
        return ImageOps.equalize(img)
    
    elif transform_type == 'posterize':
        bits = kwargs.get('bits', 4)
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb = Image.merge('RGB', (r, g, b))
            posterized = ImageOps.posterize(rgb, bits=bits)
            return Image.merge('RGBA', (*posterized.split(), a))
        elif img.mode == 'RGB':
            return ImageOps.posterize(img, bits=bits)
        else:
            return ImageOps.posterize(img.convert('RGB'), bits=bits)
    
    elif transform_type == 'solarize':
        threshold = kwargs.get('threshold', 128)
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb = Image.merge('RGB', (r, g, b))
            solarized = ImageOps.solarize(rgb, threshold=threshold)
            return Image.merge('RGBA', (*solarized.split(), a))
        elif img.mode == 'RGB':
            return ImageOps.solarize(img, threshold=threshold)
        else:
            return ImageOps.solarize(img.convert('RGB'), threshold=threshold)
    
    else:
        available = [
            'transpose', 'perspective', 'affine', 'pad', 'fit',
            'autocontrast', 'equalize', 'posterize', 'solarize'
        ]
        raise ValueError(
            f"Unknown transform type: {transform_type}. "
            f"Available transforms: {', '.join(available)}"
        )
