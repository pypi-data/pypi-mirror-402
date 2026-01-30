"""
People Models

Data models for representing people (students, faculty, staff) in MBM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PersonCategory(str, Enum):
    """Categories of people in MBM."""
    
    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    ALUMNI = "alumni"
    GUEST = "guest"


@dataclass
class Person:
    """
    Represents a person in the MBM system.
    
    Contains all information needed to display a person's profile
    including ASCII art, bio, and contact information.
    """
    
    # Required fields
    identifier: str  # lowercase, no spaces (used as command name)
    name: str  # Display name
    category: PersonCategory
    
    # Optional biographical info
    title: Optional[str] = None  # e.g., "Computer Science Student"
    role: Optional[str] = None  # e.g., "Student", "Professor"
    department: Optional[str] = None
    institution: Optional[str] = None
    bio: Optional[str] = None
    quote: Optional[str] = None
    
    # Contact/social
    contact: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    # Visual customization
    ascii_art: Optional[str] = None
    color: Optional[str] = None  # Rich color name
    
    # Metadata
    tags: list[str] = field(default_factory=list)
    year: Optional[int] = None  # Graduation year or joining year
    
    def __post_init__(self) -> None:
        """Validate and normalize data after initialization."""
        # Normalize identifier
        self.identifier = self.identifier.lower().replace(" ", "_")
        
        # Convert category if string
        if isinstance(self.category, str):
            self.category = PersonCategory(self.category.lower())
    
    def matches_search(self, query: str) -> bool:
        """
        Check if this person matches a search query.
        
        Args:
            query: Search string
            
        Returns:
            True if person matches the query
        """
        query = query.lower()
        
        # Check various fields
        if query in self.identifier:
            return True
        if query in self.name.lower():
            return True
        if self.department and query in self.department.lower():
            return True
        if self.role and query in self.role.lower():
            return True
        if any(query in tag.lower() for tag in self.tags):
            return True
        
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "category": self.category.value,
            "title": self.title,
            "role": self.role,
            "department": self.department,
            "institution": self.institution,
            "bio": self.bio,
            "quote": self.quote,
            "contact": self.contact,
            "email": self.email,
            "website": self.website,
            "ascii_art": self.ascii_art,
            "color": self.color,
            "tags": self.tags,
            "year": self.year,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Person:
        """Create a Person from a dictionary."""
        return cls(
            identifier=data["identifier"],
            name=data["name"],
            category=PersonCategory(data["category"]),
            title=data.get("title"),
            role=data.get("role"),
            department=data.get("department"),
            institution=data.get("institution"),
            bio=data.get("bio"),
            quote=data.get("quote"),
            contact=data.get("contact"),
            email=data.get("email"),
            website=data.get("website"),
            ascii_art=data.get("ascii_art"),
            color=data.get("color"),
            tags=data.get("tags", []),
            year=data.get("year"),
        )
