"""
Media Handler

Handles downloading, caching, and displaying media files
(images, etc.) with cross-platform support.
"""

from __future__ import annotations

import atexit
import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from mbm.core.config import get_config
from mbm.core.constants import DEFAULT_TIMEOUT, USER_AGENT
from mbm.utils.platform import PlatformUtils


class MediaHandler:
    """
    Cross-platform media handler.
    
    Downloads media to temporary files and opens them with the
    system's default viewer. Handles cleanup automatically.
    
    Features:
    - Downloads to temp directory (not permanent storage)
    - Auto-cleanup on exit
    - Cross-platform file opening
    - Simple caching to avoid re-downloads
    """
    
    def __init__(self, cleanup_on_exit: bool = True):
        """
        Initialize media handler.
        
        Args:
            cleanup_on_exit: Whether to cleanup temp files on exit
        """
        self.config = get_config()
        self.temp_dir = self.config.temp_dir
        self._downloaded_files: list[Path] = []
        
        if cleanup_on_exit:
            atexit.register(self.cleanup)
    
    def download(self, url: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        Download a file to the temp directory.
        
        Args:
            url: URL to download
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to downloaded file, or None if failed
        """
        if not url:
            return None
        
        try:
            # Generate filename if not provided
            if not filename:
                filename = self._generate_filename(url)
            
            filepath = self.temp_dir / filename
            
            # Check if already downloaded (simple cache)
            if filepath.exists():
                return filepath
            
            # Download file
            headers = {"User-Agent": USER_AGENT}
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.media_timeout or DEFAULT_TIMEOUT,
                stream=True,
            )
            response.raise_for_status()
            
            # Write to temp file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Track for cleanup
            self._downloaded_files.append(filepath)
            
            return filepath
            
        except (requests.exceptions.RequestException, IOError):
            return None
    
    def download_and_open(self, url: str) -> Optional[str]:
        """
        Download a file and open it with the system's default viewer.
        
        Args:
            url: URL to download
            
        Returns:
            Path to file if successful, None otherwise
        """
        filepath = self.download(url)
        
        if filepath and filepath.exists():
            success = PlatformUtils.open_file(str(filepath))
            if success:
                return str(filepath)
        
        return None
    
    def open_file(self, filepath: str) -> bool:
        """
        Open a local file with the system's default viewer.
        
        Args:
            filepath: Path to file
            
        Returns:
            True if successful
        """
        return PlatformUtils.open_file(filepath)
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate a filename from a URL.
        
        Args:
            url: URL to generate filename from
            
        Returns:
            Generated filename
        """
        # Parse URL to get extension
        parsed = urlparse(url)
        path = parsed.path
        
        # Get extension
        ext = Path(path).suffix or ".tmp"
        
        # Create hash-based filename for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        timestamp = int(time.time())
        
        return f"mbm_media_{url_hash}_{timestamp}{ext}"
    
    def cleanup(self) -> int:
        """
        Clean up downloaded temporary files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        
        for filepath in self._downloaded_files:
            try:
                if filepath.exists():
                    filepath.unlink()
                    count += 1
            except OSError:
                pass
        
        self._downloaded_files.clear()
        
        # Also clean up any orphaned files in temp dir
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("mbm_media_*"):
                try:
                    # Only delete files older than 1 hour
                    if time.time() - file.stat().st_mtime > 3600:
                        file.unlink()
                        count += 1
                except OSError:
                    pass
        
        return count
    
    def get_cache_size(self) -> int:
        """
        Get the total size of cached media files in bytes.
        
        Returns:
            Total size in bytes
        """
        total = 0
        
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("mbm_media_*"):
                try:
                    total += file.stat().st_size
                except OSError:
                    pass
        
        return total
    
    def clear_cache(self) -> int:
        """
        Clear all cached media files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("mbm_media_*"):
                try:
                    file.unlink()
                    count += 1
                except OSError:
                    pass
        
        self._downloaded_files.clear()
        return count
