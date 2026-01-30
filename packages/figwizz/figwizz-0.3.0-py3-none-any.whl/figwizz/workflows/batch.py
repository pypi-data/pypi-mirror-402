"""
Batch processing utilities for multiple files.

This module provides convenient functions for applying operations to entire
directories of images, including:
- Format conversion (batch_convert_images)
- Hexicon creation (batch_create_hexicons)
- Custom processing functions (batch_process_images)

All batch operations include progress bars and error handling for robust
processing of large image collections.

Example:
    ```python
    from figwizz.workflows.batch import batch_convert_images, batch_create_hexicons
    
    # Convert all images to PNG
    batch_convert_images('input/', 'png', output_dir='output/')
    
    # Create hexicons for all logos
    batch_create_hexicons('logos/', 'hexicons/', border_size=5)
    ```
"""

from pathlib import Path
from tqdm import tqdm


def batch_convert_images(input_dir, target_format, output_dir=None, **kwargs):
    """
    Convert all images in a directory to a target format.
    
    Processes all supported image files in the input directory, converting
    them to the specified format. Displays progress with a progress bar.
    
    Args:
        input_dir (str): Directory containing images to convert
        target_format (str): Target format (e.g., 'jpg', 'png', 'webp')
        output_dir (str, optional): Output directory for converted images.
            If None, uses input_dir. Defaults to None.
        **kwargs: Additional arguments passed to convert_image function
            (e.g., delete_original=False)
    
    Returns:
        list: List of paths to successfully converted images
    
    Examples:
        ```python
        from figwizz.workflows.batch import batch_convert_images
        
        # Convert all images to JPEG
        converted = batch_convert_images('input_images/', 'jpg')
        
        # Convert to PNG in a different directory
        converted = batch_convert_images(
            'input_images/', 
            'png', 
            output_dir='output_images/'
        )
        ```
    
    Note:
        - Supports common image formats: PNG, JPG, JPEG, GIF, BMP, TIFF
        - Failed conversions are skipped with error messages
        - Progress is displayed via tqdm progress bar
        - Output directory is created if it doesn't exist
    """
    from ..convert import convert_image
    
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(ext))
    
    converted = []
    for img_path in tqdm(image_files, desc="Converting images"):
        try:
            result = convert_image(str(img_path), target_format, **kwargs)
            converted.append(result)
        except Exception as e:
            print(f"Failed to convert {img_path}: {e}")
    
    return converted


def batch_create_hexicons(input_dir, output_dir, **kwargs):
    """
    Create hexicons for all images in a directory.
    
    Processes all images in the input directory, creating tidyverse-style
    hexagonal icons with optional borders and customizations.
    
    Args:
        input_dir (str): Directory containing source images
        output_dir (str): Output directory for hexicons
        **kwargs: Additional arguments passed to make_hexicon function.
            Common options include:
            - border_size (int): Width of border in pixels
            - border_color (str): Border color ('auto', hex, RGB tuple, or name)
            - padding (int): Padding around image content
            - background_color (str): Background color inside hexagon
    
    Returns:
        list: List of paths to successfully created hexicons
    
    Examples:
        ```python
        from figwizz.workflows.batch import batch_create_hexicons
        
        # Create simple hexicons
        hexicons = batch_create_hexicons('logos/', 'hexicons/')
        
        # Create hexicons with red border and padding
        hexicons = batch_create_hexicons(
            'logos/', 
            'hexicons/',
            border_size=5,
            border_color='red',
            padding=20
        )
        ```
    
    Note:
        - Supports PNG, JPG, and JPEG input formats
        - Output files maintain original filenames
        - Failed conversions are skipped with error messages
        - Progress is displayed via tqdm progress bar
    """
    from ..workflows.icons import make_hexicon
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(ext))
    
    hexicons = []
    for img_path in tqdm(image_files, desc="Creating hexicons"):
        try:
            hexicon = make_hexicon(str(img_path), **kwargs)
            output_file = output_path / img_path.name
            hexicon.save(output_file)
            hexicons.append(str(output_file))
        except Exception as e:
            print(f"Failed to create hexicon for {img_path}: {e}")
    
    return hexicons


def batch_process_images(input_dir, process_func, output_dir=None, **kwargs):
    """
    Apply a custom processing function to all images in a directory.
    
    This is a flexible utility function that applies any user-defined image
    processing function to all images in a directory. The processing function
    should accept a PIL Image and return a processed PIL Image.
    
    Args:
        input_dir (str): Directory containing images to process
        process_func (callable): Function that takes a PIL Image object and
            returns a processed PIL Image object. Should have signature:
            `func(image, **kwargs) -> PIL.Image`
        output_dir (str, optional): Output directory for processed images.
            If None, uses input_dir (overwrites originals). Defaults to None.
        **kwargs: Additional keyword arguments passed to process_func
    
    Returns:
        list: List of paths to successfully processed images
    
    Examples:
        ```python
        from figwizz.workflows.batch import batch_process_images
        from PIL import ImageFilter
        
        # Define custom processing function
        def apply_blur(img, radius=2):
            return img.filter(ImageFilter.GaussianBlur(radius))
        
        # Process all images
        processed = batch_process_images(
            'input_images/', 
            apply_blur,
            output_dir='blurred_images/',
            radius=5
        )
        
        # Example with rotation
        def rotate_image(img, angle=90):
            return img.rotate(angle, expand=True)
        
        rotated = batch_process_images(
            'input_images/',
            rotate_image,
            output_dir='rotated/',
            angle=45
        )
        ```
    
    Note:
        - Supports PNG, JPG, and JPEG input formats
        - Input images are automatically normalized to PIL format
        - Output images are automatically saved in original format
        - Failed operations are skipped with error messages
        - Progress is displayed via tqdm progress bar
        - Use with caution when output_dir is None (overwrites originals)
    """
    from ..utils.images import normalize_image_input, save_image
    
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(ext))
    
    processed = []
    for img_path in tqdm(image_files, desc="Processing images"):
        try:
            img = normalize_image_input(str(img_path))
            result_img = process_func(img, **kwargs)
            output_file = output_path / img_path.name
            save_image(result_img, str(output_file))
            processed.append(str(output_file))
        except Exception as e:
            print(f"Failed to process {img_path}: {e}")
    
    return processed

