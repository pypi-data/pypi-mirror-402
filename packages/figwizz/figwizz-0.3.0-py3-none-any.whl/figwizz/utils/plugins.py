"""
Plugin functions and utilities for FigWizz.

This module provides utilities for checking optional dependencies and handling
plugin functionality. It helps manage the optional dependencies in figwizz,
allowing graceful degradation when certain features are not available.

Example:
    ```python
    from figwizz.utils.plugins import check_optional_import
    
    if check_optional_import('litellm'):
        # Use AI image generation features
        from figwizz import generate_images
    else:
        print("Install litellm for AI features: pip install 'figwizz[genai]'")
    ```
"""

import importlib

def check_optional_import(package_name):
    """
    Check if an optional package is installed.
    
    This utility function attempts to import a package and returns whether
    the import was successful. Useful for checking optional dependencies
    without raising exceptions.
    
    Args:
        package_name (str): Name of the package to check (e.g., 'litellm', 'cairosvg')
    
    Returns:
        bool: True if package is installed and can be imported, False otherwise
    
    Examples:
        ```python
        from figwizz.utils.plugins import check_optional_import
        
        if check_optional_import('litellm'):
            print("LiteLLM is available for AI image generation")
        else:
            print("Install litellm to enable AI features")
        ```
    
    Note:
        This function silently catches ImportError exceptions. It does not
        distinguish between missing packages and packages with import errors.
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False