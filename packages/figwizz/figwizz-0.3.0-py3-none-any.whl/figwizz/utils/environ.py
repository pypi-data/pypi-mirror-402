"""
Environment variable loading and capability checking functions.

This module provides utilities for managing environment variables and detecting
available API capabilities based on configured keys. It handles .env file
loading and provides helpful capability reports for optional features.

Key features:
- Automatic .env file discovery in current and parent directories
- Support for multiple .env file naming conventions
- Capability detection for stock image providers and AI services
- Verbose reporting of available features

The auto_load_env function is called automatically when importing figwizz,
making environment setup seamless.

Example:
    ```python
    from figwizz.utils.environ import check_capabilities, load_env_variables
    
    # Check what features are available
    capabilities = check_capabilities(verbose=True)
    
    # Manually load specific .env file
    load_env_variables('.env.production')
    ```
"""

import os

__all__ = [
    'load_env_variables',
    'check_capabilities',
    'auto_load_env',
]

# Environment Variable Checking Functions ----------------------------------------

def search_for_env_file(env_file='auto', max_parents=3, abspath=False):
    """
    Search for environment variable files in the current and parent directories.
    
    This function searches for .env files starting from the current working directory
    and traversing up to a specified number of parent directories. It supports
    multiple .env file naming conventions.
    
    Args:
        env_file (str, optional): Specific .env file name to search for, or 'auto' to
            search for common variants. Defaults to 'auto'.
            When 'auto', searches for: .env, .env.local, .env.development, .env.production
        max_parents (int, optional): Maximum number of parent directories to search.
            Defaults to 3.
        abspath (bool, optional): If True, returns absolute path. If False, returns
            relative path. Defaults to False.
    
    Returns:
        str or None: Path to the found .env file, or None if not found
    
    Examples:
        ```python
        from figwizz.utils.environ import search_for_env_file
        
        # Search for any common .env file
        env_path = search_for_env_file()
        
        # Search for a specific .env file
        env_path = search_for_env_file(env_file='production')
        
        # Get absolute path
        env_path = search_for_env_file(abspath=True)
        ```
    
    Note:
        - Searches in order: current directory, parent, grandparent, etc.
        - Stops at first match found
        - Prints the path of the found file
    """
    env_file_opts = ['.env', '.env.local', '.env.development', '.env.production']
    
    if env_file != 'auto' and env_file is not None:
        env_file_opts = [env_file if env_file.startswith('.') else f'.{env_file}']
    
    env_filepath = None
    
    for i in range(max_parents):
        for file_opt in env_file_opts:
            relative_path = os.path.join(os.getcwd(), *['..']*i, file_opt)
            if os.path.exists(relative_path):
                env_filepath = relative_path
                break
        if env_filepath is not None:
            break
    
    if env_filepath is not None:
        print(f"Found .env file at {env_filepath}")
        if abspath:
            env_filepath = os.path.abspath(env_filepath)
            
    return env_filepath # return the path to the env file
    
def load_env_variables(env_file='auto', update_environ=True, **kwargs):
    """
    Load environment variables from a .env file.
    
    This function reads key-value pairs from a .env file and optionally updates
    the system environment variables. It handles common .env file formats including
    quoted values, inline comments, and empty lines.
    
    Args:
        env_file (str, optional): Path to .env file, or 'auto' to search for it.
            When 'auto', uses search_for_env_file() to locate the file.
            Defaults to 'auto'.
        update_environ (bool, optional): If True, updates os.environ with the loaded
            variables. If False, returns the variables as a dictionary without updating
            the environment. Defaults to True.
        **kwargs: Additional keyword arguments passed to search_for_env_file()
            (e.g., max_parents, abspath)
    
    Returns:
        dict or None: Dictionary of environment variables if update_environ=False,
            otherwise None
    
    Raises:
        FileNotFoundError: If no .env file is found
    
    Examples:
        ```python
        from figwizz.utils.environ import load_env_variables
        
        # Load and update environment
        load_env_variables()
        
        # Load without updating environment
        env_vars = load_env_variables(update_environ=False)
        print(env_vars)
        
        # Load specific file
        load_env_variables(env_file='.env.production')
        ```
    
    Note:
        - Handles quoted values (single or double quotes)
        - Strips inline comments (text after '#')
        - Skips empty lines and comment-only lines
        - Malformed lines are skipped with a warning
        - Supports values containing '=' characters
    """
    if not os.path.exists(env_file):
        env_file = search_for_env_file(env_file, **kwargs)
        if env_file is None:
            raise FileNotFoundError("No .env file found in the current or parent directories.")
    
    if env_file is not None:
       # update the environment variables with the values from the env file
       env_vars = {}
       with open(env_file, 'r') as file:
           for line_num, line in enumerate(file, 1):
               line = line.strip()
               # Skip empty lines and comments
               if not line or line.startswith('#'):
                   continue
               
               # Handle lines with '=' delimiter
               if '=' not in line:
                   print(f"Warning: Skipping malformed line {line_num} in {env_file}: {line}")
                   continue
               
               # Split on first '=' to handle values with '=' in them
               key, _, value = line.partition('=')
               key = key.strip()
               value = value.strip()
               
               # Remove quotes from value if present
               if value and value[0] in ('"', "'") and value[-1] == value[0]:
                   value = value[1:-1]
               
               # Remove inline comments (only if not in quotes)
               if '#' in value:
                   # Simple approach: split on # and take first part
                   # This won't handle # inside quotes perfectly, but is reasonable
                   value = value.split('#')[0].strip()
               
               env_vars[key] = value
               
       if not update_environ:
            return env_vars
       else: # update the global env
            os.environ.update(env_vars)
            return None

# Capability Detection Functions ----------------------------------------

# Define capability mappings
CAPABILITY_MAP = {
    'stock_image_download': {
        'pixabay': ['PIXABAY_API_KEY'],
        'unsplash': ['UNSPLASH_ACCESS_KEY'],
    },
    'genai_image_generation': {
        'openai': ['OPENAI_API_KEY'],
        'google': ['GOOGLE_API_KEY'],
        'openrouter': ['OPENROUTER_API_KEY'],
    },
}

def check_capabilities(verbose=False):
    """
    Check which capabilities are available based on environment variables.
    
    Parameters
    ----------
    verbose : bool
        If True, print detailed capability information
        
    Returns
    -------
    dict
        Dictionary mapping capability categories to available providers
    """
    capabilities = {}
    
    for capability, providers in CAPABILITY_MAP.items():
        available_providers = []
        for provider, required_keys in providers.items():
            # Check if all required keys are present and non-empty
            if all(os.getenv(key) for key in required_keys):
                available_providers.append(provider)
        
        if available_providers:
            capabilities[capability] = available_providers
    
    if verbose:
        _print_capabilities(capabilities)
    
    return capabilities

def _print_capabilities(capabilities):
    """Print formatted capability information."""
    if not capabilities:
        print("No API keys found. Basic functionality available.")
        print("Add API keys to enable additional features:")
        print("  - Stock image download (Pixabay, Unsplash)")
        print("  - AI image generation (OpenAI, Google, OpenRouter)")
        return
    
    print("Available capabilities:")
    for capability, providers in capabilities.items():
        capability_name = capability.replace('_', ' ').title()
        providers_str = ', '.join(providers)
        print(f"  - {capability_name}: {providers_str}")

def auto_load_env(verbose=False, silent_on_missing=True):
    """
    Automatically search for and load environment variables on import.
    
    Parameters
    ----------
    verbose : bool
        If True, print capability information
    silent_on_missing : bool
        If True, don't raise an error if no .env file is found
        
    Returns
    -------
    dict or None
        Dictionary of available capabilities, or None if silent_on_missing=True
    """
    try:
        # Try to find and load .env file
        env_file = search_for_env_file(env_file='auto', max_parents=3)
        if env_file is not None:
            load_env_variables(env_file=env_file, update_environ=True)
    except FileNotFoundError:
        if not silent_on_missing:
            raise
        # Silently continue if no .env file found
    
    # Check and return capabilities
    capabilities = check_capabilities(verbose=verbose)
    return capabilities