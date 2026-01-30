"""
Faculty Data

Contains all registered faculty/professor profiles for MBM.
Add new faculty members here following the Person model structure.

ASCII Art Placeholder Note:
---------------------------
The ASCII art fields below contain placeholder art. Replace with actual
ASCII/ANSI art for each person. Keep ASCII art width under 60 characters
for best terminal compatibility.
"""

from mbm.people.models import Person, PersonCategory


# =============================================================================
# FACULTY PROFILES
# =============================================================================

# Placeholder faculty member - replace with actual faculty
FACULTY_EXAMPLE = Person(
    identifier="prof_sharma",
    name="Prof. Sharma",
    category=PersonCategory.FACULTY,
    title="Professor of Computer Science",
    role="Faculty",
    department="Computer Science & Engineering",
    institution="MBM University, Jodhpur",
    bio=(
        "Distinguished professor with expertise in algorithms, data structures, "
        "and software engineering. Dedicated to nurturing the next generation "
        "of computer scientists and engineers."
    ),
    quote="Teaching is the highest form of understanding.",
    contact="Email: sharma@mbm.edu",
    ascii_art=r"""
    ╔═══════════════════════════════╗
    ║     PROF. SHARMA              ║
    ║     ══════════════            ║
    ║     Computer Science          ║
    ║     MBM University            ║
    ╚═══════════════════════════════╝
    """,
    color="bright_yellow",
    tags=["algorithms", "teaching", "research", "software-engineering"],
    year=2010,  # Year joined
)


# =============================================================================
# FACULTY TEMPLATE
# =============================================================================

# Copy this template for adding new faculty members
FACULTY_TEMPLATE = Person(
    identifier="prof_name",  # lowercase, no spaces
    name="Prof. Full Name",
    category=PersonCategory.FACULTY,
    title="Professor of Subject",
    role="Faculty",
    department="Department Name",
    institution="MBM University, Jodhpur",
    bio="Professor's biography and achievements...",
    quote="Inspirational quote...",
    contact="Email: name@mbm.edu",
    ascii_art=r"""
    ╔═══════════════════╗
    ║   YOUR ASCII ART  ║
    ║   GOES HERE       ║
    ╚═══════════════════╝
    """,
    color="bright_yellow",
    tags=["expertise1", "expertise2"],
    year=2020,
)


# =============================================================================
# EXPORT LIST
# =============================================================================

# Add all faculty to this list for automatic registration
FACULTY: list[Person] = [
    FACULTY_EXAMPLE,
    # Add more faculty here:
    # NEW_FACULTY,
]
