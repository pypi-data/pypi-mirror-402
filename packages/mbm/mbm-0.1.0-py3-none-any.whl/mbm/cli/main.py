"""
MBM Main CLI Entry Point

This module serves as the main entry point for the MBM CLI platform.
It sets up the command structure and routes to appropriate subcommands.
"""

from __future__ import annotations

import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from mbm.core.config import get_config, set_config, MBMConfig
from mbm.core.constants import (
    APP_NAME,
    APP_VERSION,
    BANNER,
    BANNER_SUBTITLE,
    COLORS,
    EXIT_SUCCESS,
)
from mbm.cli.commands.aaryan import aaryan_group
from mbm.cli.commands.ai import ai_command
from mbm.cli.commands.people import get_person_command, list_people_command
from mbm.cli.commands.student_birthday import (
    list_students_command,
    get_student_command,
    display_student_birthday,
    animation_demo_command,
)
from mbm.cli.commands.blast import blast_command
from mbm.people import PersonRegistry
from mbm.people.data.student_database import STUDENT_MAP, get_all_identifiers


# Initialize Rich console
console = Console()


def print_banner() -> None:
    """Display the MBM ASCII banner with styling."""
    banner_text = Text()
    banner_text.append(BANNER, style=f"bold {COLORS['primary']}")
    
    console.print(banner_text, justify="center")
    console.print(
        f"[{COLORS['secondary']}]{BANNER_SUBTITLE}[/{COLORS['secondary']}]",
        justify="center",
    )
    console.print(
        f"[{COLORS['muted']}]Version {APP_VERSION}[/{COLORS['muted']}]",
        justify="center",
    )
    console.print()


def print_help_panel() -> None:
    """Display the help panel with available commands."""
    help_content = Text()
    
    # Usage section
    help_content.append("USAGE\n", style="bold bright_white")
    help_content.append("  mbm                      ", style="bright_cyan")
    help_content.append("Show this help\n", style="dim")
    help_content.append("  mbm aaryan               ", style="bright_cyan")
    help_content.append("Aaryan language module\n", style="dim")
    help_content.append("  mbm aaryan run <file>    ", style="bright_cyan")
    help_content.append("Run an Aaryan program\n", style="dim")
    help_content.append("  mbm ai                   ", style="bright_cyan")
    help_content.append("Start AI assistant\n", style="dim")
    help_content.append("  mbm <person>             ", style="bright_cyan")
    help_content.append("View person's profile\n", style="dim")
    help_content.append("  mbm people               ", style="bright_cyan")
    help_content.append("List all people\n\n", style="dim")
    
    # Examples section
    help_content.append("EXAMPLES\n", style="bold bright_white")
    help_content.append("  mbm aaryan run hello.ar\n", style="bright_green")
    help_content.append("  mbm ai\n", style="bright_green")
    help_content.append("  mbm preeti\n\n", style="bright_green")
    
    # Info section
    help_content.append("MORE INFO\n", style="bold bright_white")
    help_content.append("  mbm --help               ", style="bright_yellow")
    help_content.append("Full help\n", style="dim")
    help_content.append("  mbm --version            ", style="bright_yellow")
    help_content.append("Version info\n", style="dim")
    
    panel = Panel(
        help_content,
        title=f"[bold {COLORS['primary']}]MBM CLI Platform[/bold {COLORS['primary']}]",
        border_style=COLORS['primary'],
        padding=(1, 2),
    )
    console.print(panel)


class MBMGroup(click.Group):
    """
    Custom Click Group that handles dynamic person and student commands.
    
    This allows commands like 'mbm aaryan', 'mbm preeti_yadav' etc. to work
    dynamically based on registered people and students.
    """
    
    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """
        Get a command by name, with fallback to person/student lookup.
        
        Args:
            ctx: Click context
            cmd_name: Command name to look up
            
        Returns:
            Click command if found, None otherwise
        """
        # First, try to get a registered command
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        
        # Check if it's a student identifier (new student database)
        cmd_lower = cmd_name.lower()
        if cmd_lower in STUDENT_MAP:
            # Create a dynamic command for this student
            student = STUDENT_MAP[cmd_lower]
            
            @click.command(name=cmd_lower)
            def student_cmd(s=student):
                """Display student birthday countdown."""
                display_student_birthday(s)
            
            student_cmd.__doc__ = f"Show {student.name}'s birthday countdown"
            return student_cmd
        
        # Check if it's a person name (legacy people system)
        registry = PersonRegistry()
        if registry.exists(cmd_name):
            return get_person_command(cmd_name)
        
        return None
    
    def list_commands(self, ctx: click.Context) -> list[str]:
        """
        List all available commands including dynamic person/student commands.
        
        Args:
            ctx: Click context
            
        Returns:
            List of command names
        """
        # Get static commands
        commands = list(super().list_commands(ctx))
        
        # Add student identifiers
        for identifier in get_all_identifiers():
            if identifier not in commands:
                commands.append(identifier)
        
        # Add person names (but don't duplicate if exists)
        registry = PersonRegistry()
        for name in registry.list_all():
            if name not in commands:
                commands.append(name)
        
        return sorted(commands)


@click.group(cls=MBMGroup, invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version and exit.')
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@click.option('--no-color', is_flag=True, help='Disable colored output.')
@click.pass_context
def cli(ctx: click.Context, version: bool, verbose: bool, debug: bool, no_color: bool) -> None:
    """
    MBM - Modular CLI Platform
    
    A powerful command-line interface featuring the Aaryan programming
    language and an intelligent AI assistant.
    
    Run 'mbm' with no arguments to see available commands.
    """
    # Initialize context
    ctx.ensure_object(dict)
    
    # Configure based on flags
    config = get_config()
    config.verbose = verbose
    config.debug = debug
    config.color_enabled = not no_color
    set_config(config)
    
    # Store in context for subcommands
    ctx.obj['config'] = config
    ctx.obj['console'] = console
    
    # Handle --version flag
    if version:
        console.print(f"[{COLORS['primary']}]{APP_NAME}[/{COLORS['primary']}] version [{COLORS['secondary']}]{APP_VERSION}[/{COLORS['secondary']}]")
        ctx.exit(EXIT_SUCCESS)
    
    # If no subcommand provided, show banner and help
    if ctx.invoked_subcommand is None:
        print_banner()
        print_help_panel()


# Register static commands
cli.add_command(aaryan_group, name='aaryan')
cli.add_command(ai_command, name='ai')
cli.add_command(list_people_command, name='people')
cli.add_command(list_students_command, name='students')
cli.add_command(animation_demo_command, name='animate')
cli.add_command(blast_command, name='blast')


def main() -> int:
    """
    Main entry point for the MBM CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        cli(obj={})
        return EXIT_SUCCESS
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]Interrupted by user[/{COLORS['warning']}]")
        return 130
    except Exception as e:
        console.print(f"[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
        config = get_config()
        if config.debug:
            console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main())
