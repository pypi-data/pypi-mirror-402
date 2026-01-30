"""
Student Data

Contains all registered student profiles for MBM.
Add new students here following the Person model structure.

ASCII Art Placeholder Note:
---------------------------
The ASCII art fields below contain placeholder art. Replace with actual
ASCII/ANSI art for each person. You can generate ASCII art from images
using tools like:
- https://www.ascii-art-generator.org/
- https://patorjk.com/software/taag/ (for text)
- jp2a (command line tool)

Keep ASCII art width under 60 characters for best terminal compatibility.
"""

from mbm.people.models import Person, PersonCategory


# =============================================================================
# STUDENT PROFILES
# =============================================================================

AARYAN = Person(
    identifier="aaryan",
    name="Aaryan",
    category=PersonCategory.STUDENT,
    title="Computer Science Enthusiast & Developer",
    role="Student",
    department="Computer Science & Engineering",
    institution="MBM University, Jodhpur",
    bio=(
        "Passionate about programming languages, system design, and building "
        "tools that make a difference. Creator of the Aaryan programming language "
        "within the MBM platform. Believes in writing clean, maintainable code "
        "and open-source contribution."
    ),
    quote="Code is poetry written in logic.",
    contact="GitHub: @aaryan",
    ascii_art=r"""
       _____                            
      /     \                           
     | () () |     AARYAN              
      \  ^  /      ═══════             
       |||||       CS Developer        
       |||||       MBM University      
    """,
    color="bright_cyan",
    tags=["programming", "python", "languages", "open-source", "AI"],
    year=2026,
)


PREETI = Person(
    identifier="preeti",
    name="Preeti",
    category=PersonCategory.STUDENT,
    title="Data Science & ML Researcher",
    role="Student",
    department="Computer Science & Engineering",
    institution="MBM University, Jodhpur",
    bio=(
        "Dedicated to exploring the frontiers of machine learning and data science. "
        "Working on innovative projects that bridge theory and practical applications. "
        "Active contributor to research initiatives and academic excellence."
    ),
    quote="Data tells stories; we just need to listen.",
    contact="GitHub: @preeti",
    ascii_art=r"""
       _____                            
      /     \                           
     | () () |     PREETI              
      \  ^  /      ═══════             
       |||||       Data Scientist      
       |||||       MBM University      
    """,
    color="bright_magenta",
    tags=["data-science", "machine-learning", "python", "research", "analytics"],
    year=2026,
)


# Placeholder for more students - Add your students here!
# Copy the template below and fill in the details

STUDENT_TEMPLATE = Person(
    identifier="student_name",  # lowercase, no spaces
    name="Student Name",
    category=PersonCategory.STUDENT,
    title="Your Title Here",
    role="Student",
    department="Your Department",
    institution="MBM University, Jodhpur",
    bio="Write a brief bio here...",
    quote="Your favorite quote...",
    contact="Contact info...",
    ascii_art=r"""
    ╔═══════════════════╗
    ║   YOUR ASCII ART  ║
    ║   GOES HERE       ║
    ║                   ║
    ╚═══════════════════╝
    """,
    color="bright_green",  # Choose: bright_cyan, bright_magenta, bright_green, bright_yellow, etc.
    tags=["tag1", "tag2", "tag3"],
    year=2026,
)


# =============================================================================
# EXPORT LIST
# =============================================================================

# Add all students to this list for automatic registration
STUDENTS: list[Person] = [
    AARYAN,
    PREETI,
    # Add more students here:
    # NEW_STUDENT,
]
