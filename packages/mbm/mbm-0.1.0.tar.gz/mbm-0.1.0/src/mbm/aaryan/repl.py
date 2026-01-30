"""
Aaryan Language REPL

Interactive Read-Eval-Print Loop for experimenting with Aaryan code.
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.syntax import Syntax

from mbm.aaryan.interpreter import AaryanInterpreter
from mbm.core.constants import COLORS


class AaryanREPL:
    """
    Interactive REPL for the Aaryan language.
    
    Provides an interactive environment for experimenting with
    Aaryan code with helpful features like history and syntax
    highlighting.
    """
    
    HELP_TEXT = """
╭─────────────────────────────────────────────────────────────╮
│                   Aaryan REPL Commands                      │
├─────────────────────────────────────────────────────────────┤
│  help          Show this help message                       │
│  exit / quit   Exit the REPL                                │
│  clear         Clear all variables                          │
│  vars          Show all defined variables                   │
│  history       Show command history                         │
│  example       Show example code                            │
╰─────────────────────────────────────────────────────────────╯
"""
    
    def __init__(self):
        """Initialize REPL."""
        self.console = Console()
        self.interpreter = AaryanInterpreter()
        self.history: list[str] = []
        self.running = False
    
    def run(self) -> None:
        """Start the REPL loop."""
        self.running = True
        
        while self.running:
            try:
                # Get input
                line = self._read_input()
                
                if line is None:
                    continue
                
                # Handle commands
                if self._handle_command(line):
                    continue
                
                # Execute code
                self._execute(line)
                
            except KeyboardInterrupt:
                self.console.print(f"\n[{COLORS['muted']}]Use 'exit' to quit[/{COLORS['muted']}]")
            except EOFError:
                self.console.print(f"\n[{COLORS['muted']}]Goodbye![/{COLORS['muted']}]")
                break
    
    def _read_input(self) -> Optional[str]:
        """Read user input, handling multiline input."""
        try:
            line = self.console.input(f"[{COLORS['secondary']}]aaryan>[/{COLORS['secondary']}] ").strip()
            
            if not line:
                return None
            
            # Handle multiline input (opening braces)
            open_braces = line.count('{') - line.count('}')
            
            while open_braces > 0:
                continuation = self.console.input(f"[{COLORS['muted']}]......>[/{COLORS['muted']}] ")
                line += '\n' + continuation
                open_braces += continuation.count('{') - continuation.count('}')
            
            # Add to history
            if line and (not self.history or self.history[-1] != line):
                self.history.append(line)
            
            return line
            
        except Exception:
            return None
    
    def _handle_command(self, line: str) -> bool:
        """
        Handle REPL commands.
        
        Returns:
            True if a command was handled, False otherwise
        """
        lower = line.lower().strip()
        
        if lower in ('exit', 'quit', 'q'):
            self.running = False
            self.console.print(f"[{COLORS['muted']}]Goodbye![/{COLORS['muted']}]")
            return True
        
        if lower == 'help':
            self.console.print(self.HELP_TEXT)
            return True
        
        if lower == 'clear':
            self.interpreter = AaryanInterpreter()
            self.console.print(f"[{COLORS['success']}]Environment cleared[/{COLORS['success']}]")
            return True
        
        if lower == 'vars':
            self._show_variables()
            return True
        
        if lower == 'history':
            self._show_history()
            return True
        
        if lower == 'example':
            self._show_example()
            return True
        
        return False
    
    def _execute(self, code: str) -> None:
        """Execute Aaryan code and display result."""
        try:
            result = self.interpreter.execute(code)
            
            if result is not None:
                # Display result with nice formatting
                output = self.interpreter._stringify(result)
                self.console.print(f"[{COLORS['success']}]=> {output}[/{COLORS['success']}]")
                
        except Exception as e:
            self.console.print(f"[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
    
    def _show_variables(self) -> None:
        """Show all defined variables."""
        env = self.interpreter.environment
        
        if not env.variables:
            self.console.print(f"[{COLORS['muted']}]No variables defined[/{COLORS['muted']}]")
            return
        
        self.console.print(f"\n[{COLORS['info']}]Defined Variables:[/{COLORS['info']}]")
        
        for name, value in env.variables.items():
            # Skip built-in functions
            if callable(value) and not hasattr(value, 'declaration'):
                continue
            
            type_name = self.interpreter._builtin_type([value])
            str_value = self.interpreter._stringify(value)
            
            if len(str_value) > 50:
                str_value = str_value[:47] + "..."
            
            const_marker = " (const)" if name in env.constants else ""
            self.console.print(f"  {name}: {type_name} = {str_value}{const_marker}")
        
        self.console.print()
    
    def _show_history(self) -> None:
        """Show command history."""
        if not self.history:
            self.console.print(f"[{COLORS['muted']}]No history yet[/{COLORS['muted']}]")
            return
        
        self.console.print(f"\n[{COLORS['info']}]Command History:[/{COLORS['info']}]")
        
        for i, cmd in enumerate(self.history[-20:], 1):
            # Truncate long commands
            display = cmd.replace('\n', ' ')
            if len(display) > 60:
                display = display[:57] + "..."
            self.console.print(f"  {i:3}. {display}")
        
        self.console.print()
    
    def _show_example(self) -> None:
        """Show example Aaryan code."""
        example = '''# Variables
let name = "Aaryan"
let age = 21

# Print
print "Hello, " + name + "!"

# Function
fn greet(person) {
    print "Welcome, " + person
}

greet("MBM")

# Array
let numbers = [1, 2, 3, 4, 5]
print "Length: " + len(numbers)

# Loop
let i = 0
while i < 3 {
    print i
    i = i + 1
}

# Conditionals
if age >= 18 {
    print "Adult"
} else {
    print "Minor"
}'''
        
        self.console.print(f"\n[{COLORS['info']}]Example Aaryan Code:[/{COLORS['info']}]\n")
        syntax = Syntax(example, "python", theme="monokai", line_numbers=True)
        self.console.print(syntax)
        self.console.print()
