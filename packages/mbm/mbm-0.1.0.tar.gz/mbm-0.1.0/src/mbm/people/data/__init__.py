"""
People Data Module

Contains the data for all registered people in MBM.
"""

from mbm.people.data.students import STUDENTS
from mbm.people.data.faculty import FACULTY
from mbm.people.data.student_database import (
    Student,
    Branch,
    get_all_students,
    get_students_by_branch,
    get_student_by_identifier,
    STUDENT_MAP,
    TOTAL_STUDENTS,
    BRANCH_SUMMARY,
)

__all__ = [
    "STUDENTS",
    "FACULTY",
    "Student",
    "Branch",
    "get_all_students",
    "get_students_by_branch",
    "get_student_by_identifier",
    "STUDENT_MAP",
    "TOTAL_STUDENTS",
    "BRANCH_SUMMARY",
]
