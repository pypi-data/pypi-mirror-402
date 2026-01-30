"""
Student Birthday CLI Commands

Display student profiles with real-time birthday countdown.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from mbm.core.constants import COLORS
from mbm.utils.birthday import BirthdayCalculator, BirthdayStatus
from mbm.utils.animations import BirthdayDisplay, ASCIIAnimations
from mbm.people.data.student_database import (
    Student,
    Branch,
    STUDENT_MAP,
    get_all_students,
    get_students_by_branch,
    get_all_identifiers,
    BRANCH_SUMMARY,
    TOTAL_STUDENTS,
)


console = Console()


def display_student_birthday(student: Student) -> None:
    """
    Display student profile with real-time birthday countdown.
    
    Args:
        student: Student object to display
    """
    # Parse birth date
    birth_date = BirthdayCalculator.parse_date(student.dob)
    
    if not birth_date:
        console.print(f"[red]Error: Could not parse birth date '{student.dob}'[/red]")
        return
    
    # Calculate birthday info
    now = datetime.now()
    birthday_info = BirthdayCalculator.calculate(student.name, birth_date, now)
    
    # Get zodiac sign
    zodiac_sign, zodiac_emoji = BirthdayCalculator.get_zodiac_sign(birth_date)
    
    # Determine if today/tomorrow
    is_today = birthday_info.status == BirthdayStatus.TODAY
    is_tomorrow = birthday_info.status == BirthdayStatus.TOMORROW
    
    # Create display
    display = BirthdayDisplay(console)
    
    display.display_birthday_info(
        name=student.name,
        birth_date_str=birthday_info.formatted_date,
        days=birthday_info.days_remaining,
        hours=birthday_info.hours_remaining,
        minutes=birthday_info.minutes_remaining,
        seconds=birthday_info.seconds_remaining,
        current_age=birthday_info.current_age,
        turning_age=birthday_info.age_turning,
        zodiac_sign=zodiac_sign,
        zodiac_emoji=zodiac_emoji,
        is_today=is_today,
        is_tomorrow=is_tomorrow,
        branch=student.branch.value,
        registration_no=student.registration_no,
        enrollment_no=student.enrollment_no,
    )


def get_student_command(identifier: str) -> Optional[Student]:
    """
    Get student by their CLI identifier.
    
    Args:
        identifier: Student's CLI command identifier
        
    Returns:
        Student if found, None otherwise
    """
    return STUDENT_MAP.get(identifier.lower())


@click.command("students")
@click.option("--branch", "-b", type=str, help="Filter by branch code (e.g., CSE, EE, ME)")
@click.option("--search", "-s", type=str, help="Search students by name")
@click.option("--upcoming", "-u", is_flag=True, help="Show upcoming birthdays")
def list_students_command(branch: Optional[str], search: Optional[str], upcoming: bool):
    """List all students or filter by criteria."""
    
    students = get_all_students()
    
    # Filter by branch
    if branch:
        branch_upper = branch.upper()
        branch_map = {
            "AIDS": Branch.AI_DS, "AI_DS": Branch.AI_DS, "AI": Branch.AI_DS,
            "CHEM": Branch.CHEMICAL, "CHEMICAL": Branch.CHEMICAL,
            "CIVIL": Branch.CIVIL, "CE": Branch.CIVIL,
            "CSE": Branch.CSE, "CS": Branch.CSE,
            "EE": Branch.EE, "ELECTRICAL": Branch.EE,
            "ECE": Branch.ECE,
            "ECC": Branch.ECC,
            "EEE": Branch.EEE,
            "IT": Branch.IT,
            "ME": Branch.ME, "MECH": Branch.ME, "MECHANICAL": Branch.ME,
            "MINING": Branch.MINING, "MINE": Branch.MINING,
            "PETRO": Branch.PETROLEUM, "PETROLEUM": Branch.PETROLEUM,
            "PIE": Branch.PIE, "PRODUCTION": Branch.PIE,
        }
        
        if branch_upper in branch_map:
            students = get_students_by_branch(branch_map[branch_upper])
        else:
            console.print(f"[red]Unknown branch: {branch}[/red]")
            console.print("Available branches: AIDS, CHEM, CIVIL, CSE, EE, ECE, ECC, EEE, IT, ME, MINING, PETRO, PIE")
            return
    
    # Filter by search
    if search:
        search_lower = search.lower()
        students = [s for s in students if search_lower in s.name.lower()]
    
    # Show upcoming birthdays
    if upcoming:
        now = datetime.now()
        birthday_students = []
        
        for student in students:
            birth_date = BirthdayCalculator.parse_date(student.dob)
            if birth_date:
                info = BirthdayCalculator.calculate(student.name, birth_date, now)
                if info.days_remaining <= 30:  # Within 30 days
                    birthday_students.append((student, info))
        
        # Sort by days remaining
        birthday_students.sort(key=lambda x: x[1].days_remaining)
        
        if not birthday_students:
            console.print("[yellow]No upcoming birthdays in the next 30 days.[/yellow]")
            return
        
        # Display table
        table = Table(
            title="🎂 Upcoming Birthdays (Next 30 Days)",
            title_style="bold bright_magenta",
            border_style="bright_cyan",
        )
        
        table.add_column("Name", style="bright_white")
        table.add_column("Branch", style="bright_green")
        table.add_column("Birthday", style="bright_cyan")
        table.add_column("Days Left", style="bright_yellow")
        table.add_column("Status", style="bright_magenta")
        
        for student, info in birthday_students:
            status = ""
            if info.status == BirthdayStatus.TODAY:
                status = "🎂 TODAY!"
            elif info.status == BirthdayStatus.TOMORROW:
                status = "🎉 Tomorrow!"
            elif info.status == BirthdayStatus.THIS_WEEK:
                status = "📅 This Week"
            else:
                status = "📆 This Month"
            
            days_str = str(info.days_remaining) if info.days_remaining > 0 else "NOW!"
            
            table.add_row(
                student.name,
                student.branch.name,
                info.next_birthday.strftime("%b %d"),
                days_str,
                status,
            )
        
        console.print()
        console.print(table)
        return
    
    # Regular listing
    if not students:
        console.print("[yellow]No students found.[/yellow]")
        return
    
    # Group by branch if not filtered
    if not branch:
        # Show summary
        console.print()
        console.print(Panel(
            f"[bold]Total Students: {TOTAL_STUDENTS}[/bold]",
            title="[bold bright_cyan]MBM University Student Database[/bold bright_cyan]",
            border_style="bright_blue",
        ))
        
        table = Table(
            title="Students by Branch",
            title_style="bold bright_cyan",
            border_style="bright_blue",
        )
        
        table.add_column("Branch", style="bright_green")
        table.add_column("Students", style="bright_yellow", justify="right")
        
        for b, count in BRANCH_SUMMARY.items():
            table.add_row(b.value, str(count))
        
        console.print(table)
        console.print()
        console.print("[dim]Use --branch/-b to filter by branch[/dim]")
        console.print("[dim]Use --search/-s to search by name[/dim]")
        console.print("[dim]Use --upcoming/-u to show upcoming birthdays[/dim]")
        console.print()
        console.print("[dim]Run: mbm <student_name> to see their birthday countdown[/dim]")
    else:
        # Show students in branch
        table = Table(
            title=f"Students - {students[0].branch.value if students else 'Unknown'}",
            title_style="bold bright_cyan",
            border_style="bright_blue",
        )
        
        table.add_column("#", style="dim")
        table.add_column("Name", style="bright_white")
        table.add_column("Command", style="bright_green")
        table.add_column("Registration", style="dim")
        table.add_column("DOB", style="bright_cyan")
        
        for i, student in enumerate(students, 1):
            table.add_row(
                str(i),
                student.name,
                f"mbm {student.identifier}",
                student.registration_no,
                student.dob,
            )
        
        console.print()
        console.print(table)
        console.print()
        console.print("[dim]Total: {len(students)} students[/dim]")


def print_student_commands_help():
    """Print help about student commands."""
    console.print()
    console.print(Panel(
        "[bold]Student Birthday Commands[/bold]\n\n"
        "Run [bright_cyan]mbm <student_name>[/bright_cyan] to see their birthday countdown.\n\n"
        "[bold]Examples:[/bold]\n"
        "  mbm aaditya_mehta     - Show Aaditya Mehta's birthday\n"
        "  mbm preeti_yadav      - Show Preeti Yadav's birthday\n"
        "  mbm students          - List all students\n"
        "  mbm students -u       - Show upcoming birthdays\n"
        "  mbm students -b CSE   - List CSE students\n",
        title="[bold bright_cyan]🎂 Birthday Countdown System[/bold bright_cyan]",
        border_style="bright_blue",
    ))


@click.command("animate")
@click.option("--confetti", "-c", is_flag=True, help="Play falling confetti animation")
@click.option("--fireworks", "-f", is_flag=True, help="Play fireworks explosion animation")
@click.option("--cake", "-k", is_flag=True, help="Play animated birthday cake with flickering candles")
@click.option("--countdown", "-t", is_flag=True, help="Play countdown flip animation")
@click.option("--all", "-a", "play_all", is_flag=True, help="Play all animations")
@click.option("--name", "-n", type=str, default="Guest", help="Name to display in animations")
def animation_demo_command(confetti: bool, fireworks: bool, cake: bool, countdown: bool, play_all: bool, name: str):
    """
    🎬 Demo the moving ASCII animations.
    
    Experience the real animated terminal effects:
    - Falling confetti with physics simulation
    - Fireworks explosions with particle effects
    - Birthday cake with flickering candles
    - Countdown timer flip animation
    """
    from mbm.utils.animations import TerminalAnimator
    
    animator = TerminalAnimator(console)
    
    if not any([confetti, fireworks, cake, countdown, play_all]):
        # Show help if no option selected
        console.print()
        console.print(Panel(
            "[bold]🎬 ASCII Animation Demo[/bold]\n\n"
            "[bold]Available Animations:[/bold]\n"
            "  [bright_cyan]--confetti, -c[/bright_cyan]   Falling confetti with physics\n"
            "  [bright_cyan]--fireworks, -f[/bright_cyan]  Fireworks explosions\n"
            "  [bright_cyan]--cake, -k[/bright_cyan]       Birthday cake with flickering candles\n"
            "  [bright_cyan]--countdown, -t[/bright_cyan]  Countdown flip animation\n"
            "  [bright_cyan]--all, -a[/bright_cyan]        Play ALL animations\n\n"
            "[bold]Options:[/bold]\n"
            "  [bright_cyan]--name, -n[/bright_cyan]       Name to display (default: Guest)\n\n"
            "[bold]Examples:[/bold]\n"
            "  mbm animate --confetti\n"
            "  mbm animate --fireworks --name \"John Doe\"\n"
            "  mbm animate --all --name \"Birthday Person\"",
            title="[bold bright_magenta]Animation System[/bold bright_magenta]",
            border_style="bright_magenta",
        ))
        return
    
    if play_all or confetti:
        console.print("\n[bold bright_cyan]🎊 Playing: Falling Confetti Animation[/bold bright_cyan]")
        animator.animate_falling_confetti(duration=3.0, message=f"★ {name.upper()} ★")
    
    if play_all or fireworks:
        console.print("\n[bold bright_yellow]🎆 Playing: Fireworks Animation[/bold bright_yellow]")
        animator.animate_fireworks(bursts=3, message=f"🎉 {name.upper()} 🎉")
    
    if play_all or cake:
        console.print("\n[bold bright_magenta]🎂 Playing: Birthday Cake Animation[/bold bright_magenta]")
        animator.animate_cake_candles(name, duration=3.0)
    
    if play_all or countdown:
        console.print("\n[bold bright_green]⏰ Playing: Countdown Flip Animation[/bold bright_green]")
        animator.animate_countdown_flip(days=5, hours=12, mins=30, secs=45, duration=2.5)
    
    # Final message
    animator.clear_screen()
    console.print()
    console.print(Panel(
        f"[bold bright_green]✅ Animation Demo Complete![/bold bright_green]\n\n"
        f"These animations play automatically when viewing birthday info:\n"
        f"  • [bright_yellow]Birthday TODAY[/bright_yellow] → Fireworks + Cake + Confetti\n"
        f"  • [bright_cyan]Birthday TOMORROW[/bright_cyan] → Countdown flip animation\n"
        f"  • [bright_green]Birthday THIS WEEK[/bright_green] → Typing text effect",
        title="[bold]🎬 Demo Finished[/bold]",
        border_style="bright_green",
    ))
