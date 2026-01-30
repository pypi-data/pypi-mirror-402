"""
MBM Command Shortcuts

Direct entry points for key commands so they can be run
without the 'mbm' prefix after installation.

After `pip install mbm`, these commands work directly:
  - aaryan      (instead of mbm aaryan)
  - blast       (instead of mbm blast)
  - animate     (instead of mbm animate)
  - students    (instead of mbm students)
"""

from __future__ import annotations

import sys


def aaryan_shortcut():
    """Direct entry point for 'aaryan' command."""
    from mbm.cli.commands.aaryan import aaryan_group
    sys.exit(aaryan_group(standalone_mode=True))


def blast_shortcut():
    """Direct entry point for 'blast' command."""
    from mbm.cli.commands.blast import blast_command
    sys.exit(blast_command(standalone_mode=True))


def animate_shortcut():
    """Direct entry point for 'animate' command."""
    from mbm.cli.commands.student_birthday import animation_demo_command
    sys.exit(animation_demo_command(standalone_mode=True))


def students_shortcut():
    """Direct entry point for 'students' command."""
    from mbm.cli.commands.student_birthday import list_students_command
    sys.exit(list_students_command(standalone_mode=True))
