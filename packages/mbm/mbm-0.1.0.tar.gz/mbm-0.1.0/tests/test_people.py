"""
Tests for the People module.
"""

import pytest

from mbm.people import PersonRegistry, Person, PersonCategory


class TestPerson:
    """Tests for the Person model."""
    
    def test_create_person(self):
        person = Person(
            identifier="test_person",
            name="Test Person",
            category=PersonCategory.STUDENT,
            title="Test Title",
        )
        
        assert person.identifier == "test_person"
        assert person.name == "Test Person"
        assert person.category == PersonCategory.STUDENT
    
    def test_identifier_normalization(self):
        person = Person(
            identifier="Test Person",
            name="Test",
            category=PersonCategory.STUDENT,
        )
        
        assert person.identifier == "test_person"
    
    def test_matches_search(self):
        person = Person(
            identifier="john",
            name="John Doe",
            category=PersonCategory.STUDENT,
            department="Computer Science",
            tags=["python", "ai"],
        )
        
        assert person.matches_search("john")
        assert person.matches_search("doe")
        assert person.matches_search("computer")
        assert person.matches_search("python")
        assert not person.matches_search("xyz")
    
    def test_to_dict(self):
        person = Person(
            identifier="test",
            name="Test",
            category=PersonCategory.FACULTY,
            bio="Test bio",
        )
        
        data = person.to_dict()
        
        assert data["identifier"] == "test"
        assert data["name"] == "Test"
        assert data["category"] == "faculty"
        assert data["bio"] == "Test bio"
    
    def test_from_dict(self):
        data = {
            "identifier": "test",
            "name": "Test Person",
            "category": "student",
            "bio": "Test bio",
        }
        
        person = Person.from_dict(data)
        
        assert person.identifier == "test"
        assert person.name == "Test Person"
        assert person.category == PersonCategory.STUDENT


class TestPersonRegistry:
    """Tests for the PersonRegistry."""
    
    def test_registry_singleton(self):
        registry1 = PersonRegistry()
        registry2 = PersonRegistry()
        
        assert registry1 is registry2
    
    def test_default_people_loaded(self):
        registry = PersonRegistry()
        
        # Should have default people loaded
        assert registry.count() > 0
        assert registry.exists("aaryan")
        assert registry.exists("preeti")
    
    def test_get_person(self):
        registry = PersonRegistry()
        
        person = registry.get("aaryan")
        
        assert person is not None
        assert person.name == "Aaryan"
        assert person.category == PersonCategory.STUDENT
    
    def test_get_by_category(self):
        registry = PersonRegistry()
        
        students = registry.get_by_category("student")
        
        assert len(students) >= 2  # At least Aaryan and Preeti
        assert all(p.category == PersonCategory.STUDENT for p in students)
    
    def test_search(self):
        registry = PersonRegistry()
        
        results = registry.search("computer")
        
        assert len(results) > 0
    
    def test_list_all(self):
        registry = PersonRegistry()
        
        names = registry.list_all()
        
        assert "aaryan" in names
        assert "preeti" in names


class TestPersonCategory:
    """Tests for PersonCategory enum."""
    
    def test_category_values(self):
        assert PersonCategory.STUDENT.value == "student"
        assert PersonCategory.FACULTY.value == "faculty"
        assert PersonCategory.STAFF.value == "staff"
        assert PersonCategory.ALUMNI.value == "alumni"
