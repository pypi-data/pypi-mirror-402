"""
Figure and image scraping utilities.

This module provides functions for downloading images from various sources including:
- Stock image providers (Pixabay, Unsplash)
- PDF documents (local files or URLs)
- Web pages (extracting embedded images)

Supports automatic metadata collection and handles various image formats including
raster images (PNG, JPEG) and vector graphics (SVG with optional conversion).

Example:
    ```python
    from figwizz import download_stock_images, extract_images_from_pdf
    
    # Download stock images
    images = download_stock_images('mountains', 5, 'output/')
    
    # Extract from PDF
    extract_images_from_pdf('paper.pdf', 'figures/')
    ```
"""

import os, sys, json
import tempfile
import requests
from glob import glob
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

__all__ = [
    'download_stock_images',
    'extract_images_from_pdf',
    'extract_images_from_url',
]

# Stock Image Download Functions ----------------------------------------

def download_stock_images(query, n_images, output_dir, provider='pixabay', api_key=None):
    """
    Download stock images from various providers (Pixabay or Unsplash).
    
    This function provides a unified interface for downloading stock images from
    multiple providers. Each downloaded image is saved with accompanying metadata
    in JSON format.
    
    Args:
        query (str): Search query string to find images
        n_images (int): Number of images to download
        output_dir (str): Directory path where images and metadata will be saved
        provider (str, optional): Image provider to use. Options: 'pixabay' or 'unsplash'.
            Defaults to 'pixabay'.
        api_key (str, optional): API key for the selected provider. If None, attempts to
            read from environment variables (PIXABAY_API_KEY or UNSPLASH_ACCESS_KEY).
            Defaults to None.
    
    Returns:
        list: List of paths to successfully downloaded images
    
    Raises:
        ValueError: If provider is not 'pixabay' or 'unsplash'
        ValueError: If API key is not provided and not found in environment
        RuntimeError: If API request fails or returns unexpected format
    
    Examples:
        ```python
        from figwizz import download_stock_images
        
        # Download 5 images of mountains from Pixabay
        images = download_stock_images('mountains', 5, 'output/mountains')
        
        # Download from Unsplash with explicit API key
        images = download_stock_images(
            'sunset', 10, 'output/sunsets',
            provider='unsplash',
            api_key='your_api_key_here'
        )
        ```
    
    Note:
        - Each image is saved as a .jpg file with a sequential name (e.g., image_1.jpg)
        - Metadata for each image is saved in a corresponding .json file
        - If the output directory already contains images, numbering continues from the last image
        - Requires valid API keys from the respective providers (Pixabay or Unsplash)
    """
    if provider not in ['pixabay', 'unsplash']:
        raise ValueError(f"Invalid provider: {provider}. Must be 'pixabay' or 'unsplash'.")
    
    if provider == 'pixabay':
        return download_pixabay_images(query, n_images, output_dir, api_key)
    elif provider == 'unsplash':
        return download_unsplash_images(query, n_images, output_dir, api_key)
    

# Function to download images from Pixabay
def download_pixabay_images(query, n_images, output_dir, api_key=None):
    """
    Download images from Pixabay API.
    
    This function queries the Pixabay API for images matching the search query
    and downloads high-resolution versions along with comprehensive metadata.
    
    Args:
        query (str): Search query string to find images on Pixabay
        n_images (int): Maximum number of images to download (up to 200 per request)
        output_dir (str): Directory path where images and metadata will be saved
        api_key (str, optional): Pixabay API key. If None, reads from PIXABAY_API_KEY
            environment variable. Defaults to None.
    
    Returns:
        list: List of paths to successfully downloaded images
    
    Raises:
        ValueError: If PIXABAY_API_KEY is not set and api_key is None
        RuntimeError: If API request fails or returns unexpected format
    
    Examples:
        ```python
        from figwizz.scrape import download_pixabay_images
        
        # Download 10 nature images
        images = download_pixabay_images('nature', 10, 'pixabay_images')
        print(f"Downloaded {len(images)} images")
        ```
    
    Note:
        - Images are downloaded in 'largeImageURL' format (typically 1280px width)
        - Metadata includes image URL, dimensions, tags, user info, and more
        - Sequential numbering continues from existing images in the directory
        - Failed downloads are skipped with a warning message
    """
    if api_key is None:
        api_key = os.getenv('PIXABAY_API_KEY')
    if api_key is None:
        raise ValueError(
            "PIXABAY_API_KEY is not set in the environment variables. "
            "Set it in the .env file or pass it as an argument."
        )
        
    url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=photo&per_page=200"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch images from Pixabay: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse Pixabay response: {e}")
    
    if 'hits' not in data:
        raise RuntimeError(f"Unexpected Pixabay API response format: {data}")
    
    images = data['hits'][:n_images]
    
    if not images:
        print(f"Warning: No images found for query '{query}'")
        return []
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    previous_downloads = glob(f"{output_dir}/*.jpg")
    start_index = len(previous_downloads)
    
    saved_images = []

    for index, image in enumerate(images):
        actual_index = start_index + index
        image_url = image['largeImageURL']
        image_id = f"image_{actual_index + 1}"
        
        image_path = f"{output_dir}/{image_id}.jpg"
        json_path = f"{output_dir}/{image_id}.json"
        
        # Download image
        try:
            img_data = requests.get(image_url, timeout=30).content
            with open(image_path, 'wb') as handler:
                handler.write(img_data)
            saved_images.append(image_path)
        except requests.RequestException as e:
            print(f"Warning: Failed to download image {image_url}: {e}")
            continue
        
        # Prepare metadata
        metadata = {
            'Image_URL': image_url, 
            'Image_Path': image_path,
            **image,
        }
        
        # Save metadata as JSON
        with open(json_path, 'w') as json_file:
            json.dump(metadata, json_file, indent=4)
    
    print(f"Successfully downloaded {len(saved_images)} images to {output_dir}")
    return saved_images

# Function to download images from Unsplash
def download_unsplash_images(query, n_images, output_dir, api_key=None):
    """
    Download images from Unsplash API.
    
    This function queries the Unsplash API for images matching the search query
    and downloads full-resolution versions along with photographer attribution
    and comprehensive metadata.
    
    Args:
        query (str): Search query string to find images on Unsplash
        n_images (int): Maximum number of images to download (up to 30 per request)
        output_dir (str): Directory path where images and metadata will be saved
        api_key (str, optional): Unsplash Access Key. If None, reads from
            UNSPLASH_ACCESS_KEY environment variable. Defaults to None.
    
    Returns:
        list: List of paths to successfully downloaded images
    
    Raises:
        ValueError: If UNSPLASH_ACCESS_KEY is not set and api_key is None
        RuntimeError: If API request fails or returns unexpected format
    
    Examples:
        ```python
        from figwizz.scrape import download_unsplash_images
        
        # Download 5 landscape photos
        images = download_unsplash_images('landscape', 5, 'unsplash_images')
        ```
    
    Note:
        - Images are downloaded in 'full' resolution (highest quality available)
        - Metadata includes photographer attribution, description, tags, likes, and more
        - Sequential numbering continues from existing images in the directory
        - Failed downloads are skipped with a warning message
        - Please respect Unsplash's API guidelines and attribution requirements
    """
    if api_key is None:
        api_key = os.getenv('UNSPLASH_ACCESS_KEY')
    if api_key is None:
        raise ValueError(
            "UNSPLASH_ACCESS_KEY is not set in the environment variables. "
            "Set it in the .env file or pass it as an argument."
        )
        
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page={n_images}&client_id={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch images from Unsplash: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse Unsplash response: {e}")
    
    if 'results' not in data:
        raise RuntimeError(f"Unexpected Unsplash API response format: {data}")
    
    images = data['results']

    if not images:
        print(f"Warning: No images found for query '{query}'")
        return []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    previous_downloads = glob(f"{output_dir}/*.jpg")
    start_index = len(previous_downloads)
    
    saved_images = []

    for index, image in enumerate(images):
        actual_index = start_index + index
        image_url = image['urls']['full']
        image_id = f"image_{actual_index + 1}"
        
        image_path = f"{output_dir}/{image_id}.jpg"
        json_path = f"{output_dir}/{image_id}.json"
        
        # Download image
        try:
            img_data = requests.get(image_url, timeout=30).content
            with open(image_path, 'wb') as handler:
                handler.write(img_data)
            saved_images.append(image_path)
        except requests.RequestException as e:
            print(f"Warning: Failed to download image {image_url}: {e}")
            continue
        
        # Prepare metadata
        metadata = {
            'Image_Path': image_path,
            'Image_URL': image_url,
            'User': image['user']['name'],
            'User_Profile': image['user']['links']['html'],
            'Page_URL': image['links']['html'],
            'Description': image.get('description', ''),
            'Alt_Description': image.get('alt_description', ''),
            'Tags': [tag['title'] for tag in image.get('tags', [])],
            'Image_Width': image['width'],
            'Image_Height': image['height'],
            'Likes': image['likes'],
            'Downloads': image.get('downloads', 'N/A')
        }
        
        # Save metadata as JSON
        with open(json_path, 'w') as json_file:
            json.dump(metadata, json_file, indent=4)
    
    print(f"Successfully downloaded {len(saved_images)} images to {output_dir}")
    return saved_images
            
# Source Image Extraction Functions ----------------------------------------

def extract_images_from_pdf(pdf_path, output_dir, min_width=100, min_height=100, name_prefix="figure"):
    """
    Extract images from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        min_width: Minimum image width to keep (filters out small icons)
        min_height: Minimum image height to keep (filters out small icons)
        name_prefix: Prefix for saved image filenames
    
    Returns:
        List of saved image paths
    """
    try:
        import fitz  # PyMuPDF  # type: ignore
    except ImportError:
        print("Error: PyMuPDF is required for PDF extraction.")
        print("Install it with: pip install PyMuPDF")
        sys.exit(1)
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_images = []
    doc = fitz.open(pdf_path)
    
    print(f"Processing PDF: {pdf_path.name}")
    print(f"Total pages: {len(doc)}")
    
    image_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        
        print(f"Page {page_num + 1}: Found {len(image_list)} images")
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            width = base_image["width"]
            height = base_image["height"]
            
            # Filter out small images (likely icons or decorations)
            if width < min_width or height < min_height:
                print(f"  Skipping small image: {width}x{height}")
                continue
            
            image_count += 1
            filename = f"{name_prefix}{str(image_count).zfill(3)}.{image_ext}"
            filepath = output_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            saved_images.append(filepath)
            print(f"  Saved: {filename} ({width}x{height})")
    
    doc.close()
    print(f"\nTotal images extracted: {image_count}")
    return saved_images


def download_pdf_from_url(url):
    """
    Download a PDF from a URL to a temporary file.
    
    Args:
        url: URL of the PDF file
    
    Returns:
        Path to the temporary PDF file
    """
        
    print(f"Downloading PDF from: {url}")
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        response.raise_for_status()
        
        # Verify it's actually a PDF
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
            print(f"Warning: Content-Type is '{content_type}', may not be a PDF")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        temp_file.close()
        print(f"PDF downloaded to temporary file: {temp_file.name}")
        
        return temp_file.name
        
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}")
        sys.exit(1)


def extract_images_from_url(url, output_dir, min_width=100, min_height=100, name_prefix="figure", convert_svg=False, svg_scale=3.0):
    """
    Extract images from a web page URL.
    
    Args:
        url: URL of the web page
        output_dir: Directory to save downloaded images
        min_width: Minimum image width to keep
        min_height: Minimum image height to keep
        name_prefix: Prefix for saved image filenames
        convert_svg: Whether to convert SVG files to PNG
        svg_scale: Scale factor for SVG to PNG conversion (default: 3.0 for high quality)
    
    Returns:
        List of saved image paths
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching URL: {url}")
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all image tags and picture sources
    img_tags = soup.find_all('img')
    picture_tags = soup.find_all('picture')
    
    print(f"Found {len(img_tags)} img tags and {len(picture_tags)} picture tags")
    
    # Collect all image URLs
    all_img_urls = []
    
    # Process img tags
    for idx, img_tag in enumerate(img_tags):
        # Try multiple common attributes for lazy-loaded images
        img_url = None
        
        # Check various attributes in order of preference
        for attr in ['src', 'data-src', 'data-lazy-src', 'data-original']:
            img_url = img_tag.get(attr)
            if img_url:
                break
        
        # If still no URL, try data-srcset
        if not img_url:
            srcset = img_tag.get('data-srcset') or img_tag.get('srcset')
            if srcset:
                # Get the first URL from srcset
                try:
                    img_url = srcset.split(',')[0].strip().split()[0]
                except:
                    pass
        
        # Add to list if valid
        if img_url and not img_url.startswith('data:'):
            all_img_urls.append(img_url)
    
    # Process picture tags (get the source with highest quality)
    for picture_tag in picture_tags:
        sources = picture_tag.find_all('source')
        if sources:
            # Get the last source (usually highest quality)
            source_url = sources[-1].get('srcset', '').split(',')[0].split()[0]
            if source_url and not source_url.startswith('data:'):
                all_img_urls.append(source_url)
    
    print(f"Found {len(all_img_urls)} total image URLs to process")
    
    saved_images = []
    image_count = 0
    
    for idx, img_url in enumerate(all_img_urls):
        if not img_url:
            continue
        
        # Fix backslashes in URLs (common HTML error)
        img_url = img_url.replace('\\', '/')
        
        # Handle relative URLs
        img_url = urljoin(url, img_url)
        
        try:
            print(f"\nDownloading image {idx + 1}/{len(all_img_urls)}: {img_url}")
            img_response = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            img_response.raise_for_status()
            
            # Check if it's an SVG
            is_svg = img_url.lower().endswith('.svg') or 'svg' in img_response.headers.get('Content-Type', '')
            
            if is_svg:
                # Handle SVG files
                if convert_svg:
                    # Convert SVG to PNG
                    image_count += 1
                    filename = f"{name_prefix}{str(image_count).zfill(3)}.png"
                    filepath = output_dir / filename
                    
                    if convert_svg(img_response.content, filepath, scale=svg_scale):
                        saved_images.append(filepath)
                        print(f"  Saved (converted to PNG at {svg_scale}x scale): {filename}")
                    else:
                        # Fallback to saving as SVG if conversion fails
                        filename = f"{name_prefix}{str(image_count).zfill(3)}.svg"
                        filepath = output_dir / filename
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        saved_images.append(filepath)
                        print(f"  Saved (as SVG): {filename}")
                else:
                    # Save SVG as-is
                    image_count += 1
                    filename = f"{name_prefix}{str(image_count).zfill(3)}.svg"
                    filepath = output_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(img_response.content)
                    saved_images.append(filepath)
                    print(f"  Saved: {filename}")
            else:
                # Handle raster images (PNG, JPEG, etc.)
                # Open image to check dimensions
                img = Image.open(BytesIO(img_response.content))
                width, height = img.size
                
                # Filter out small images
                if width < min_width or height < min_height:
                    print(f"  Skipping small image: {width}x{height}")
                    continue
                
                # Determine file extension
                img_format = img.format.lower() if img.format else 'jpg'
                
                # Generate sequential filename
                image_count += 1
                filename = f"{name_prefix}{str(image_count).zfill(3)}.{img_format}"
                filepath = output_dir / filename
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                saved_images.append(filepath)
                print(f"  Saved: {filename} ({width}x{height})")
            
        except Exception as e:
            print(f"  Error downloading {img_url}: {e}")
            continue
    
    print(f"\nTotal images downloaded: {image_count}")
    return saved_images