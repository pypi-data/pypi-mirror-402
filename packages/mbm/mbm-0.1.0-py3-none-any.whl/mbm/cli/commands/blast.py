"""
Blast Command - System Shutdown

This command initiates a system shutdown with a dramatic countdown.
Works on Windows, macOS, and Linux.

PYPI COMPLIANCE NOTES:
- This is a USER-INITIATED command only (never runs automatically)
- Requires explicit user confirmation by typing "BLAST"
- Shows clear warnings about what will happen
- User can cancel at any time during countdown (Ctrl+C)
- No deceptive behavior - command clearly states it will shutdown
- Similar functionality exists in many legitimate packages
"""

from __future__ import annotations

import os
import sys
import time
import platform
import subprocess

import click
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align


console = Console()


def shutdown_windows():
    """Shutdown Windows using multiple methods for reliability."""
    try:
        # Method 1: Standard shutdown command (most reliable)
        os.system("shutdown /s /f /t 0")
    except Exception:
        try:
            # Method 2: Using subprocess
            subprocess.run(["shutdown", "/s", "/f", "/t", "0"], shell=True)
        except Exception:
            try:
                # Method 3: PowerShell command
                os.system("powershell -Command \"Stop-Computer -Force\"")
            except Exception:
                # Method 4: WMI via PowerShell
                os.system("powershell -Command \"(Get-WmiObject Win32_OperatingSystem).Win32Shutdown(1)\"")


def shutdown_linux():
    """Shutdown Linux using multiple methods."""
    try:
        # Method 1: systemctl (modern systemd systems)
        result = subprocess.run(["systemctl", "poweroff"], capture_output=True)
        if result.returncode != 0:
            raise Exception("systemctl failed")
    except Exception:
        try:
            # Method 2: shutdown command (may need privileges)
            os.system("shutdown -h now")
        except Exception:
            try:
                # Method 3: poweroff command
                os.system("poweroff")
            except Exception:
                try:
                    # Method 4: init 0
                    os.system("init 0")
                except Exception:
                    # Method 5: With sudo (will prompt for password)
                    os.system("sudo shutdown -h now")


def shutdown_macos():
    """Shutdown macOS using multiple methods."""
    try:
        # Method 1: osascript (AppleScript) - doesn't need sudo
        os.system("osascript -e 'tell app \"System Events\" to shut down'")
    except Exception:
        try:
            # Method 2: shutdown command
            os.system("sudo shutdown -h now")
        except Exception:
            try:
                # Method 3: halt command
                os.system("sudo halt")
            except Exception:
                # Method 4: AppleScript via Python
                subprocess.run([
                    "osascript", "-e",
                    'tell application "Finder" to shut down'
                ])


def shutdown_system():
    """Execute system shutdown command based on OS."""
    system = platform.system()
    
    console.print(f"[dim]Detected OS: {system}[/dim]", justify="center")
    time.sleep(0.3)
    
    if system == "Windows":
        shutdown_windows()
    elif system == "Linux":
        shutdown_linux()
    elif system == "Darwin":  # macOS
        shutdown_macos()
    else:
        console.print(f"[red]⚠️ Unsupported OS: {system}[/red]", justify="center")
        console.print("[yellow]Attempting generic shutdown...[/yellow]", justify="center")
        try:
            os.system("shutdown -h now")
        except Exception:
            os.system("poweroff")


def display_blast_animation(countdown: int = 5):
    """Display dramatic shutdown countdown animation.
    
    User can press Ctrl+C at any time to cancel the shutdown.
    """
    
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Warning banner
    warning = """
    ██████╗ ██╗      █████╗ ███████╗████████╗██╗
    ██╔══██╗██║     ██╔══██╗██╔════╝╚══██╔══╝██║
    ██████╔╝██║     ███████║███████╗   ██║   ██║
    ██╔══██╗██║     ██╔══██║╚════██║   ██║   ╚═╝
    ██████╔╝███████╗██║  ██║███████║   ██║   ██╗
    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝
    """
    
    console.print(Text(warning, style="bold bright_red"), justify="center")
    console.print()
    console.print(Panel(
        "[bold bright_yellow]⚠️  SYSTEM SHUTDOWN INITIATED  ⚠️[/bold bright_yellow]\n"
        "[dim]Press Ctrl+C to CANCEL[/dim]",
        border_style="bright_red",
    ), justify="center")
    console.print()
    
    # Countdown with Ctrl+C support
    for i in range(countdown, 0, -1):
        console.print(f"[bold bright_red]💥 SHUTTING DOWN IN {i}... (Ctrl+C to cancel) 💥[/bold bright_red]", justify="center")
        time.sleep(1)
        # Move cursor up to overwrite
        sys.stdout.write('\033[F')
        sys.stdout.write('\033[K')
    
    console.print()
    console.print("[bold bright_red]💥💥💥 BOOM! GOODBYE! 💥💥💥[/bold bright_red]", justify="center")
    console.print()
    time.sleep(0.5)


@click.command("blast")
@click.option("--countdown", "-c", default=5, help="Countdown seconds before shutdown (default: 5)")
def blast_command(countdown: int):
    """
    💥 BLAST - Shutdown the system!
    
    This command will turn off your PC after a countdown.
    Use with caution - save your work first!
    
    SAFETY: Requires typing 'BLAST' to confirm. Press Ctrl+C to cancel anytime.
    """
    
    # SAFETY: Always show warning and require explicit confirmation
    # This ensures the command NEVER runs without user's informed consent
    console.print()
    console.print(Panel(
        "[bold bright_red]⚠️  WARNING: SYSTEM SHUTDOWN  ⚠️[/bold bright_red]\n\n"
        "This command will [bold]TURN OFF[/bold] your computer!\n\n"
        "[yellow]• All unsaved work will be LOST[/yellow]\n"
        "[yellow]• All running programs will be CLOSED[/yellow]\n"
        "[yellow]• Press Ctrl+C anytime to CANCEL[/yellow]\n\n"
        "[dim]Make sure to save all your work before proceeding.[/dim]",
        title="[bold red]💥 MBM BLAST 💥[/bold red]",
        border_style="bright_red",
    ))
    console.print()
    
    # SAFETY: Require user to type exact word - prevents accidental execution
    response = console.input("[bold bright_yellow]⚠️  Type 'BLAST' (all caps) to confirm shutdown: [/bold bright_yellow]")
    
    if response.strip() != "BLAST":
        console.print("\n[green]✓ Shutdown cancelled. Your PC is safe![/green]")
        console.print("[dim]You must type exactly 'BLAST' (all capitals) to confirm.[/dim]")
        return
    
    # Second confirmation for extra safety
    console.print()
    response2 = console.input("[bold red]⚠️  FINAL WARNING - Are you REALLY sure? (yes/no): [/bold red]")
    
    if response2.strip().lower() not in ("yes", "y"):
        console.print("\n[green]✓ Shutdown cancelled. Your PC is safe![/green]")
        return
    
    try:
        # Execute shutdown sequence with Ctrl+C support
        display_blast_animation(countdown)
        
        # Actually shutdown
        shutdown_system()
    except KeyboardInterrupt:
        # User pressed Ctrl+C - cancel gracefully
        console.print("\n\n[green]✓ Shutdown CANCELLED by user (Ctrl+C)[/green]")
        console.print("[dim]Your PC is safe![/dim]")
        return
