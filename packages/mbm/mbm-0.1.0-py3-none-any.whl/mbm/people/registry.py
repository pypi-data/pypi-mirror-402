"""
People Registry

Central registry for managing all people profiles in MBM.
Handles registration, lookup, and organization of people data.
"""

from __future__ import annotations

from typing import Optional

from mbm.people.models import Person, PersonCategory
from mbm.people.data.students import STUDENTS
from mbm.people.data.faculty import FACULTY


class PersonRegistry:
    """
    Central registry for all people in MBM.
    
    Provides methods to register, lookup, and manage people profiles.
    Uses a singleton pattern to ensure consistency across the application.
    """
    
    _instance: Optional[PersonRegistry] = None
    _people: dict[str, Person]
    
    def __new__(cls) -> PersonRegistry:
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._people = {}
            cls._instance._load_default_people()
        return cls._instance
    
    def _load_default_people(self) -> None:
        """Load default people from data modules."""
        # Load students
        for person in STUDENTS:
            self.register(person)
        
        # Load faculty
        for person in FACULTY:
            self.register(person)
    
    def register(self, person: Person) -> None:
        """
        Register a person in the registry.
        
        Args:
            person: Person object to register
        """
        self._people[person.identifier] = person
    
    def unregister(self, identifier: str) -> bool:
        """
        Remove a person from the registry.
        
        Args:
            identifier: Person's identifier
            
        Returns:
            True if person was removed, False if not found
        """
        if identifier in self._people:
            del self._people[identifier]
            return True
        return False
    
    def get(self, identifier: str) -> Optional[Person]:
        """
        Get a person by identifier.
        
        Args:
            identifier: Person's identifier (case-insensitive)
            
        Returns:
            Person object if found, None otherwise
        """
        return self._people.get(identifier.lower())
    
    def exists(self, identifier: str) -> bool:
        """
        Check if a person exists in the registry.
        
        Args:
            identifier: Person's identifier
            
        Returns:
            True if person exists
        """
        return identifier.lower() in self._people
    
    def get_all(self) -> list[Person]:
        """
        Get all registered people.
        
        Returns:
            List of all Person objects
        """
        return list(self._people.values())
    
    def get_by_category(self, category: str | PersonCategory) -> list[Person]:
        """
        Get all people in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of Person objects in the category
        """
        if isinstance(category, str):
            category = PersonCategory(category.lower())
        
        return [p for p in self._people.values() if p.category == category]
    
    def search(self, query: str) -> list[Person]:
        """
        Search for people matching a query.
        
        Args:
            query: Search string
            
        Returns:
            List of matching Person objects
        """
        return [p for p in self._people.values() if p.matches_search(query)]
    
    def list_all(self) -> list[str]:
        """
        List all registered person identifiers.
        
        Returns:
            List of identifiers
        """
        return list(self._people.keys())
    
    def count(self) -> int:
        """
        Get the total number of registered people.
        
        Returns:
            Count of people
        """
        return len(self._people)
    
    def clear(self) -> None:
        """Clear all registered people (mainly for testing)."""
        self._people.clear()
    
    def reload(self) -> None:
        """Reload all default people."""
        self.clear()
        self._load_default_people()
