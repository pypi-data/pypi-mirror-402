"""
Generative AI workflow functions.

This module provides utilities for working with generative AI image models,
including response parsing, serialization, and image extraction from various
API response formats.

Key features:
- Extract images from AI model responses (base64 or URL)
- Convert response objects to JSON-serializable dictionaries
- Handle multiple AI provider response formats

These functions are primarily used internally by the generate module but can
be used directly for custom AI image generation workflows.

Example:
    ```python
    from figwizz.workflows.genai import extract_image_from_genai_response
    
    # Extract image from API response
    image_bytes, metadata = extract_image_from_genai_response(response)
    
    # Save to file
    with open('output.png', 'wb') as f:
        f.write(image_bytes)
    ```
"""

import requests
import base64
from typing import Union, Any, Dict

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
    Convert a generative AI response to a dictionary.
    
    Recursively converts response objects (including nested objects) to
    dictionaries, handling special types like bytes. Optionally filters
    to keep only specified keys.
    
    Args:
        response: The response from a generative AI model (can be a custom object,
            dict, list, or primitive type)
        keep_keys (list[str], optional): List of key names to retain in the output.
            If None, all keys are kept. Defaults to None.
    
    Returns:
        dict: A JSON-serializable dictionary representation of the response
    
    Examples:
        ```python
        from figwizz.workflows.genai import convert_response_to_dict
        
        # Convert full response
        response_dict = convert_response_to_dict(api_response)
        
        # Keep only specific keys
        filtered = convert_response_to_dict(api_response, keep_keys=['data', 'model'])
        ```
    
    Note:
        - Bytes objects are decoded to UTF-8 strings (with error handling)
        - Objects with __dict__ are recursively converted
        - Useful for serializing API responses to JSON
    """
    
    response_dict = _recursive_convert_to_dict(response)
    
    if keep_keys is not None:
        response_dict = _recursive_keep_keys(response_dict, keep_keys)

    return response_dict

def make_json_serializable(obj: Any) -> Any:
    """
    Convert an object to a JSON-serializable format.
    
    Handles various non-serializable types including litellm response objects,
    datetime objects, and custom classes with __dict__. This is a convenience
    wrapper around convert_response_to_dict.
    
    Args:
        obj (Any): Object to convert (can be any type)
    
    Returns:
        Any: JSON-serializable representation of the object
    
    Examples:
        ```python
        from figwizz.workflows.genai import make_json_serializable
        import json
        
        # Convert and save API response
        response = api_call()
        serializable = make_json_serializable(response)
        with open('response.json', 'w') as f:
            json.dump(serializable, f, indent=2)
        ```
    
    Note:
        - Particularly useful for saving API responses to JSON files
        - Handles nested objects and complex data structures
        - Bytes are decoded to strings with UTF-8
    """
    return convert_response_to_dict(obj)


def extract_image_from_genai_response(response: Any) -> tuple[bytes, Dict[str, Any]]:
    """
    Extract image data from various generative AI response formats.
    
    Intelligently handles multiple response structures from different AI providers,
    automatically detecting and extracting image data from various formats including
    base64 encoded strings and URLs.
    
    Supports multiple response structures:
    - response['data'][0] with 'b64_json' or 'url'
    - response['data'][0] with 'image' key containing base64
    - response with direct 'b64_json', 'url', or 'image' keys
    - response['choices'][0]['image'] (for some API formats)
    
    Args:
        response (Any): Response object from a generative AI API call. Can be a
            dictionary, custom object, or any structure containing image data.
    
    Returns:
        tuple[bytes, dict]: A tuple containing:
            - bytes: Raw image data ready to be saved or processed
            - dict: Metadata about the extraction including:
                - 'extraction_method': Which method was used to extract the image
                - 'original_format': Original format ('base64' or 'url')
                - 'source_url': Original URL if image was downloaded (optional)
    
    Raises:
        ValueError: If no supported image format is found in the response,
            with detailed information about what keys were found
    
    Examples:
        ```python
        from figwizz.workflows.genai import extract_image_from_genai_response
        from PIL import Image
        from io import BytesIO
        
        # Extract from API response
        image_bytes, metadata = extract_image_from_genai_response(api_response)
        
        # Save to file
        with open('generated.png', 'wb') as f:
            f.write(image_bytes)
        
        # Or open with PIL
        image = Image.open(BytesIO(image_bytes))
        image.show()
        
        # Check extraction metadata
        print(f"Extracted via: {metadata['extraction_method']}")
        print(f"Format was: {metadata['original_format']}")
        ```
    
    Note:
        - Automatically handles data URI schemes (data:image/...)
        - Downloads images from URLs when necessary
        - Provides detailed error messages when extraction fails
        - Works with most major generative AI providers (OpenAI, etc.)
    """
    metadata = {'extraction_method': None, 'original_format': None}
    
    # Try to convert response to dict if it's an object
    if hasattr(response, '__dict__') and not isinstance(response, dict):
        response_dict = make_json_serializable(response)
    else:
        response_dict = response
    
    # Method 1: Standard format with data array
    if isinstance(response_dict, dict) and 'data' in response_dict:
        data = response_dict['data']
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            raise ValueError(f"Unexpected 'data' format: {type(data)}")
        
        # Check for b64_json
        if isinstance(item, dict) and 'b64_json' in item and item['b64_json'] is not None:
            image_str = item['b64_json']
            metadata['extraction_method'] = 'data[0].b64_json'
            metadata['original_format'] = 'base64'
            
            # Handle data URI format
            if image_str.startswith('data:image/'):
                image_str = image_str.split(',', 1)[1]
            
            return base64.b64decode(image_str), metadata
        
        # Check for url
        elif isinstance(item, dict) and 'url' in item and item['url'] is not None:
            url = item['url']
            metadata['extraction_method'] = 'data[0].url'
            metadata['original_format'] = 'url'
            metadata['source_url'] = url
            
            response_obj = requests.get(url)
            response_obj.raise_for_status()
            return response_obj.content, metadata
        
        # Check for direct image key
        elif isinstance(item, dict) and 'image' in item and item['image'] is not None:
            image_str = item['image']
            metadata['extraction_method'] = 'data[0].image'
            metadata['original_format'] = 'base64'
            
            if image_str.startswith('data:image/'):
                image_str = image_str.split(',', 1)[1]
            
            return base64.b64decode(image_str), metadata
    
    # Method 2: Direct keys at top level
    if isinstance(response_dict, dict):
        if 'b64_json' in response_dict and response_dict['b64_json'] is not None:
            image_str = response_dict['b64_json']
            metadata['extraction_method'] = 'root.b64_json'
            metadata['original_format'] = 'base64'
            
            if image_str.startswith('data:image/'):
                image_str = image_str.split(',', 1)[1]
            
            return base64.b64decode(image_str), metadata
        
        elif 'url' in response_dict and response_dict['url'] is not None:
            url = response_dict['url']
            metadata['extraction_method'] = 'root.url'
            metadata['original_format'] = 'url'
            metadata['source_url'] = url
            
            response_obj = requests.get(url)
            response_obj.raise_for_status()
            return response_obj.content, metadata
        
        elif 'image' in response_dict and response_dict['image'] is not None:
            image_str = response_dict['image']
            metadata['extraction_method'] = 'root.image'
            metadata['original_format'] = 'base64'
            
            if image_str.startswith('data:image/'):
                image_str = image_str.split(',', 1)[1]
            
            return base64.b64decode(image_str), metadata
        
        # Method 3: Choices format (some APIs use this)
        elif 'choices' in response_dict:
            choices = response_dict['choices']
            if isinstance(choices, list) and len(choices) > 0:
                item = choices[0]
                if isinstance(item, dict) and 'image' in item and item['image'] is not None:
                    image_str = item['image']
                    metadata['extraction_method'] = 'choices[0].image'
                    metadata['original_format'] = 'base64'
                    
                    if image_str.startswith('data:image/'):
                        image_str = image_str.split(',', 1)[1]
                    
                    return base64.b64decode(image_str), metadata
    
    # If we got here, we couldn't parse the response
    if isinstance(response_dict, dict):
        # Build a helpful error message showing what keys were found
        found_keys = list(response_dict.keys())
        none_keys = [k for k in ['b64_json', 'url', 'image', 'data', 'choices'] if k in response_dict and response_dict[k] is None]
        
        error_msg = f"Unable to extract image data from response. Found keys: {found_keys}"
        if none_keys:
            error_msg += f"\nNote: These image-related keys were present but had None values: {none_keys}"
        
        if 'data' in response_dict:
            data = response_dict['data']
            if isinstance(data, list) and len(data) > 0:
                error_msg += f"\nFirst data item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}"
            elif isinstance(data, dict):
                error_msg += f"\nData keys: {list(data.keys())}"
        
        raise ValueError(error_msg)
    else:
        raise ValueError(f"Unable to extract image data. Response type: {type(response_dict)}")