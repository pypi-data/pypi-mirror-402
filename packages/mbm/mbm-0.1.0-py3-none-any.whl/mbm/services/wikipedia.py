"""
Wikipedia Service

Fetches information from the Wikipedia REST API.
Uses only the official, public Wikipedia API.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import requests

from mbm.core.constants import (
    WIKIPEDIA_API_URL,
    DEFAULT_TIMEOUT,
    USER_AGENT,
)


class WikipediaService:
    """
    Wikipedia information retrieval service.
    
    Uses the official Wikipedia REST API to fetch article summaries.
    This is a legal, public API that doesn't require authentication.
    """
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize Wikipedia service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
    
    def get_summary(self, query: str) -> Optional[dict]:
        """
        Get a summary of a Wikipedia article.
        
        Args:
            query: Search term (article title)
            
        Returns:
            Dictionary with title and extract, or None if not found
        """
        if not query or not query.strip():
            return None
        
        # URL encode the query
        encoded_query = quote(query.strip().replace(" ", "_"))
        url = f"{WIKIPEDIA_API_URL}/{encoded_query}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
            )
            
            if response.status_code == 404:
                # Try search if exact match not found
                return self._search_and_get(query)
            
            response.raise_for_status()
            data = response.json()
            
            # Check for disambiguation or missing page
            if data.get("type") == "disambiguation":
                return {
                    "title": data.get("title", query),
                    "extract": (
                        f"'{query}' may refer to multiple topics. "
                        "Please be more specific."
                    ),
                }
            
            if "extract" not in data:
                return None
            
            return {
                "title": data.get("title", query),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            }
            
        except requests.exceptions.RequestException:
            return None
    
    def _search_and_get(self, query: str) -> Optional[dict]:
        """
        Search Wikipedia and get the first result's summary.
        
        Args:
            query: Search term
            
        Returns:
            Dictionary with title and extract, or None if not found
        """
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
        }
        
        try:
            response = requests.get(
                search_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("query", {}).get("search", [])
            
            if search_results:
                # Get the first result's title and fetch its summary
                first_title = search_results[0].get("title")
                if first_title:
                    return self.get_summary(first_title)
            
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search Wikipedia for articles.
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of search results with title and snippet
        """
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }
        
        try:
            response = requests.get(
                search_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                })
            
            return results
            
        except requests.exceptions.RequestException:
            return []
