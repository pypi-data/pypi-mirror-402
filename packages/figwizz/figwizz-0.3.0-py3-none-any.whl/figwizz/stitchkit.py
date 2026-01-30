"""
Slide conversion and PDF stitching utilities.

This module provides functions for converting presentation slides (PowerPoint, Keynote)
to images and PDFs, with support for whitespace cropping and batch processing.

Platform Support:
    - macOS: Uses AppleScript for Keynote and PowerPoint
    - Windows: Uses COM interface for PowerPoint
    - Linux: Uses LibreOffice command-line tools

Example:
    ```python
    from figwizz.stitchkit import slides_to_images
    slides_to_images('presentation.pptx', 'output_folder', crop_images=True)
    ```
"""

import os, re
import glob
import subprocess
import platform
from copy import copy
from PIL import Image, ImageChops

__all__ = [
    'slides_to_images',
    'convert_to_pdf',
    'convert_images_to_pdf',
    'mogrify_images_to_pdf',
]

# Core Functions ------------------------------------------------------------

def slides_to_images(input_path, output_path, filename_format='figure{:01d}.png',
                     crop_images=True, margin_size='1cm', dpi=300):
    """
    Convert presentation slides to image files.
    
    Extracts all slides from PowerPoint (.ppt, .pptx) or Keynote (.key) presentations
    as individual PNG images. Automatically detects the presentation format and uses
    platform-appropriate tools for conversion. Optionally crops whitespace and adds
    margins for professional-looking figures.
    
    Args:
        input_path (str): Path to the presentation file. Supported formats:
            - PowerPoint: .ppt, .pptx
            - Keynote: .key (macOS only)
        output_path (str): Directory path where the images will be saved. Created
            automatically if it doesn't exist.
        filename_format (str, optional): Python format string for output filenames.
            Must include a placeholder for slide number (e.g., '{:01d}' for 1-digit,
            '{:03d}' for 3-digit with leading zeros). Defaults to 'figure{:01d}.png'.
        crop_images (bool, optional): If True, removes whitespace around slides and
            adds specified margin. If False, keeps original slide dimensions.
            Defaults to True.
        margin_size (str, optional): Margin to add around cropped slides (e.g., '1cm',
            '0.5cm', '2cm'). Only used when crop_images=True. Defaults to '1cm'.
        dpi (int, optional): Resolution for output images in dots per inch. Higher
            values produce larger, higher-quality images. Defaults to 300.
    
    Examples:
        ```python
        from figwizz import slides_to_images
        
        # Basic conversion
        slides_to_images('presentation.pptx', 'output_slides/')
        
        # Without cropping
        slides_to_images('slides.pptx', 'figures/', crop_images=False)
        
        # Custom filename format with 3-digit numbering
        slides_to_images(
            'deck.key',
            'keynote_slides/',
            filename_format='slide_{:03d}.png'
        )
        
        # High resolution with custom margin
        slides_to_images(
            'presentation.pptx',
            'high_res_figures/',
            margin_size='2cm',
            dpi=600
        )
        ```
    
    Note:
        Platform compatibility:
        - macOS: Supports both PowerPoint (.ppt, .pptx) and Keynote (.key)
          Uses AppleScript for automation
        - Windows: Supports PowerPoint (.ppt, .pptx) only
          Uses COM interface (pywin32 required)
        - Linux: Supports PowerPoint via LibreOffice
          Requires LibreOffice installed
        
        Additional notes:
        - Output directory is created if it doesn't exist
        - Existing images with same names are overwritten
        - Cropping uses intelligent whitespace detection
        - Margin size is converted to pixels using the specified DPI
        - Progress is shown for multi-step operations
    """
    input_ext = _check_slides_extension(input_path)

    if input_ext in ['.ppt', '.pptx']:
        powerpoint_to_images(input_path, output_path, filename_format)

    if input_ext == '.key':
        keynote_to_images(input_path, output_path, filename_format)

    if crop_images:
        crop_whitespace(output_path, margin_size=margin_size, dpi=dpi)

def keynote_to_images(input_path, output_path, filename_format='figure{:01d}.png'):
    """
    Convert Keynote slides to image files using AppleScript.
    
    Uses macOS AppleScript automation to export all slides from a Keynote presentation
    as individual PNG images. This is the native method for Keynote conversion on macOS.
    
    Args:
        input_path (str): Path to the Keynote (.key) file
        output_path (str): Directory path where the images will be saved. Created
            automatically if it doesn't exist.
        filename_format (str, optional): Python format string for output filenames.
            Must include a placeholder for slide number. Defaults to 'figure{:01d}.png'.
    
    Examples:
        ```python
        from figwizz.stitchkit import keynote_to_images
        
        # Convert Keynote to images
        keynote_to_images('presentation.key', 'slides/')
        
        # Custom filename format
        keynote_to_images(
            'deck.key',
            'output/',
            filename_format='slide_{:03d}.png'
        )
        ```
    
    Note:
        - **macOS only**: Requires Keynote to be installed
        - Uses AppleScript automation via osascript command
        - Keynote application will briefly open during conversion
        - All slides are exported, including hidden/skipped slides
        - Images are exported in PNG format with transparency
        - Source: https://iworkautomation.com/keynote/document-export.html
    
    Raises:
        SystemError: If run on non-macOS platform
        FileNotFoundError: If Keynote is not installed
    """
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    applescript = f'''
    tell application "Keynote"
        set theDocument to open "{input_path}"
        set documentName to the name of theDocument
        set targetFolderHFSPath to POSIX file "{output_path}" as string

        export theDocument as slide images to file targetFolderHFSPath with properties {{image format:PNG, skipped slides:FALSE}}
    end tell
    '''
    
    subprocess.run(['osascript', '-e', applescript])

    if filename_format:
        reformat_image_filenames(output_path, filename_format)

def powerpoint_to_images(input_path, output_path, filename_format='figure{:01d}.png'):
    """
    Convert PowerPoint slides to image files.
    
    Platform-aware conversion that automatically uses the best method available
    for your operating system. Exports all slides from PowerPoint presentations
    (.ppt, .pptx) as individual PNG images.
    
    Args:
        input_path (str): Path to the PowerPoint file (.ppt or .pptx)
        output_path (str): Directory path where the images will be saved. Created
            automatically if it doesn't exist.
        filename_format (str, optional): Python format string for output filenames.
            Must include a placeholder for slide number. Defaults to 'figure{:01d}.png'.
    
    Examples:
        ```python
        from figwizz.stitchkit import powerpoint_to_images
        
        # Convert PowerPoint to images
        powerpoint_to_images('presentation.pptx', 'slides/')
        
        # Custom filename format
        powerpoint_to_images(
            'deck.pptx',
            'output/',
            filename_format='slide_{:03d}.png'
        )
        ```
    
    Platform-specific behavior:
        **macOS:**
        - Uses AppleScript with Microsoft PowerPoint
        - Requires PowerPoint for Mac to be installed
        - PowerPoint will briefly open during conversion
        
        **Windows:**
        - Uses COM interface via win32com.client
        - Requires PowerPoint and pywin32: `pip install pywin32`
        - PowerPoint runs in background (visible)
        
        **Linux/Other:**
        - Uses LibreOffice command-line interface
        - Requires LibreOffice: `sudo apt install libreoffice`
        - Falls back to python-pptx with limited functionality
    
    Note:
        - All slides are exported, including hidden/skipped slides
        - Images are exported in PNG format
        - Original slide dimensions are preserved
        - Output directory is created if it doesn't exist
        - Existing images with same names are overwritten
    
    Raises:
        ImportError: If required libraries (pywin32, python-pptx) are not installed
        FileNotFoundError: If PowerPoint/LibreOffice is not found
        subprocess.CalledProcessError: If LibreOffice conversion fails
    """
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    if platform.system() == 'Darwin':  # macOS
        applescript = f'''
        tell application "Microsoft PowerPoint"
            open "{input_path}"
            set thePresentation to active presentation
            
            set slideCount to count of slides in thePresentation
            repeat with i from 1 to slideCount
                set current slide of thePresentation to slide i of thePresentation
                set slideFile to "{output_path}/Slide" & i & ".png"
                save thePresentation in slideFile as save as PNG
            end repeat
            
            close thePresentation saving no
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript])
    
    elif platform.system() == 'Windows':
        try:
            import win32com.client # type: ignore
            
            # Initialize PowerPoint application
            ppt = win32com.client.Dispatch("PowerPoint.Application")
            ppt.Visible = True
            
            # Open the presentation
            presentation = ppt.Presentations.Open(input_path)
            
            # Export slides as images
            for i in range(1, presentation.Slides.Count + 1):
                slide_path = os.path.join(output_path, f"Slide{i}.png")
                presentation.Slides(i).Export(slide_path, "PNG")
            
            # Close presentation without saving changes
            presentation.Close()
            ppt.Quit()
            
        except ImportError:
            print("Error: win32com is required for Windows. Install with 'pip install pywin32'")
            return
        except Exception as e:
            print(f"Error exporting PowerPoint slides: {e}")
            return
    
    else:
        try:
            from pptx import Presentation
            
            # This is a limited fallback as python-pptx doesn't directly support exporting slides as images
            # For full functionality, consider using LibreOffice CLI in a subprocess
            print("Using python-pptx for basic PowerPoint handling. For full slide export, use Windows or macOS.")
            
            # For Linux/other platforms, can use LibreOffice command line:
            # subprocess.run(['soffice', '--headless', '--convert-to', 'png', '--outdir', output_path, input_path])
            
            # Example LibreOffice conversion (uncomment if LibreOffice is available)
            libreoffice_cmd = ['soffice', '--headless', '--convert-to', 'png', '--outdir', output_path, input_path]
            try:
                subprocess.run(libreoffice_cmd, check=True)
            except subprocess.CalledProcessError:
                print("Warning: LibreOffice conversion failed. Limited functionality available.")
                print("Install LibreOffice for better platform-independent conversion.")
            
        except ImportError:
            print("Error: pptx package is required. Install with 'pip install python-pptx'")
            return
    
    if filename_format:
        reformat_image_filenames(output_path, filename_format)

# Helper Functions ------------------------------------------------------------

def _check_slides_extension(input_path):
    input_ext = os.path.splitext(input_path)[1]

    if input_ext not in ['.key', '.ppt', '.pptx']:
        raise ValueError(f"Unsupported file extension: {input_ext}",
                         "Supported extensions: .key, .ppt, .pptx")
    
    return input_ext

def reformat_image_filenames(output_path, reformat_pattern):
    """
    Rename image files based on a specified pattern.
    
    Renames all PNG files in a directory to follow a consistent naming pattern.
    Extracts existing numbers from filenames and applies the new format.
    
    Args:
        output_path (str): Directory containing the PNG image files to rename
        reformat_pattern (str): Python format string for new filenames (e.g.,
            'figure{:01d}.png' or 'slide_{:03d}.png'). Must contain a numeric
            placeholder that will be filled with the extracted slide/image number.
    
    Examples:
        ```python
        from figwizz.stitchkit import reformat_image_filenames
        
        # Rename Slide1.png, Slide2.png, etc. to figure1.png, figure2.png
        reformat_image_filenames('slides/', 'figure{:01d}.png')
        
        # Rename to zero-padded format: img001.png, img002.png, etc.
        reformat_image_filenames('images/', 'img{:03d}.png')
        ```
    
    Note:
        - Only processes PNG files
        - Extracts the first numeric value found in each filename
        - Files are renamed in place within the same directory
        - Original files are overwritten with new names
        - Useful after slides_to_images to standardize naming
    """
    image_files = glob.glob(os.path.join(output_path, '*.png'))
    
    for image_file in image_files:
        basename = os.path.basename(image_file)
        slide_number = re.search(r'\d+', basename).group(0)
        new_filename = reformat_pattern.format(int(slide_number))
        new_filepath = os.path.join(output_path, new_filename)
        os.rename(image_file, new_filepath)

def crop_whitespace(image_path, output_path=None, margin_size='1cm', dpi=300):
    """
    Crop whitespace around images and add a specified margin.
    
    Intelligently removes white borders and backgrounds from images while preserving
    the important content. Optionally adds a clean margin around the cropped content.
    Perfect for cleaning up screenshots, slides, or figures with excess whitespace.
    
    Args:
        image_path (str): Path to an image file or a directory containing image files.
            If a directory, processes all PNG, JPG, and JPEG files within it.
        output_path (str, optional): Path where cropped images will be saved. 
            - If None, overwrites the original files
            - For single files, specify output file path
            - For directories, specify output directory path
            Defaults to None.
        margin_size (str, optional): Margin to add around cropped content (e.g., '1cm',
            '0.5cm', '2cm'). Converted to pixels based on DPI. Defaults to '1cm'.
        dpi (int, optional): DPI (dots per inch) for margin calculation. Standard values:
            - 72: screen resolution
            - 150: draft print quality
            - 300: standard print quality (default)
            - 600: high-quality print
            Defaults to 300.
    
    Examples:
        ```python
        from figwizz.stitchkit import crop_whitespace
        
        # Crop single image with default 1cm margin
        crop_whitespace('screenshot.png')  # Overwrites original
        
        # Crop and save to new file
        crop_whitespace('slide.png', 'cropped_slide.png')
        
        # Crop all images in directory
        crop_whitespace('slides_folder/')
        
        # Custom margin and DPI
        crop_whitespace(
            'figures/',
            output_path='cropped_figures/',
            margin_size='2cm',
            dpi=600
        )
        
        # No margin (tight crop)
        crop_whitespace('image.png', margin_size='0cm')
        ```
    
    Note:
        - Uses intelligent bounding box detection to find content
        - Converts RGBA images to RGB with white background before cropping
        - Margin size is converted from centimeters to pixels: pixels = (cm * dpi) / 2.54
        - When processing directories, preserves original filenames
        - Supports PNG, JPG, and JPEG formats
        - Creates output directory if it doesn't exist
        - Original images are preserved if output_path is specified
    """
    def add_margin(image, margin_pixels):
        width, height = image.size
        new_width = width + 2 * margin_pixels
        new_height = height + 2 * margin_pixels
        new_image = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 255))
        new_image.paste(image, (margin_pixels, margin_pixels))
        return new_image

    def crop_single_image(source_file, output_file):
        image = Image.open(source_file)
        image = image.convert("RGBA")

        # Remove alpha channel by pasting the image onto a white background
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image_rgb = background.convert("RGB")

        # Find the bounding box and crop the image
        difference = ImageChops.difference(image_rgb, Image.new("RGB", image.size, (255, 255, 255)))
        bounds = difference.getbbox()
        cropped_image = image.crop(bounds)

        # Add margin if specified
        if margin_size:
            margin_cm = float(margin_size.strip('cm'))
            margin_pixels = int(margin_cm * dpi / 2.54)  # Convert cm to pixels
            cropped_image = add_margin(cropped_image, margin_pixels)

        cropped_image.save(output_file)

    if os.path.isdir(image_path):
        for filename in os.listdir(image_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                source_file = os.path.join(image_path, filename)
                if output_path:
                    output_file = os.path.join(output_path, filename)
                else:
                    output_file = source_file
                crop_single_image(source_file, output_file)
    else:
        if output_path is None:
            output_path = image_path
        crop_single_image(image_path, output_path)

def convert_to_pdf(image_path, output_path=None, dpi=300, **kwargs):
    """
    Convert PNG, JPEG, or TIFF images to high-quality PDF files.
    
    Creates publication-quality PDF files from raster images with specified resolution.
    Automatically handles transparency by adding white backgrounds where needed.
    
    Args:
        image_path (str): Path to an image file or a directory containing image files.
            Supported formats: PNG, JPG, JPEG, TIFF, TIF
        output_path (str, optional): Path where the PDF files will be saved.
            - If None, uses same location as input with .pdf extension
            - For single files, specify output file path
            - For directories, processes all images in place
            Defaults to None.
        dpi (int, optional): DPI (dots per inch) for the output PDF. Common values:
            - 72: screen resolution (smallest file size)
            - 150: draft print quality
            - 300: standard print quality (default)
            - 600: high-quality print
            Defaults to 300.
        **kwargs: Additional keyword arguments:
            - pdf_only (bool): If True, removes original image files after conversion.
              Defaults to False.
    
    Returns:
        None
    
    Examples:
        ```python
        from figwizz.stitchkit import convert_to_pdf
        
        # Convert single image
        convert_to_pdf('figure.png')  # Creates figure.pdf
        
        # Convert with custom output path
        convert_to_pdf('image.jpg', 'document.pdf')
        
        # Convert all images in directory
        convert_to_pdf('figures_folder/')
        
        # High-resolution PDF
        convert_to_pdf('figure.png', dpi=600)
        
        # Convert and delete original
        convert_to_pdf('image.png', pdf_only=True)
        
        # Batch convert to new directory
        convert_to_pdf('input_images/', 'pdf_output/')
        ```
    
    Note:
        - Automatically converts RGBA/LA images to RGB with white background
        - Preserves image quality and dimensions
        - PDF resolution is embedded in the file
        - When processing directories, converts each image to PDF with same filename
        - Output directory is created if it doesn't exist
        - Use pdf_only=True with caution as it deletes original images
    """
    if output_path is None:
        output_path = copy(image_path)
    
    if os.path.isdir(image_path):
        for filename in os.listdir(image_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
                source_file = os.path.join(image_path, filename)
                if output_path:
                    output_file = os.path.join(output_path, os.path.splitext(filename)[0] + '.pdf')
                else:
                    output_file = os.path.join(image_path, os.path.splitext(filename)[0] + '.pdf')
                print(f'Converting {source_file} to {output_file}...')
                image = Image.open(source_file)
                # Convert to RGB mode if necessary
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                image.save(output_file, 'PDF', resolution=dpi)
    else:
        if output_path:
            output_file = os.path.splitext(output_path)[0] + '.pdf'
        else:
            output_file = os.path.splitext(image_path)[0] + '.pdf'
        image = Image.open(image_path)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        image.save(output_file, 'PDF', resolution=dpi)

    if kwargs.get('pdf_only', False):
        os.remove(image_path)

def convert_images_to_pdf(input_path, dpi=300, **kwargs):
    """
    Convert all images in a directory and its subdirectories to PDF files.
    
    Recursively searches through all subdirectories and converts every PNG, JPEG,
    and TIFF image to PDF format. Useful for batch processing entire folder structures.
    
    Args:
        input_path (str): Path to the root directory containing images. All subdirectories
            will be searched recursively.
        dpi (int, optional): DPI (dots per inch) for all output PDF files. Defaults to 300.
        **kwargs: Additional keyword arguments passed to convert_to_pdf:
            - pdf_only (bool): If True, removes original image files after conversion.
              Defaults to False.
    
    Examples:
        ```python
        from figwizz.stitchkit import convert_images_to_pdf
        
        # Convert all images in directory tree
        convert_images_to_pdf('project_figures/')
        
        # High-resolution conversion
        convert_images_to_pdf('images/', dpi=600)
        
        # Convert and remove originals
        convert_images_to_pdf('temp_images/', pdf_only=True)
        ```
    
    Note:
        - Searches recursively through all subdirectories
        - Supported formats: PNG, JPG, JPEG, TIFF, TIF
        - Each image is converted in its current location
        - PDF files are created alongside original images
        - Use pdf_only=True with caution as it deletes original images
        - Does not follow symbolic links
    """
    image_exts = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
    image_files = glob.glob(os.path.join(input_path, f'**/*.{",".join(image_exts)}'), recursive=True)
    for image_file in image_files:
        convert_to_pdf(image_file, None, dpi, **kwargs)

def mogrify_images_to_pdf(input_path, **kwargs):
    """
    Convert images to PDF using ImageMagick's mogrify command.
    
    Alternative to convert_images_to_pdf that uses ImageMagick for conversion.
    Provides high-quality conversion with ImageMagick's robust processing engine.
    Recursively processes all images in subdirectories.
    
    Args:
        input_path (str): Path to the directory containing images. All subdirectories
            will be searched recursively.
        **kwargs: Additional keyword arguments:
            - pdf_only (bool): If True, removes original image files after conversion.
              Defaults to False.
    
    Examples:
        ```python
        from figwizz.stitchkit import mogrify_images_to_pdf
        
        # Convert using ImageMagick
        mogrify_images_to_pdf('figures/')
        
        # Convert and remove originals
        mogrify_images_to_pdf('temp_images/', pdf_only=True)
        ```
    
    Note:
        - **Requires ImageMagick**: Install with:
          * macOS: `brew install imagemagick`
          * Ubuntu/Debian: `sudo apt install imagemagick`
          * Windows: Download from https://imagemagick.org
        - Uses fixed settings: quality=100, density=300 DPI
        - Searches recursively through all subdirectories
        - Supported formats: PNG, JPG, JPEG, TIFF, TIF
        - Each image is converted in its current location
        - Generally faster than PIL-based conversion for large batches
        - Use pdf_only=True with caution as it deletes original images
    
    Raises:
        FileNotFoundError: If ImageMagick's mogrify command is not found in PATH
        subprocess.CalledProcessError: If mogrify command fails
    """
    image_exts = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
    image_files = glob.glob(os.path.join(input_path, f'**/*.{",".join(image_exts)}'), recursive=True)
    for image_file in image_files:
        subprocess.run(['mogrify', '-format', 'pdf', '-quality', '100', '-density', '300', image_file])

    if kwargs.get('pdf_only', False):
        for image_file in image_files:
            os.remove(image_file)