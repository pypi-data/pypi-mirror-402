"""
MBM People Module

Manages special people profiles (students, faculty, staff) with
ASCII art and biographical information.
"""

from mbm.people.registry import PersonRegistry
from mbm.people.models import Person, PersonCategory

__all__ = [
    "PersonRegistry",
    "Person",
    "PersonCategory",
]
