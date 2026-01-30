"""
Image display and grid layout utilities.

This module provides functions for displaying images in matplotlib-based
grid layouts with customizable configurations.

Example:
    ```python
    from figwizz.display import make_image_grid
    images = ['img1.png', 'img2.png', 'img3.png']
    fig, axes = make_image_grid(images, titles=['A', 'B', 'C'])
    plt.show()
    ```
"""

import matplotlib.pyplot as plt
import numpy as np
from math import ceil
from .utils.images import normalize_image_input

def make_image_grid(images, titles=None, max_cols=None, show_index=False, 
                    figsize=None, title_fontsize=10, show_axes=False):
    """
    Plot a list of images in a grid layout using matplotlib.
    
    Creates a publication-ready grid display of images with optional titles and
    indexing. Automatically calculates optimal grid dimensions and figure size.
    Perfect for comparing multiple images, showing results, or creating figure
    panels for papers and presentations.
    
    Args:
        images (list): List of images in any supported format (paths, PIL Images,
            bytes, numpy arrays, URLs, etc.). All images will be normalized to PIL
            format automatically.
        titles (list[str], optional): List of titles for each image. Length should
            match the number of images. Defaults to None.
        max_cols (int, optional): Maximum number of columns in the grid. If None,
            defaults to min(4, number_of_images). Defaults to None.
        show_index (bool, optional): If True, shows "Image N" label in the corner
            of each subplot. Defaults to False.
        figsize (tuple, optional): Figure size as (width, height) in inches. If None,
            automatically calculated as (max_cols*3, num_rows*3). Defaults to None.
        title_fontsize (int, optional): Font size for image titles in points.
            Defaults to 10.
        show_axes (bool, optional): If True, shows axes with tick marks around each
            image. If False, axes are hidden for a cleaner look. Defaults to False.
    
    Returns:
        tuple: (fig, axes) - Matplotlib Figure and Axes objects that can be further
            customized or saved. Returns (None, None) if images list is empty.
    
    Examples:
        ```python
        from figwizz import make_image_grid
        import matplotlib.pyplot as plt
        
        # Simple grid of images
        images = ['img1.png', 'img2.png', 'img3.png', 'img4.png']
        fig, axes = make_image_grid(images)
        plt.show()
        
        # Grid with titles and custom columns
        fig, axes = make_image_grid(
            images,
            titles=['Original', 'Processed', 'Enhanced', 'Final'],
            max_cols=2
        )
        plt.savefig('comparison.png', dpi=300, bbox_inches='tight')
        
        # Grid with image indices
        fig, axes = make_image_grid(
            images,
            show_index=True,
            figsize=(12, 8)
        )
        
        # Mix different input types
        mixed_images = [
            'local_image.png',
            'https://example.com/image.jpg',
            pil_image_object,
            numpy_array
        ]
        fig, axes = make_image_grid(mixed_images)
        ```
    
    Note:
        - Empty image list returns (None, None)
        - Grid dimensions are automatically calculated for optimal layout
        - Unused subplots (when images don't fill the grid) are hidden
        - All images are normalized to PIL format internally
        - Figure can be saved with plt.savefig() or displayed with plt.show()
        - Axes are hidden by default for cleaner appearance
        - Index labels appear with semi-transparent background for readability
    """
    if not images:
        print("No images to display")
        return None, None
    
    # Normalize all images to PIL format
    images = [normalize_image_input(img) for img in images]
    
    n_images = len(images)
    
    # Calculate grid dimensions
    if max_cols is None:
        n_cols = min(4, n_images)  # Default to 4 columns max
    else:
        n_cols = min(max_cols, n_images)
    
    n_rows = ceil(n_images / n_cols)
    
    # Auto-calculate figure size if not provided
    if figsize is None:
        figsize = (n_cols * 3, n_rows * 3)
    
    # Create figure and axes
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    
    # Handle case of single subplot
    if n_images == 1:
        axes = np.array([axes])
    
    # Flatten axes array for easy iteration
    axes_flat = axes.flatten() if n_images > 1 else axes
    
    # Plot each image
    for idx, (ax, img) in enumerate(zip(axes_flat, images)):
        ax.imshow(img)
        
        if show_index:
            ax.text(0.02, 0.02, f'Image {idx + 1}', fontsize=8, color='black', 
                    backgroundcolor='whitesmoke', ha='center', va='top', alpha=1.0)

        if not show_axes:
            ax.axis('off')
        
        # Add title if provided
        if titles and idx < len(titles):
            ax.set_title(titles[idx], fontsize=title_fontsize)
    
    # Hide any unused subplots
    for idx in range(n_images, len(axes_flat)):
        axes_flat[idx].axis('off')
    
    plt.tight_layout()
    return fig, axes