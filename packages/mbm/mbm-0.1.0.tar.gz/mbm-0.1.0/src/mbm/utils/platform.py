"""
Platform Utilities

Cross-platform utilities for detecting OS and executing
platform-specific operations.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    """Supported platforms."""
    
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class PlatformUtils:
    """
    Cross-platform utility class.
    
    Provides methods for platform detection and platform-specific
    operations like opening files with the default application.
    """
    
    @staticmethod
    def get_platform() -> Platform:
        """
        Detect the current platform.
        
        Returns:
            Platform enum value
        """
        system = platform.system().lower()
        
        if system == "windows":
            return Platform.WINDOWS
        elif system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            return Platform.LINUX
        else:
            return Platform.UNKNOWN
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return PlatformUtils.get_platform() == Platform.WINDOWS
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS."""
        return PlatformUtils.get_platform() == Platform.MACOS
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux."""
        return PlatformUtils.get_platform() == Platform.LINUX
    
    @staticmethod
    def open_file(filepath: str) -> bool:
        """
        Open a file with the system's default application.
        
        Uses:
        - Windows: os.startfile
        - macOS: open
        - Linux: xdg-open
        
        Args:
            filepath: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(filepath):
            return False
        
        try:
            current_platform = PlatformUtils.get_platform()
            
            if current_platform == Platform.WINDOWS:
                os.startfile(filepath)
                
            elif current_platform == Platform.MACOS:
                subprocess.run(
                    ["open", filepath],
                    check=True,
                    capture_output=True,
                )
                
            elif current_platform == Platform.LINUX:
                subprocess.run(
                    ["xdg-open", filepath],
                    check=True,
                    capture_output=True,
                )
                
            else:
                # Try xdg-open as fallback
                subprocess.run(
                    ["xdg-open", filepath],
                    check=True,
                    capture_output=True,
                )
            
            return True
            
        except (OSError, subprocess.CalledProcessError):
            return False
    
    @staticmethod
    def open_url(url: str) -> bool:
        """
        Open a URL in the system's default browser.
        
        Args:
            url: URL to open
            
        Returns:
            True if successful, False otherwise
        """
        import webbrowser
        
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_temp_dir() -> str:
        """
        Get the system's temporary directory.
        
        Returns:
            Path to temp directory
        """
        import tempfile
        return tempfile.gettempdir()
    
    @staticmethod
    def get_home_dir() -> str:
        """
        Get the user's home directory.
        
        Returns:
            Path to home directory
        """
        return os.path.expanduser("~")
    
    @staticmethod
    def get_python_version() -> str:
        """
        Get the current Python version.
        
        Returns:
            Python version string
        """
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    @staticmethod
    def get_system_info() -> dict:
        """
        Get system information.
        
        Returns:
            Dictionary with system info
        """
        return {
            "platform": PlatformUtils.get_platform().value,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": PlatformUtils.get_python_version(),
        }
    
    @staticmethod
    def clear_screen() -> None:
        """
        Clear the terminal screen.
        
        Works on Windows, macOS, and Linux.
        """
        if PlatformUtils.is_windows():
            os.system('cls')
        else:
            os.system('clear')
    
    @staticmethod
    def hide_cursor() -> None:
        """Hide the terminal cursor (cross-platform)."""
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
    
    @staticmethod
    def show_cursor() -> None:
        """Show the terminal cursor (cross-platform)."""
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
    
    @staticmethod
    def get_terminal_size() -> tuple:
        """
        Get the terminal size.
        
        Returns:
            Tuple of (columns, rows)
        """
        try:
            size = os.get_terminal_size()
            return (size.columns, size.lines)
        except OSError:
            return (80, 24)  # Default fallback
