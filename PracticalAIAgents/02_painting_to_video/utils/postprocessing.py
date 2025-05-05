from typing import Dict, Any, Optional, Union
import re
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Normalize a URL by ensuring it has an https:// prefix and removing query parameters.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL with proper prefix and without query parameters
    """
    # If URL is empty or None, return as is
    if not url:
        return url
    
    # Add https:// prefix if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Remove query parameters (everything after ?)
    parsed = urlparse(url)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        '',  # Remove query
        ''   # Remove fragment
    ))
    
    return clean_url


def process_artwork_urls(artwork_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all URLs in the artwork data to ensure they are properly formatted.
    
    Args:
        artwork_data: Dictionary containing artwork details including image_urls
        
    Returns:
        Updated artwork data with normalized URLs
    """
    # Create a copy to avoid mutating the original
    processed_data = artwork_data.copy()
    
    # Process image URLs if they exist
    if "image_urls" in processed_data and isinstance(processed_data["image_urls"], dict):
        image_urls = processed_data["image_urls"]
        
        # Process main image URL
        if "main_image_url" in image_urls:
            image_urls["main_image_url"] = normalize_url(image_urls["main_image_url"])
            
        # Process source URL
        if "source_url" in image_urls:
            image_urls["source_url"] = normalize_url(image_urls["source_url"])
    
    return processed_data

