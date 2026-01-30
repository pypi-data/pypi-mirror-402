"""
ASCII Animations Module - Moving Art in Text Mode

Real animated terminal animations for celebrations including:
- Falling confetti with physics simulation
- Flickering candles on birthday cakes
- Typing text effects
- Pulsing/blinking effects
- Matrix-style rain effects
- Firework explosions
"""

from __future__ import annotations

import random
import time
import sys
import os
from typing import List, Optional, Tuple
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.table import Table
import rich.box


# Color palettes for celebrations
CONFETTI_COLORS = [
    "bright_red", "bright_green", "bright_yellow", "bright_blue",
    "bright_magenta", "bright_cyan", "red", "green", "yellow",
    "blue", "magenta", "cyan", "orange1", "deep_pink1", "gold1",
    "spring_green1", "turquoise2", "violet", "chartreuse1"
]

CONFETTI_CHARS = ['*', '•', '°', '✦', '✧', '★', '☆', '❋', '❊', '✴', '✵', '❄', '♦', '♥', '♠', '♣', '◆', '●', '○', '◇']
SPARKLE_CHARS = ['✨', '⭐', '🌟', '💫', '✦', '✧', '★', '☆', '·', '•', '*']
CANDLE_FLAMES = ['🔥', '🕯️', '✨', '💫', '*', '·', ' ']
FIREWORK_CHARS = ['✺', '✹', '✸', '✷', '✶', '✵', '✴', '*', '·', '.', ' ']


class ConfettiParticle:
    """A single confetti particle with physics."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.char = random.choice(CONFETTI_CHARS)
        self.color = random.choice(CONFETTI_COLORS)
        self.velocity_x = random.uniform(-0.5, 0.5)
        self.velocity_y = random.uniform(0.3, 1.0)
        self.alive = True
    
    def update(self):
        """Update particle position."""
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Add slight horizontal wobble
        self.velocity_x += random.uniform(-0.1, 0.1)
        self.velocity_x = max(-1, min(1, self.velocity_x))
        
        # Check bounds
        if self.y >= self.height or self.x < 0 or self.x >= self.width:
            self.alive = False


class FireworkParticle:
    """A firework explosion particle."""
    
    def __init__(self, x: int, y: int, angle: float, speed: float):
        import math
        self.x = x
        self.y = y
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
        self.color = random.choice(CONFETTI_COLORS)
        self.life = 1.0
        self.char_index = 0
    
    def update(self):
        """Update particle with gravity and fading."""
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.1  # Gravity
        self.life -= 0.1
        self.char_index = min(len(FIREWORK_CHARS) - 1, int((1 - self.life) * len(FIREWORK_CHARS)))
    
    @property
    def char(self) -> str:
        return FIREWORK_CHARS[self.char_index]
    
    @property
    def alive(self) -> bool:
        return self.life > 0


class TerminalAnimator:
    """
    Real-time terminal animation engine.
    Handles frame rendering, timing, and screen management.
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.width = 70
        self.height = 20
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def hide_cursor(self):
        """Hide terminal cursor."""
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
    
    def show_cursor(self):
        """Show terminal cursor."""
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
    
    def move_cursor(self, x: int, y: int):
        """Move cursor to position."""
        sys.stdout.write(f'\033[{y};{x}H')
        sys.stdout.flush()
    
    def animate_falling_confetti(self, duration: float = 3.0, message: str = ""):
        """
        Animate falling confetti particles.
        Real physics-based falling animation.
        """
        particles: List[ConfettiParticle] = []
        start_time = time.time()
        frame_count = 0
        
        try:
            self.hide_cursor()
            
            while time.time() - start_time < duration:
                # Spawn new particles at top
                if random.random() < 0.4:
                    x = random.randint(0, self.width - 1)
                    particles.append(ConfettiParticle(x, 0, self.width, self.height))
                
                # Create frame buffer
                frame = [[' ' for _ in range(self.width)] for _ in range(self.height)]
                colors = [[None for _ in range(self.width)] for _ in range(self.height)]
                
                # Update and render particles
                alive_particles = []
                for p in particles:
                    p.update()
                    if p.alive:
                        alive_particles.append(p)
                        px, py = int(p.x), int(p.y)
                        if 0 <= px < self.width and 0 <= py < self.height:
                            frame[py][px] = p.char
                            colors[py][px] = p.color
                
                particles = alive_particles
                
                # Add message in center if provided
                if message:
                    msg_y = self.height // 2
                    msg_x = (self.width - len(message)) // 2
                    for i, ch in enumerate(message):
                        if 0 <= msg_x + i < self.width:
                            frame[msg_y][msg_x + i] = ch
                            colors[msg_y][msg_x + i] = "bold bright_magenta"
                
                # Render frame with Rich
                text = Text()
                for y in range(self.height):
                    for x in range(self.width):
                        char = frame[y][x]
                        color = colors[y][x]
                        if color:
                            text.append(char, style=color)
                        else:
                            text.append(char)
                    text.append("\n")
                
                # Clear and print
                self.clear_screen()
                self.console.print(text)
                
                frame_count += 1
                time.sleep(0.05)  # ~20 FPS
        
        finally:
            self.show_cursor()
    
    def animate_fireworks(self, bursts: int = 3, message: str = ""):
        """
        Animate firework explosions.
        Multiple bursts with expanding particles.
        """
        import math
        
        all_particles: List[FireworkParticle] = []
        
        try:
            self.hide_cursor()
            
            for burst in range(bursts):
                # Create explosion at random position
                cx = random.randint(15, self.width - 15)
                cy = random.randint(5, self.height - 5)
                
                # Create particles in all directions
                for i in range(20):
                    angle = (2 * math.pi * i) / 20
                    speed = random.uniform(1, 2)
                    all_particles.append(FireworkParticle(cx, cy, angle, speed))
                
                # Animate this burst
                for _ in range(15):
                    frame = [[' ' for _ in range(self.width)] for _ in range(self.height)]
                    colors = [[None for _ in range(self.width)] for _ in range(self.height)]
                    
                    alive = []
                    for p in all_particles:
                        p.update()
                        if p.alive:
                            alive.append(p)
                            px, py = int(p.x), int(p.y)
                            if 0 <= px < self.width and 0 <= py < self.height:
                                frame[py][px] = p.char
                                colors[py][px] = p.color
                    
                    all_particles = alive
                    
                    # Add message
                    if message:
                        msg_y = self.height - 2
                        msg_x = (self.width - len(message)) // 2
                        for i, ch in enumerate(message):
                            if 0 <= msg_x + i < self.width:
                                frame[msg_y][msg_x + i] = ch
                                colors[msg_y][msg_x + i] = "bold bright_yellow"
                    
                    # Render
                    text = Text()
                    for y in range(self.height):
                        for x in range(self.width):
                            char = frame[y][x]
                            color = colors[y][x]
                            if color:
                                text.append(char, style=color)
                            else:
                                text.append(char)
                        text.append("\n")
                    
                    self.clear_screen()
                    self.console.print(text)
                    time.sleep(0.08)
                
                time.sleep(0.2)  # Pause between bursts
        
        finally:
            self.show_cursor()
    
    def animate_typing_text(self, text: str, style: str = "bold bright_cyan", delay: float = 0.05):
        """
        Animate text typing character by character.
        Classic typewriter effect.
        """
        for i, char in enumerate(text):
            self.console.print(char, style=style, end="")
            time.sleep(delay)
        self.console.print()
    
    def animate_pulsing_text(self, text: str, cycles: int = 5, base_style: str = "bright_magenta"):
        """
        Animate text that pulses bright/dim.
        """
        styles = [
            f"dim {base_style}",
            base_style,
            f"bold {base_style}",
            base_style,
        ]
        
        try:
            self.hide_cursor()
            for _ in range(cycles):
                for style in styles:
                    self.console.print(f"\r{text}", style=style, end="")
                    time.sleep(0.15)
            self.console.print()
        finally:
            self.show_cursor()
    
    def animate_sparkle_border(self, content: str, width: int = 50, duration: float = 2.0):
        """
        Animate a border with moving sparkles.
        """
        sparkle_positions = list(range(width))
        start_time = time.time()
        
        try:
            self.hide_cursor()
            
            while time.time() - start_time < duration:
                # Rotate sparkle positions
                random.shuffle(sparkle_positions)
                active_sparkles = set(sparkle_positions[:width//3])
                
                # Build top border
                top = ""
                for i in range(width):
                    if i in active_sparkles:
                        top += random.choice(['✨', '⭐', '★', '✦'])
                    else:
                        top += "═"
                
                # Build display
                display = Text()
                display.append(f"╔{top}╗\n", style="bright_yellow")
                display.append(f"║{content.center(width)}║\n", style="bright_cyan")
                display.append(f"╚{top}╝\n", style="bright_yellow")
                
                self.move_cursor(1, 1)
                self.console.print(display, end="")
                time.sleep(0.1)
        
        finally:
            self.show_cursor()
            self.console.print()
    
    def animate_countdown_flip(self, days: int, hours: int, mins: int, secs: int, duration: float = 3.0):
        """
        Animate countdown numbers with flip effect.
        Numbers appear to flip/change rapidly before settling.
        """
        start_time = time.time()
        final_values = [days, hours, mins, secs]
        labels = ["DAYS", "HRS", "MIN", "SEC"]
        
        try:
            self.hide_cursor()
            
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                progress = elapsed / duration
                
                text = Text()
                text.append("\n  ╔════════════════════════════════════════╗\n", style="bright_cyan")
                text.append("  ║       ⏰ BIRTHDAY COUNTDOWN ⏰        ║\n", style="bright_cyan")
                text.append("  ╠════════════════════════════════════════╣\n", style="bright_cyan")
                text.append("  ║    ", style="bright_cyan")
                
                for i, (final, label) in enumerate(zip(final_values, labels)):
                    # Calculate displayed value (random then settle to final)
                    if progress < 0.7:
                        # Still flipping
                        display_val = random.randint(0, 99) if i < 1 else random.randint(0, 59)
                    else:
                        # Settling
                        display_val = final
                    
                    text.append(f"{display_val:3d}" if i == 0 else f"{display_val:2d}", style="bold bright_white")
                    text.append(f" {label}", style="dim")
                    if i < 3:
                        text.append("  ", style="bright_cyan")
                
                text.append("  ║\n", style="bright_cyan")
                text.append("  ╚════════════════════════════════════════╝\n", style="bright_cyan")
                
                self.clear_screen()
                self.console.print(text)
                time.sleep(0.05)
        
        finally:
            self.show_cursor()
    
    def animate_cake_candles(self, name: str, duration: float = 3.0):
        """
        Animate birthday cake with flickering candles.
        Real animated flame effect.
        """
        candle_states = [0, 0, 0, 0, 0, 0, 0]  # 7 candles
        flame_chars = ['🔥', '✨', '💫', '*', '·']
        
        cake_template = '''
            {c0}  {c1}  {c2}  {c3}  {c4}  {c5}  {c6}
          ╔═══════════════════════════╗
          ║  ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥  ║
          ╠═══════════════════════════╣
          ║                           ║
          ║      🎂 HAPPY 🎂         ║
          ║       BIRTHDAY!           ║
          ║        {name}        ║
          ║                           ║
          ╠═══════════════════════════╣
          ║  ✿ ✿ ✿ ✿ ✿ ✿ ✿ ✿ ✿ ✿ ✿  ║
          ╚═══════════════════════════╝
         /█████████████████████████████\\
        /███████████████████████████████\\
'''
        
        start_time = time.time()
        
        try:
            self.hide_cursor()
            
            while time.time() - start_time < duration:
                # Update candle flames
                flames = []
                for i in range(7):
                    if random.random() < 0.3:
                        candle_states[i] = (candle_states[i] + 1) % len(flame_chars)
                    flames.append(flame_chars[candle_states[i]])
                
                # Format name to fit
                display_name = name[:15].center(15)
                
                # Build cake with current flames
                cake = cake_template.format(
                    c0=flames[0], c1=flames[1], c2=flames[2], c3=flames[3],
                    c4=flames[4], c5=flames[5], c6=flames[6],
                    name=display_name
                )
                
                self.clear_screen()
                self.console.print(Text(cake, style="bright_yellow"))
                time.sleep(0.1)
        
        finally:
            self.show_cursor()
    
    def animate_birthday_celebration(self, name: str, is_today: bool = False):
        """
        Full animated birthday celebration sequence.
        Combines multiple animation effects.
        """
        if is_today:
            # Epic celebration for birthday day
            self.console.print("\n")
            
            # 1. Fireworks
            self.animate_fireworks(bursts=2, message=f"🎂 HAPPY BIRTHDAY {name.upper()}! 🎂")
            
            # 2. Animated cake with flickering candles
            self.animate_cake_candles(name, duration=2.5)
            
            # 3. Falling confetti
            self.animate_falling_confetti(duration=2.0, message=f"✨ {name.upper()} ✨")
            
        else:
            # Subtle animation for countdown
            self.console.print("\n")
            self.animate_typing_text(f"  🎈 {name}'s Birthday Countdown 🎈", delay=0.03)
            time.sleep(0.3)


class ASCIIAnimations:
    """Collection of ASCII art and real-time animations for celebrations."""
    
    # Static cake designs (for non-animated fallback)
    CAKE_SMALL = r"""
       ___
      |   |
    __|___|__
   |  HAPPY  |
   | BIRTHDAY|
   |_________|
    """
    
    CAKE_MEDIUM = r"""
          ⁀⁀⁀
         (  🎂  )
       ____|  |____
      |   HAPPY    |
      |  BIRTHDAY! |
      |____________|
      \############/
       \##########/
        \########/
    """
    
    CAKE_LARGE = r"""
                    🕯️  🕯️  🕯️
                 ___________
                |  *  *  *  |
             ___|___________|___
            |                   |
            |   ★ HAPPY ★      |
            |    BIRTHDAY!      |
            |___________________|
           /#####################\\
          /  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~  \\
         /#########################\\
        |###########################|
        |###########################|
         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
    """
    
    CAKE_TODAY = r"""
        🎈          🎈          🎈
           🎊    🎉    🎊
              ★ ☆ ★ ☆ ★
          
            🕯️🕯️🕯️🕯️🕯️🕯️🕯️
          ╔═══════════════════╗
          ║ ✿ ✿ ✿ ✿ ✿ ✿ ✿ ✿ ║
          ╠═══════════════════╣
          ║                   ║
          ║   🎂 HAPPY 🎂    ║
          ║    BIRTHDAY!!     ║
          ║                   ║
          ╠═══════════════════╣
          ║ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ║
          ╚═══════════════════╝
         /█████████████████████\\
        /███████████████████████\\
       /█████████████████████████\\
       
        🎈          🎁          🎈
    """
    
    BALLOONS = r"""
     🎈     🎈     🎈     🎈     🎈
      \\     |     /       \\     /
       \\    |    /         \\   /
        \\   |   /           \\ /
         \\  |  /             V
          \\ | /
           \\|/
    """
    
    GIFT_BOX = r"""
          ★
         /|\\
        /_|_\\
       |     |
       |  🎁 |
       |_____|
    """
    
    PARTY_BANNER = r"""
    ╔══════════════════════════════════════════════════════════╗
    ║  🎉  🎊  🎈  HAPPY BIRTHDAY  🎈  🎊  🎉  ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    COUNTDOWN_FRAME = r"""
    ╭─────────────────────────────────────╮
    │      ⏰ BIRTHDAY COUNTDOWN ⏰       │
    ╰─────────────────────────────────────╯
    """
    
    @classmethod
    def generate_confetti_line(cls, width: int = 70) -> Text:
        """Generate a single line of colorful confetti."""
        text = Text()
        for _ in range(width):
            if random.random() < 0.3:  # 30% chance of confetti
                char = random.choice(CONFETTI_CHARS)
                color = random.choice(CONFETTI_COLORS)
                text.append(char, style=color)
            else:
                text.append(" ")
        return text
    
    @classmethod
    def generate_confetti_block(cls, lines: int = 5, width: int = 70) -> List[Text]:
        """Generate multiple lines of confetti."""
        return [cls.generate_confetti_line(width) for _ in range(lines)]
    
    @classmethod
    def generate_sparkle_border(cls, content: str, width: int = 60) -> str:
        """Wrap content with sparkly border."""
        sparkles = "✨ " * (width // 3)
        border = "═" * width
        
        lines = [
            f"╔{border}╗",
            f"║{sparkles.center(width)}║",
            f"║{content.center(width)}║",
            f"║{sparkles.center(width)}║",
            f"╚{border}╝"
        ]
        return "\n".join(lines)
    
    @classmethod
    def get_birthday_cake(cls, is_today: bool = False) -> str:
        """Get appropriate birthday cake based on status."""
        if is_today:
            return cls.CAKE_TODAY
        return cls.CAKE_LARGE
    
    @classmethod
    def get_celebration_header(cls, name: str, is_today: bool = False) -> Panel:
        """Generate celebration header with name using Rich Panel for proper alignment."""
        if is_today:
            content = Text()
            content.append("🎂 HAPPY BIRTHDAY ", style="bold bright_magenta")
            content.append(name.upper(), style="bold bright_yellow")
            content.append("! 🎂", style="bold bright_magenta")
            
            return Panel(
                Align.center(content),
                border_style="bright_yellow",
                box=rich.box.DOUBLE,
                padding=(0, 2),
            )
        else:
            content = Text()
            content.append("🎈 ", style="bold")
            content.append(name.upper(), style="bold bright_cyan")
            content.append("'s Birthday Countdown 🎈", style="bold bright_cyan")
            
            return Panel(
                Align.center(content),
                border_style="bright_cyan",
                padding=(0, 2),
            )
    
    @classmethod
    def get_countdown_display(
        cls,
        days: int,
        hours: int,
        minutes: int,
        seconds: int,
        is_today: bool = False,
        is_tomorrow: bool = False
    ) -> Panel:
        """Generate beautiful countdown display using Rich Panel for proper alignment."""
        from rich.table import Table
        
        if is_today:
            # Special TODAY display
            content = Text()
            content.append("🎂 TODAY IS THE DAY! 🎂", style="bold bright_magenta")
            return Panel(
                Align.center(content),
                border_style="bright_yellow",
                padding=(1, 4),
            )
        
        # Determine style based on urgency
        if is_tomorrow:
            box_style = "bright_green"
            title = "🎉 BIRTHDAY TOMORROW! 🎉"
        elif days <= 7:
            box_style = "bright_cyan"
            title = "⏰ BIRTHDAY THIS WEEK! ⏰"
        else:
            box_style = "bright_blue"
            title = "⏳ TIME REMAINING ⏳"
        
        # Create countdown table for perfect alignment
        countdown_table = Table.grid(padding=(0, 3))
        countdown_table.add_column(justify="right")
        countdown_table.add_column(justify="left")
        countdown_table.add_column(justify="right")
        countdown_table.add_column(justify="left")
        countdown_table.add_column(justify="right")
        countdown_table.add_column(justify="left")
        countdown_table.add_column(justify="right")
        countdown_table.add_column(justify="left")
        
        countdown_table.add_row(
            Text(f"{days}", style="bold bright_white"),
            Text("DAYS", style="dim"),
            Text(f"{hours}", style="bold bright_white"),
            Text("HRS", style="dim"),
            Text(f"{minutes}", style="bold bright_white"),
            Text("MIN", style="dim"),
            Text(f"{seconds}", style="bold bright_white"),
            Text("SEC", style="dim"),
        )
        
        return Panel(
            Align.center(countdown_table),
            title=f"[bold]{title}[/bold]",
            border_style=box_style,
            padding=(1, 2),
        )
        
        return text
    
    @classmethod
    def get_age_display(cls, current_age: int, turning_age: int, is_today: bool = False) -> Text:
        """Display age information."""
        text = Text()
        
        if is_today:
            text.append(f"\n  🎂 Turning ", style="dim")
            text.append(f"{turning_age}", style="bold bright_magenta")
            text.append(" years old TODAY!\n", style="dim")
        else:
            text.append(f"\n  📅 Currently ", style="dim")
            text.append(f"{current_age}", style="bold bright_cyan")
            text.append(" years old, turning ", style="dim")
            text.append(f"{turning_age}", style="bold bright_green")
            text.append("\n", style="dim")
        
        return text
    
    @classmethod
    def get_zodiac_display(cls, sign: str, emoji: str) -> Text:
        """Display zodiac sign."""
        text = Text()
        text.append(f"  {emoji} Zodiac: ", style="dim")
        text.append(f"{sign}\n", style="bold bright_yellow")
        return text
    
    @classmethod
    def get_confetti_celebration(cls, console: Console, name: str) -> None:
        """Print animated confetti celebration."""
        # Top confetti
        for line in cls.generate_confetti_block(3, 60):
            console.print(Align.center(line))
        
        # Celebration message
        celebration = Text()
        celebration.append("🎊 ", style="bold")
        celebration.append(f"HAPPY BIRTHDAY {name.upper()}!", style="bold bright_magenta")
        celebration.append(" 🎊", style="bold")
        console.print(Align.center(celebration))
        
        # Bottom confetti
        for line in cls.generate_confetti_block(3, 60):
            console.print(Align.center(line))


class BirthdayDisplay:
    """Complete birthday display generator with real animations."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.animations = ASCIIAnimations()
        self.animator = TerminalAnimator(self.console)
    
    def display_birthday_info(
        self,
        name: str,
        birth_date_str: str,
        days: int,
        hours: int,
        minutes: int,
        seconds: int,
        current_age: int,
        turning_age: int,
        zodiac_sign: str,
        zodiac_emoji: str,
        is_today: bool = False,
        is_tomorrow: bool = False,
        branch: str = "",
        registration_no: str = "",
        enrollment_no: str = "",
        animate: bool = True  # Enable/disable animations
    ) -> None:
        """Display complete birthday information with REAL moving animations."""
        
        if animate and is_today:
            # ═══════════════════════════════════════════════════════════
            # BIRTHDAY TODAY - FULL ANIMATED CELEBRATION!
            # ═══════════════════════════════════════════════════════════
            
            # 1. Animated fireworks explosion
            self.animator.animate_fireworks(
                bursts=2, 
                message=f"🎂 HAPPY BIRTHDAY {name.upper()}! 🎂"
            )
            
            # 2. Animated cake with flickering candles
            self.animator.animate_cake_candles(name, duration=2.5)
            
            # 3. Falling confetti animation
            self.animator.animate_falling_confetti(
                duration=2.0, 
                message=f"★ {name.upper()} ★"
            )
            
            # 4. Clear and show final static display
            self.animator.clear_screen()
        
        elif animate and is_tomorrow:
            # ═══════════════════════════════════════════════════════════
            # BIRTHDAY TOMORROW - Countdown animation
            # ═══════════════════════════════════════════════════════════
            
            # Animated countdown flip effect
            self.animator.animate_countdown_flip(days, hours, minutes, seconds, duration=2.0)
            self.animator.clear_screen()
        
        elif animate and days <= 7:
            # ═══════════════════════════════════════════════════════════
            # BIRTHDAY THIS WEEK - Typing effect
            # ═══════════════════════════════════════════════════════════
            self.animator.animate_typing_text(
                f"  🎈 {name}'s Birthday is coming up! 🎈",
                delay=0.02
            )
        
        # ═══════════════════════════════════════════════════════════════
        # STATIC DISPLAY (shown after animations complete)
        # ═══════════════════════════════════════════════════════════════
        
        # Confetti header for special occasions
        if is_today:
            for line in self.animations.generate_confetti_block(4, 70):
                self.console.print(Align.center(line))
        
        # Header
        header = self.animations.get_celebration_header(name, is_today)
        self.console.print(Align.center(header))
        
        # Cake
        cake = self.animations.get_birthday_cake(is_today)
        if is_today:
            self.console.print(Align.center(Text(cake, style="bright_yellow")))
        else:
            self.console.print(Align.center(Text(cake, style="bright_cyan")))
        
        # Countdown
        countdown = self.animations.get_countdown_display(
            days, hours, minutes, seconds, is_today, is_tomorrow
        )
        self.console.print(Align.center(countdown))
        
        # Info Panel
        info_text = Text()
        info_text.append(f"\n  📛 Name: ", style="dim")
        info_text.append(f"{name}\n", style="bold bright_white")
        
        info_text.append(f"  🎂 Birthday: ", style="dim")
        info_text.append(f"{birth_date_str}\n", style="bold bright_cyan")
        
        # Age display
        age_text = self.animations.get_age_display(current_age, turning_age, is_today)
        info_text.append_text(age_text)
        
        # Zodiac
        zodiac_text = self.animations.get_zodiac_display(zodiac_sign, zodiac_emoji)
        info_text.append_text(zodiac_text)
        
        # Branch & Registration (if provided)
        if branch:
            info_text.append(f"  🎓 Branch: ", style="dim")
            info_text.append(f"{branch}\n", style="bold bright_green")
        
        if registration_no:
            info_text.append(f"  🆔 Reg. No: ", style="dim")
            info_text.append(f"{registration_no}\n", style="bright_white")
        
        if enrollment_no:
            info_text.append(f"  📋 Enrollment: ", style="dim")
            info_text.append(f"{enrollment_no}\n", style="bright_white")
        
        panel = Panel(
            info_text,
            title="[bold bright_cyan]Student Profile[/bold bright_cyan]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(Align.center(panel))
        
        # Bottom confetti for birthday
        if is_today:
            for line in self.animations.generate_confetti_block(4, 70):
                self.console.print(Align.center(line))
            
            # Extra celebration
            self.console.print()
            celebration = Text()
            celebration.append("  🎁 ", style="bold")
            celebration.append("Wishing you an amazing birthday filled with joy! ", style="bright_yellow")
            celebration.append("🎁\n", style="bold")
            self.console.print(Align.center(celebration))
        elif is_tomorrow:
            self.console.print()
            tomorrow_msg = Text()
            tomorrow_msg.append("  🎊 ", style="bold")
            tomorrow_msg.append("Get ready! Your special day is TOMORROW! ", style="bright_green")
            tomorrow_msg.append("🎊\n", style="bold")
            self.console.print(Align.center(tomorrow_msg))
