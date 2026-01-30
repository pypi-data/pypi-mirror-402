"""
Aaryan Language CLI Commands

Commands for interacting with the Aaryan programming language module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from mbm.core.config import get_config
from mbm.core.constants import AARYAN_FILE_EXTENSION, COLORS, EXIT_SUCCESS
from mbm.aaryan import AaryanInterpreter, AaryanREPL


console = Console()


# Aaryan ASCII Banner
AARYAN_BANNER = r"""
                                                                    
                                                                    
   ,---,                                                            
  '  .' \                                                           
 /  ;    '.                 __  ,-.                          ,---,  
:  :       \              ,' ,'/ /|                      ,-+-. /  | 
:  |   /\   \    ,--.--.  '  | |' |   .--,   ,--.--.    ,--.'|'   | 
|  :  ' ;.   :  /       \ |  |   ,' /_ ./|  /       \  |   |  ,"' | 
|  |  ;/  \   \.--.  .-. |'  :  /, ' , ' : .--.  .-. | |   | /  | | 
'  :  | \  \ ,' \__\/: . .|  | '/___/ \: |  \__\/: . . |   | |  | | 
|  |  '  '--'   ," .--.; |;  : | .  \  ' |  ," .--.; | |   | |  |/  
|  :  :        /  /  ,.  ||  , ;  \  ;   : /  /  ,.  | |   | |--'   
|  | ,'       ;  :   .'   \---'    \  \  ;;  :   .'   \|   |/       
`--''         |  ,     .-./         :  \  \  ,     .-./'---'        
               `--`---'              \  ' ;`--`---'          
                                                                                  
                             .-+#@@@%#*+=-:.:::..:+****#%%@@@#=:.                             
                        ..:#@@@#=...:..:.:-+#**%-*==-+=+*#**#=+#@@*:.                         
                      .*%@@+:.=.--+=+**#*#%%##%%#%%%%%#*++=+-*=++++@@%+.                      
                  ..=@@%=....+=#%%%*#%%%%@@@%#%%#%@@%%@@%%##+-++++-:.=%@%=.                   
                 :%@@=.  .:+#%%%%%%#@@@%@@@@@@@@%@@@@@@%%%@##%##%%#*=:..+@@#.                 
              .-%@#:.   .-#*#%%%%@%@@@@@@@@@@@@@@@@@@@@@@@%%#***####+:... :%@%:               
            .-%@*.     .-*+##@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#***-:==:..  :#@%:             
           .%@#.       .===%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%#*=-:-::..   .#@#.           
         .+@%:         ..*+%@@@@@@@@@@@@@@@@@@@@@%%@@@@@@@@@@@@@%#+==*+=-==.    -@@=.         
        .%@+.            .+%%@@@@@%%###*********++***#%%%%%@%@@@%%%#**==-:=:     .#@#.        
       -@@-          ..*#%%@@@%%#**++=====------::-:---=+**%%%@@%%%#%*=+-+#*.      -@%:       
     .=@%.         .:-:-*%@@@%#*+==----------:::::::::::-==+*#%%@@%@%%%#*+**.       :@@-      
     =@#.           :..-%@@@%*===----------:::::::...........:=#%@@@%@%%+-#%+.       :%@-     
    =@#.            . .@%@@%*=--------------:::::.............::=#@@@%%*+**#.         .@@:    
   -@%.              .-@@%%#=-----------:::::::::..............::-#@@%%%##*.           :%@:   
  .%@:                -@%%%*--------::::::::::::...............:::+@@@@@%%*.            =@#.  
  *@=                 +%%%#------------:::::.....................:=%@@@@@%-.            .*@=  
 -@#.                 *%%@=-=*##%@@%%##+==-::::::::..............:+%@@@@#..              .%@. 
.#@=                  +#+@%#******+**###*++==------==---:........:*%@@@%.                 +@+.
:@@.                  :%+*======+++*****+##*+++++++++#%#%%#=:....:+%@@@=.                 :@%.
=@*                   .%==:=+****#######**+#%%%##%###***++**+=-:..-@@%=.                  .%@:
*@:                .=-=+:=-*##%##%%@%#%#**=*#=+#%*###****++++*==*:.%@*.                    +@=
%@.                .+-*-:=:-=++****#####++**...-@*#####%%#***++=::##=-                     -@*
@%                 .=-+::----==+++**+==-=++:....=#*##*#%%%####*+:-*++.                     .@#
@%                 .-+-:-::+::----------*-:......*-+*#***++==+#+--#*.                       @%
@%                 .+*:::::--=++++++*+*=:........=-.::-=+*+-:....:=.                       .@%
%@.                .=*::-----=====+++=:::.........::............-.===-.                    :@#
*@:                .-=-----===++++++=::::::::......::.:--:....:...=++.                     =@+
=@*                .:=--====++**#*+++-=++-======-...++=----:......=-:                      #@-
:@@.                .=====++*#%#*+===+*##****#%%*+=-##*+===--:....*..                     :@%:
.#@=                 .:==++*%%**+++++**##########*++**#*+++=--:::::..                     =@*.
 -@#.                .:=+++*%###**++++++****####*=+**##%#***++=-:-.                       %@: 
  #@-                 .-=++*%%%%%%%******++++++=:-=####%%%##***=-..                      +@+  
  .%@:                 -=++**##*+*##:.:.:--:=*###%####%@@@####*+:.                      -@#.  
  .-@#.                .-=++**++=-==+#*=--..::--*#@@%#%%%*###*=-.                      .%@-   
    +@*.                .===+++==---====+==-....:=****##**###+=.                      .%@-    
     +@#.                .==++++=----==+++**+++---+++***##**#:                       .#@=     
     .+@#.                .++++===--==++++++++----=++**#####:.                      .%@=      
       -@@:                :#+++======+++++++=----=+*###%%:                        :@@-       
        :@@=               .+##+===-======---::---=+#%%%+.                       .+@%.        
         .*@#.           .::=*%#*+===++==-::::::--=*%@%=...                     :%@+.         
           .@@*.       .=@@-==+@#*+**#**++=-----=+#@@#-...=:.                 .#@%.           
            .=@@+...+#%%@@*-===+#%%###%###*++++*%%%#*=:....#+++-.           .*@%-.            
              .+%%%%@@%@@#---===++##%%%%%%%%%%%%%##*=::....+**#%**=:.     .*@@=.              
                .-%%@%@@#-=-=====++**##%%%%%%####*+=-:.....###%@+*+*+=..-@@@:.                
                  .:*@@@#-=-======++**#########**+=--::...=*#%%%#%*=:-#@@+:.                  
                      :##*=--=====++*****###*****+=--::..:###%%##-=%@@*.                      
                        ..=%%*===+++************++=-::.:-##*--*@@@%-..                        
                            .:=*%@%####********++=----=+*%@@@%*-.                             
                                   .-*%@@@@@@@@@@@@@@@@#+-.                                          
                                      `--`                          

"""


def print_aaryan_banner() -> None:
    """Display the Aaryan language banner."""
    console.print(f"[{COLORS['secondary']}]{AARYAN_BANNER}[/{COLORS['secondary']}]")
    console.print(
        f"[{COLORS['muted']}]The Aaryan Programming Language [/{COLORS['muted']}]",
        justify="center",
    )
    console.print()


def print_aaryan_help() -> None:
    """Display Aaryan language help."""
    help_content = Text()
    
    help_content.append("AARYAN LANGUAGE\n", style="bold bright_white")
    help_content.append("A simple, educational programming language.\n\n", style="dim")
    
    help_content.append("USAGE\n", style="bold bright_white")
    help_content.append("  mbm aaryan                 ", style="bright_cyan")
    help_content.append("Show this help\n", style="dim")
    help_content.append("  mbm aaryan run <file>      ", style="bright_cyan")
    help_content.append("Run an Aaryan program\n", style="dim")
    help_content.append("  mbm aaryan repl            ", style="bright_cyan")
    help_content.append("Start interactive REPL\n", style="dim")
    help_content.append("  mbm aaryan check <file>    ", style="bright_cyan")
    help_content.append("Check syntax without running\n\n", style="dim")
    
    help_content.append("FILE EXTENSION\n", style="bold bright_white")
    help_content.append(f"  {AARYAN_FILE_EXTENSION}\n\n", style="bright_green")
    
    help_content.append("EXAMPLES\n", style="bold bright_white")
    help_content.append("  mbm aaryan run hello.ar\n", style="bright_green")
    help_content.append("  mbm aaryan repl\n", style="bright_green")
    
    panel = Panel(
        help_content,
        title=f"[bold {COLORS['secondary']}]Aaryan Language[/bold {COLORS['secondary']}]",
        border_style=COLORS['secondary'],
        padding=(1, 2),
    )
    console.print(panel)


@click.group(invoke_without_command=True)
@click.pass_context
def aaryan_group(ctx: click.Context) -> None:
    """
    Aaryan programming language module.
    
    A simple, educational programming language embedded in MBM.
    Use 'mbm aaryan --help' for more information.
    """
    if ctx.invoked_subcommand is None:
        print_aaryan_banner()
        print_aaryan_help()


@aaryan_group.command(name='run')
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output.')
@click.option('--trace', is_flag=True, help='Enable execution tracing.')
@click.pass_context
def run_command(ctx: click.Context, filepath: str, verbose: bool, trace: bool) -> None:
    """
    Run an Aaryan program file.
    
    FILEPATH: Path to the .ar file to execute.
    """
    path = Path(filepath)
    
    # Validate file extension
    if path.suffix != AARYAN_FILE_EXTENSION:
        console.print(
            f"[{COLORS['warning']}]Warning: File does not have {AARYAN_FILE_EXTENSION} extension[/{COLORS['warning']}]"
        )
    
    # Read and execute
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        if verbose:
            console.print(f"[{COLORS['info']}]Running: {path}[/{COLORS['info']}]")
            console.print()
        
        interpreter = AaryanInterpreter(trace=trace)
        result = interpreter.execute(source_code)
        
        if result is not None and verbose:
            console.print(f"\n[{COLORS['success']}]Program completed with result: {result}[/{COLORS['success']}]")
            
    except FileNotFoundError:
        console.print(f"[{COLORS['error']}]Error: File not found: {filepath}[/{COLORS['error']}]")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
        config = get_config()
        if config.debug:
            console.print_exception()
        ctx.exit(1)


@aaryan_group.command(name='repl')
@click.pass_context
def repl_command(ctx: click.Context) -> None:
    """
    Start the Aaryan interactive REPL.
    
    An interactive environment for experimenting with Aaryan code.
    Type 'exit' or 'quit' to leave, 'help' for commands.
    """
    print_aaryan_banner()
    console.print(f"[{COLORS['info']}]Interactive Mode - Type 'help' for commands, 'exit' to quit[/{COLORS['info']}]")
    console.print()
    
    repl = AaryanREPL()
    repl.run()


@aaryan_group.command(name='check')
@click.argument('filepath', type=click.Path(exists=True))
@click.pass_context
def check_command(ctx: click.Context, filepath: str) -> None:
    """
    Check an Aaryan program for syntax errors without running it.
    
    FILEPATH: Path to the .ar file to check.
    """
    path = Path(filepath)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        interpreter = AaryanInterpreter()
        errors = interpreter.check_syntax(source_code)
        
        if errors:
            console.print(f"[{COLORS['error']}]Found {len(errors)} error(s):[/{COLORS['error']}]")
            for error in errors:
                console.print(f"  • {error}")
            ctx.exit(1)
        else:
            console.print(f"[{COLORS['success']}]✓ No syntax errors found in {path.name}[/{COLORS['success']}]")
            
    except FileNotFoundError:
        console.print(f"[{COLORS['error']}]Error: File not found: {filepath}[/{COLORS['error']}]")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
        ctx.exit(1)


@aaryan_group.command(name='example')
@click.pass_context
def example_command(ctx: click.Context) -> None:
    """
    Show example Aaryan code.
    """
    example_code = '''# Hello World in Aaryan
print "Hello, World!"

# Variables
let name = "MBM"
let year = 2026

# Print with variables
print "Welcome to " + name
print "Year: " + year

# Simple function
fn greet(person) {
    print "Hello, " + person + "!"
}

# Call function
greet("Aaryan")
'''
    
    console.print(f"\n[{COLORS['info']}]Example Aaryan Program:[/{COLORS['info']}]\n")
    syntax = Syntax(example_code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="hello.ar", border_style=COLORS['secondary']))
    console.print(f"\n[{COLORS['muted']}]Save this as 'hello.ar' and run with: mbm aaryan run hello.ar[/{COLORS['muted']}]")
