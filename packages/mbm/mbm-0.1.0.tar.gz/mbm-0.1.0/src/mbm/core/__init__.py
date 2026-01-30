"""
MBM Core Module

Contains configuration, constants, and core functionality shared across
all MBM components.
"""

from mbm.core.config import MBMConfig
from mbm.core.constants import APP_NAME, APP_VERSION, BANNER

__all__ = [
    "MBMConfig",
    "APP_NAME",
    "APP_VERSION",
    "BANNER",
]
