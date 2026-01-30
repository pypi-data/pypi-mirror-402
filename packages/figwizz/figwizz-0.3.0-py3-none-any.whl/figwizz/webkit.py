"""
Web utilities for URL handling and response processing.

This module provides utilities for working with web resources,
including PDF detection and response object conversion.

Example:
    ```python
    from figwizz.webkit import is_url_a_pdf
    is_pdf = is_url_a_pdf('http://example.com/document.pdf')
    ```
"""

import requests

__all__ = [
    'is_url_a_pdf',
    'convert_response_to_dict',
]

def is_url_a_pdf(url):
    """
    Check if a URL points to a PDF file.
    
    Args:
        url: URL to check
    
    Returns:
        True if the URL likely points to a PDF
    """
    # Check URL extension
    if url.lower().endswith('.pdf'):
        return True
    
    # Check Content-Type header
    try:
        response = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True, timeout=10)
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' in content_type.lower():
            return True
    except:
        pass
    
    return False

def _recursive_convert_to_dict(obj):
    if hasattr(obj, '__dict__'):
        # Recursively convert the __dict__ values
        return {k: _recursive_convert_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: _recursive_convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_recursive_convert_to_dict(item) for item in obj]
    elif isinstance(obj, bytes):
        # Handle bytes objects (common in image responses)
        return obj.decode('utf-8', errors='ignore')
    else:
        # For primitives and other objects, just return as-is
        return obj
    
def _recursive_keep_keys(obj, keep_keys: list[str]):
    if hasattr(obj, '__dict__'):
        return {k: _recursive_keep_keys(v, keep_keys) 
                for k, v in obj.__dict__.items() if k in keep_keys}
    elif isinstance(obj, dict):
        return {k: _recursive_keep_keys(v, keep_keys) 
                for k, v in obj.items() if k in keep_keys}
    elif isinstance(obj, list):
        return [_recursive_keep_keys(item, keep_keys) for item in obj]
    else:
        return obj
    
def convert_response_to_dict(response, keep_keys: list[str]=None):
    """
    Convert a webkit response to a dictionary.
    
    Args:
        response: The response from a web request.
        keep_keys: The keys to keep in the dictionary.
    
    Returns:
        A dictionary of the response.
    """
    
    response_dict = _recursive_convert_to_dict(response)
    
    if keep_keys is not None:
        response_dict = _recursive_keep_keys(response_dict, keep_keys)

    return response_dict