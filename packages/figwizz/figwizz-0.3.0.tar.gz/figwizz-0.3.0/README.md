# FigWizz <img src="./assets/figwizz-hexicon.png" align="right" width="224px" height="224px" />

Python toolkit for programmatic figure design.

- Easily convert images to different formats
- Stitch keynote / powerpoint slides into auto-cropped images
- Stitch multiple figures to a single PDF
- Scrape images from publication PDFs / websites
- Download stock images from Unsplash / Pixabay
- Batch-generate images from prompts in a single line
- Make image grids, decks, and icons (e.g. hexicons)

## Installation

Basic installation from PyPI:

```bash
pip install figwizz
```

With optional dependencies:
```bash
# For AI image generation
pip install 'figwizz[genai]'

# For PDF processing
pip install 'figwizz[pdf]'

# For SVG support
pip install 'figwizz[svg]'

# For development
pip install 'figwizz[dev]'

# For documentation
pip install 'figwizz[docs]'

# Install all optional dependencies
pip install 'figwizz[genai,pdf,svg]'
```

## Quick Start

### Image Conversion

```python
from figwizz import convert_image

# Convert image format
convert_image("input.png", "jpg")

# Convert with custom settings
convert_image("input.png", "pdf", delete_original=False)
```

### Image Modification

```python
from figwizz import make_image_opaque, ngon_crop

# Make transparent image opaque
make_image_opaque("logo.png", bg_color="white")

# Create hexagonal crop
ngon_crop("photo.jpg", sides=6, crop_size=512)
```

### Presentation Conversion

```python
from figwizz import slides_to_images, images_to_pdf

# Convert PowerPoint/Keynote to images
slides_to_images("presentation.pptx", output_dir="slides/")

# Stitch images into PDF
images_to_pdf("slides/", output_path="presentation.pdf")
```

### Stock Image Download

```python
from figwizz import download_stock_images

# Download from Unsplash or Pixabay
download_stock_images(
    query="nature landscape",
    n_images=10,
    output_dir="stock_images/",
    source="unsplash"  # or "pixabay"
)
```

### AI Image Generation

```python
from figwizz import generate_images

# Generate images from prompts
generate_images(
    prompts=["a serene mountain lake", "abstract geometric art"],
    model="gpt-image-1",
    output_dir="generated/"
)
```

### Image Grids and Display

```python
from figwizz import make_image_grid

# Create and display image grid
images = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
titles = ["Sample 1", "Sample 2", "Sample 3", "Sample 4"]
make_image_grid(images, titles=titles, max_cols=2)
```

### Hexicon Creation

```python
from figwizz.workflows import make_hexicon

# Create hexagonal icon
hexicon = make_hexicon(
    "logo.png",
    size=512,
    border_thickness=10,
    border_color="auto"
)
hexicon.save("hexicon.png")
```

## Command-Line Interface

```bash
# Download stock images
figwizz download-stock "mountain landscape" --n-images 5 --source unsplash

# Generate AI images
figwizz generate "abstract art" --model dall-e-3 --n-images 3

# Convert presentation to images
figwizz slides-to-images presentation.pptx --output-dir slides/

# Extract images from PDF or URL
figwizz extract-images document.pdf --output-dir extracted/
figwizz extract-images https://example.com/page --output-dir scraped/
```

## Documentation

Full documentation available at: [https://colinconwell.github.io/FigWizz](https://colinconwell.github.io/FigWizz)

## Environment Variables

For API-based features, set up a `.env.local` file:

```bash
# For stock image downloads
UNSPLASH_ACCESS_KEY=your_unsplash_key
PIXABAY_API_KEY=your_pixabay_key

# For AI image generation
OPENAI_API_KEY=your_openai_key
```