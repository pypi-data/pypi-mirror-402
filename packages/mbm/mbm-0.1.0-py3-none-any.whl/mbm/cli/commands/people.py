"""
People CLI Commands

Commands for displaying special people profiles with ASCII art and information.
"""

from __future__ import annotations

from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mbm.core.config import get_config
from mbm.core.constants import COLORS
from mbm.people import PersonRegistry, Person


console = Console()


def display_person(person: Person) -> None:
    """
    Display a person's profile with ASCII art and information.
    
    Args:
        person: Person object to display
    """
    # Create content
    content = Text()
    
    # ASCII Art (if available)
    if person.ascii_art:
        content.append(person.ascii_art, style=person.color or COLORS['secondary'])
        content.append("\n\n")
    
    # Name and title
    content.append(person.name, style="bold bright_white")
    if person.title:
        content.append(f"\n{person.title}", style=COLORS['muted'])
    content.append("\n\n")
    
    # Role/Position
    if person.role:
        content.append("Role: ", style="bold")
        content.append(f"{person.role}\n", style=COLORS['info'])
    
    # Department
    if person.department:
        content.append("Department: ", style="bold")
        content.append(f"{person.department}\n", style=COLORS['info'])
    
    # Institution
    if person.institution:
        content.append("Institution: ", style="bold")
        content.append(f"{person.institution}\n", style=COLORS['info'])
    
    # Bio
    if person.bio:
        content.append("\n")
        content.append(person.bio, style="dim")
    
    # Quote
    if person.quote:
        content.append("\n\n")
        content.append(f'"{person.quote}"', style="italic bright_yellow")
    
    # Social/Contact
    if person.contact:
        content.append("\n\n")
        content.append("Contact: ", style="bold")
        content.append(person.contact, style=COLORS['primary'])
    
    # Tags/Skills
    if person.tags:
        content.append("\n\n")
        content.append("Tags: ", style="bold")
        content.append(" • ".join(person.tags), style=COLORS['secondary'])
    
    # Create panel
    border_color = person.color or COLORS['primary']
    panel = Panel(
        content,
        title=f"[bold {border_color}]✨ {person.name} ✨[/bold {border_color}]",
        subtitle=f"[{COLORS['muted']}]{person.category.title()}[/{COLORS['muted']}]",
        border_style=border_color,
        padding=(1, 2),
    )
    
    console.print(panel)


def get_person_command(name: str) -> click.Command:
    """
    Create a dynamic Click command for displaying a person's profile.
    
    Args:
        name: Name identifier of the person
        
    Returns:
        Click command for displaying the person
    """
    @click.command(name=name)
    @click.pass_context
    def person_command(ctx: click.Context) -> None:
        """Display profile for this person."""
        registry = PersonRegistry()
        person = registry.get(name)
        
        if person:
            display_person(person)
        else:
            console.print(f"[{COLORS['error']}]Person not found: {name}[/{COLORS['error']}]")
            ctx.exit(1)
    
    # Set docstring dynamically
    person_command.__doc__ = f"Display {name}'s profile with ASCII art and information."
    
    return person_command


@click.command(name='people')
@click.option('--category', '-c', type=click.Choice(['all', 'student', 'faculty', 'staff']), 
              default='all', help='Filter by category.')
@click.option('--list', '-l', 'list_only', is_flag=True, help='List names only.')
@click.pass_context
def list_people_command(ctx: click.Context, category: str, list_only: bool) -> None:
    """
    List all registered people in MBM.
    
    Shows students, faculty, and staff with their basic information.
    Use --category to filter by type.
    """
    registry = PersonRegistry()
    
    if category == 'all':
        people = registry.get_all()
    else:
        people = registry.get_by_category(category)
    
    if not people:
        console.print(f"[{COLORS['warning']}]No people found.[/{COLORS['warning']}]")
        return
    
    if list_only:
        # Simple list
        console.print(f"\n[{COLORS['primary']}]Registered People:[/{COLORS['primary']}]\n")
        for person in people:
            console.print(f"  • [bold]{person.name}[/bold] ({person.category})")
        console.print(f"\n[{COLORS['muted']}]Use 'mbm <name>' to view a profile[/{COLORS['muted']}]")
        return
    
    # Table view
    table = Table(
        title=f"[bold {COLORS['primary']}]MBM People Directory[/bold {COLORS['primary']}]",
        show_header=True,
        header_style=f"bold {COLORS['secondary']}",
        border_style=COLORS['muted'],
    )
    
    table.add_column("Name", style="bold")
    table.add_column("Category", style=COLORS['info'])
    table.add_column("Role", style="dim")
    table.add_column("Command", style=COLORS['success'])
    
    for person in people:
        table.add_row(
            person.name,
            person.category.title(),
            person.role or "-",
            f"mbm {person.identifier}",
        )
    
    console.print()
    console.print(table)
    console.print()
    console.print(f"[{COLORS['muted']}]Tip: Run 'mbm <name>' to view a person's full profile[/{COLORS['muted']}]")
