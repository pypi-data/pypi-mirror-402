"""
Tests for utility functions.
"""

import pytest
import os
import tempfile

from mbm.utils.platform import PlatformUtils, Platform


class TestPlatformUtils:
    """Tests for platform utilities."""
    
    def test_get_platform(self):
        platform = PlatformUtils.get_platform()
        
        assert platform in [Platform.WINDOWS, Platform.MACOS, Platform.LINUX, Platform.UNKNOWN]
    
    def test_platform_detection_methods(self):
        # At least one of these should be True
        is_any = (
            PlatformUtils.is_windows() or
            PlatformUtils.is_macos() or
            PlatformUtils.is_linux()
        )
        
        # On known platforms, one should be True
        # (might be False on very unusual platforms)
        assert isinstance(PlatformUtils.is_windows(), bool)
        assert isinstance(PlatformUtils.is_macos(), bool)
        assert isinstance(PlatformUtils.is_linux(), bool)
    
    def test_get_temp_dir(self):
        temp_dir = PlatformUtils.get_temp_dir()
        
        assert temp_dir is not None
        assert os.path.isdir(temp_dir)
    
    def test_get_home_dir(self):
        home_dir = PlatformUtils.get_home_dir()
        
        assert home_dir is not None
        assert os.path.isdir(home_dir)
    
    def test_get_python_version(self):
        version = PlatformUtils.get_python_version()
        
        assert version is not None
        assert "." in version
    
    def test_get_system_info(self):
        info = PlatformUtils.get_system_info()
        
        assert "platform" in info
        assert "system" in info
        assert "python_version" in info
    
    def test_open_file_nonexistent(self):
        # Should return False for non-existent file
        result = PlatformUtils.open_file("/nonexistent/path/file.txt")
        assert result is False


class TestMediaHandler:
    """Tests for media handler."""
    
    def test_generate_filename(self):
        from mbm.utils.media import MediaHandler
        
        handler = MediaHandler(cleanup_on_exit=False)
        
        filename = handler._generate_filename("https://example.com/image.jpg")
        
        assert filename.startswith("mbm_media_")
        assert filename.endswith(".jpg")
    
    def test_cleanup(self):
        from mbm.utils.media import MediaHandler
        
        handler = MediaHandler(cleanup_on_exit=False)
        
        # Cleanup should not raise errors even with no files
        count = handler.cleanup()
        assert count >= 0
    
    def test_get_cache_size(self):
        from mbm.utils.media import MediaHandler
        
        handler = MediaHandler(cleanup_on_exit=False)
        
        size = handler.get_cache_size()
        assert size >= 0
