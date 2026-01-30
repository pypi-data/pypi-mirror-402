"""
Image generation with generative AI models.

This module provides functions for generating images using AI models
through the litellm library. Requires optional dependency: litellm.

Example:
    ```python
    from figwizz.generate import generate_images
    prompts = ["a red apple", "a blue ocean"]
    images = generate_images(prompts, output_dir="generated")
    ```
"""

import os, re, json
from copy import copy
from datetime import datetime
from typing import Any, Dict
from PIL import Image
from tqdm.auto import tqdm

from .utils import check_optional_import

from .workflows.genai import (
    make_json_serializable,
    extract_image_from_genai_response,
)

def extract_image_data(response: Any) -> tuple[bytes, Dict[str, Any]]:
    """
    Extract image data from a generative AI response.
    
    This is a convenience wrapper around extract_image_from_genai_response.
    It handles various response formats from different AI providers.
    
    Args:
        response (Any): The response object from a generative AI model (e.g., OpenAI,
            Google, OpenRouter). Can be a dictionary or custom response object.
        
    Returns:
        tuple[bytes, dict]: A tuple containing:
            - bytes: Raw image data ready to be saved
            - dict: Metadata about the extraction method and format
    
    Examples:
        ```python
        from figwizz.generate import extract_image_data
        from litellm import image_generation
        
        # Generate image
        response = image_generation(prompt="a sunset", model="gpt-image-1")
        
        # Extract image bytes
        image_bytes, metadata = extract_image_data(response)
        
        # Save to file
        with open('sunset.png', 'wb') as f:
            f.write(image_bytes)
        ```
    
    Note:
        - Supports base64 and URL-based image responses
        - Automatically handles various AI provider response formats
        - See extract_image_from_genai_response for detailed format support
    """
    return extract_image_from_genai_response(response)

def generate_images(prompts, output_dir, n_images=1, model='gpt-image-1', 
                    api_key=None, return_images=True):
    """
    Generate images from text prompts using generative AI models.
    
    Uses the litellm library to generate images from various AI providers including
    OpenAI, Google, and OpenRouter. Each generated image is saved with comprehensive
    metadata including the prompt, model, timestamp, and API response details.
    
    Args:
        prompts (str or list[str]): Text prompt(s) describing the desired image(s).
            Can be a single string or a list of strings for batch generation.
        output_dir (str): Directory where generated images and metadata will be saved.
            Created automatically if it doesn't exist.
        n_images (int, optional): Number of images to generate for each prompt.
            Defaults to 1.
        model (str, optional): Model identifier for image generation. Common options:
            - 'gpt-image-1' (OpenAI DALL-E)
            - 'dall-e-3' (OpenAI DALL-E 3)
            - 'dall-e-2' (OpenAI DALL-E 2)
            Defaults to 'gpt-image-1'.
        api_key (str, optional): API key for the AI service. If None, reads from
            OPENAI_API_KEY environment variable. Defaults to None.
        return_images (bool, optional): If True, returns list of PIL Image objects.
            If False, only saves images and returns None. Defaults to True.
        
    Returns:
        list[PIL.Image.Image] or None: List of PIL Image objects if return_images=True,
            otherwise None
    
    Raises:
        ImportError: If litellm is not installed
        ValueError: If OPENAI_API_KEY is not set and api_key is None
    
    Examples:
        ```python
        from figwizz import generate_images
        
        # Generate a single image
        images = generate_images(
            "a serene mountain landscape at sunset",
            output_dir="generated_images"
        )
        images[0].show()
        
        # Generate multiple images from multiple prompts
        prompts = [
            "a red apple on a wooden table",
            "a blue ocean with white clouds",
            "a futuristic city at night"
        ]
        images = generate_images(
            prompts,
            output_dir="ai_art",
            n_images=2,  # 2 variations per prompt
            model="dall-e-3"
        )
        
        # Generate without returning images (saves memory)
        generate_images(
            prompts,
            output_dir="batch_output",
            return_images=False
        )
        ```
    
    Note:
        - Requires litellm: `pip install litellm` or `pip install 'figwizz[genai]'`
        - Each prompt creates a subdirectory named after the prompt (sanitized)
        - For each image, saves:
          * image_N.png - The generated image
          * image_N_response.json - Full API response
          * image_N_metadata.json - Curated metadata (prompt, model, timestamp, etc.)
        - Failed generations are skipped with error messages
        - Progress is displayed via tqdm progress bars
        - Image numbering continues from existing images in subdirectories
        - Prompt text is sanitized for use in directory names (removes special chars)
    """
    
    if not check_optional_import('litellm'):
        raise ImportError("litellm is required for image generation. Install it with: pip install litellm or pip install 'figwizz[genai]'")
    
    from litellm import image_generation
    
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')
        
    if api_key is None:
        raise ValueError("OPENAI_API_KEY required for image generation. Set it in the .env file or pass it as an argument.")
    
    if not isinstance(prompts, list):
        prompts = [prompts]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
        
    image_paths = [] # list to store the paths to the generated images
        
    for prompt in tqdm(prompts, desc="Processing Prompts"):
        prompt_for_filepath = copy(prompt).lower()
        
        # remove common english articles
        prompt_for_filepath = re.sub(r'\b(a|an|the)\b', '', prompt_for_filepath)
        
        # Remove all non-alphanumeric characters
        prompt_for_filepath = re.sub(r'[^a-z0-9\s]', '', prompt_for_filepath)
        
        # Replace whitespace with a single dash
        prompt_for_filepath = re.sub(r'\s+', '-', prompt_for_filepath)
        
        # Replace double dashes with single dash
        prompt_for_filepath = re.sub(r'--', '-', prompt_for_filepath)
        
        # Remove leading/trailing dashes
        prompt_for_filepath = prompt_for_filepath.strip('-')
        
        output_subdir = os.path.join(output_dir, prompt_for_filepath)
        os.makedirs(output_subdir, exist_ok=True)
        
        for image_index in tqdm(range(n_images), desc="Generating Images"):
            response = None
            response_path = None
            
            try:
                # Generate the image
                response = image_generation(
                    prompt=prompt, 
                    size='1024x1024', 
                    model=model,
                    api_key=api_key,
                )
                
            except Exception as error:
                print(f"Error generating image for prompt: {prompt}")
                print(f"   Error: {error}")
                continue
            
            # Prepare file paths
            image_path = os.path.join(output_subdir, f"image_{image_index + 1}.png")
            response_path = os.path.join(output_subdir, f"image_{image_index + 1}_response.json")
            metadata_path = os.path.join(output_subdir, f"image_{image_index + 1}_metadata.json")
            
            # Handle existing files by incrementing index
            if os.path.exists(image_path):
                last_index = int(image_path.split('_')[-1].split('.')[0])
                image_path = os.path.join(output_subdir, f"image_{last_index + 1}.png")
                response_path = os.path.join(output_subdir, f"image_{last_index + 1}_response.json")
                metadata_path = os.path.join(output_subdir, f"image_{last_index + 1}_metadata.json")
            
            try:
                # Convert response to JSON-serializable format and save
                serializable_response = make_json_serializable(response)
                
                with open(response_path, 'w') as json_file:
                    json.dump(serializable_response, json_file, indent=2)
                
            except Exception as error:
                print(f"Warning: Could not save full response to JSON: {error}")
                print(f"   Attempting to save string representation instead")
                try:
                    with open(response_path, 'w') as json_file:
                        json.dump({'response_str': str(response), 'error': str(error)}, json_file, indent=2)
                except Exception as nested_error:
                    print(f"   Failed to save response: {nested_error}")
            
            try:
                # Extract image data using the helper function
                image_bytes, extraction_metadata = extract_image_data(response)
                
                # Save the image
                with open(image_path, "wb") as filepath:
                    filepath.write(image_bytes)
                
                # Create and save comprehensive metadata
                metadata = {
                    'prompt': prompt,
                    'model': model,
                    'timestamp': datetime.now().isoformat(),
                    'image_path': image_path,
                    'response_path': response_path,
                    'extraction_info': extraction_metadata
                }
                
                with open(metadata_path, 'w') as json_file:
                    json.dump(metadata, json_file, indent=2)
                
                image_paths.append(image_path)
                    
            except ValueError as error:
                print(f"Error: Unable to parse image from response for prompt: {prompt}")
                print(f"   {error}")
                if response_path and os.path.exists(response_path):
                    print(f"   Full response saved to: {response_path}")
                continue
                
            except Exception as error:
                print(f"Error processing generated image for prompt: {prompt}")
                print(f"   Error type: {type(error).__name__}")
                print(f"   Error: {error}")
                if response_path and os.path.exists(response_path):
                    print(f"   Full response saved to: {response_path}")
                continue
            
    if return_images:
        return [Image.open(image_path) for image_path in image_paths]