"""
MBM Exceptions

Custom exception classes for the MBM platform, providing clear error
handling and informative error messages.
"""

from typing import Optional


class MBMError(Exception):
    """Base exception for all MBM-related errors."""
    
    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.code = code
    
    def __str__(self) -> str:
        if self.code:
            return f"[MBM-{self.code}] {self.message}"
        return f"[MBM] {self.message}"


class ConfigError(MBMError):
    """Configuration-related errors."""
    
    def __init__(self, message: str):
        super().__init__(message, code=100)


class FileNotFoundError(MBMError):
    """File not found errors."""
    
    def __init__(self, filepath: str):
        super().__init__(f"File not found: {filepath}", code=200)
        self.filepath = filepath


class ParseError(MBMError):
    """Parsing errors for Aaryan language."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        location = ""
        if line is not None:
            location = f" at line {line}"
            if column is not None:
                location += f", column {column}"
        super().__init__(f"Parse error{location}: {message}", code=300)
        self.line = line
        self.column = column


class RuntimeError(MBMError):
    """Runtime errors during Aaryan program execution."""
    
    def __init__(self, message: str, line: Optional[int] = None):
        location = f" at line {line}" if line else ""
        super().__init__(f"Runtime error{location}: {message}", code=400)
        self.line = line


class AIError(MBMError):
    """AI/NLP related errors."""
    
    def __init__(self, message: str):
        super().__init__(message, code=500)


class NetworkError(MBMError):
    """Network-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        full_message = message
        if url:
            full_message += f" (URL: {url})"
        super().__init__(full_message, code=600)
        self.url = url


class MediaError(MBMError):
    """Media handling errors."""
    
    def __init__(self, message: str):
        super().__init__(message, code=700)


class PersonNotFoundError(MBMError):
    """Person profile not found errors."""
    
    def __init__(self, name: str):
        super().__init__(f"Person not found: {name}", code=800)
        self.name = name
