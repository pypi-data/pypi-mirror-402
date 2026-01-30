"""
MBM - Modular CLI Platform

A powerful command-line interface platform featuring the Aaryan programming
language and an intelligent AI assistant. Built for education, productivity,
and extensibility.

Copyright (c) 2026 MBM Team
License: MIT
"""

__version__ = "0.1.0"
__author__ = "MBM Team"
__email__ = "contact@mbm.edu"
__license__ = "MIT"

from mbm.core.config import MBMConfig
from mbm.core.constants import APP_NAME, APP_VERSION

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "MBMConfig",
    "APP_NAME",
    "APP_VERSION",
]
