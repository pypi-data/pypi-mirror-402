"""
Wikimedia Commons Service

Fetches images from Wikimedia Commons - a legal, public source
of freely licensed media.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import requests

from mbm.core.constants import (
    WIKIMEDIA_COMMONS_API,
    DEFAULT_TIMEOUT,
    USER_AGENT,
)


class WikimediaService:
    """
    Wikimedia Commons image retrieval service.
    
    Uses the official Wikimedia Commons API to search for and
    fetch freely licensed images. This is a legal, ethical
    source of images.
    
    Note: NO Google Images scraping - Wikimedia Commons only!
    """
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize Wikimedia service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
    
    def search_image(self, query: str) -> Optional[str]:
        """
        Search for an image on Wikimedia Commons.
        
        Args:
            query: Search term
            
        Returns:
            URL of the image, or None if not found
        """
        if not query or not query.strip():
            return None
        
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",  # File namespace
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrlimit": "5",
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": "800",  # Request thumbnail for faster loading
        }
        
        try:
            response = requests.get(
                WIKIMEDIA_COMMONS_API,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            
            # Find the best image
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue
                
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    
                    # Check if it's an actual image
                    mime = info.get("mime", "")
                    if mime.startswith("image/"):
                        # Return thumbnail URL for faster loading
                        return info.get("thumburl") or info.get("url")
            
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def search_images(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search for multiple images on Wikimedia Commons.
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of image info dictionaries
        """
        if not query or not query.strip():
            return []
        
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrlimit": str(limit),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "400",
        }
        
        try:
            response = requests.get(
                WIKIMEDIA_COMMONS_API,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue
                
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    mime = info.get("mime", "")
                    
                    if mime.startswith("image/"):
                        metadata = info.get("extmetadata", {})
                        results.append({
                            "title": page_data.get("title", ""),
                            "url": info.get("url"),
                            "thumb_url": info.get("thumburl"),
                            "width": info.get("width"),
                            "height": info.get("height"),
                            "mime": mime,
                            "description": metadata.get("ImageDescription", {}).get("value", ""),
                            "license": metadata.get("LicenseShortName", {}).get("value", ""),
                        })
            
            return results
            
        except requests.exceptions.RequestException:
            return []
    
    def get_image_info(self, filename: str) -> Optional[dict]:
        """
        Get information about a specific image file.
        
        Args:
            filename: File name (e.g., "File:Example.jpg")
            
        Returns:
            Image info dictionary or None
        """
        if not filename:
            return None
        
        # Ensure proper format
        if not filename.startswith("File:"):
            filename = f"File:{filename}"
        
        params = {
            "action": "query",
            "format": "json",
            "titles": filename,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "800",
        }
        
        try:
            response = requests.get(
                WIKIMEDIA_COMMONS_API,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue
                
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    metadata = info.get("extmetadata", {})
                    
                    return {
                        "title": page_data.get("title", ""),
                        "url": info.get("url"),
                        "thumb_url": info.get("thumburl"),
                        "width": info.get("width"),
                        "height": info.get("height"),
                        "mime": info.get("mime"),
                        "description": metadata.get("ImageDescription", {}).get("value", ""),
                        "license": metadata.get("LicenseShortName", {}).get("value", ""),
                        "author": metadata.get("Artist", {}).get("value", ""),
                    }
            
            return None
            
        except requests.exceptions.RequestException:
            return None
