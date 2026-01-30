"""
AI Assistant CLI Command

Interactive AI assistant using local NLP for intent detection
and entity extraction.
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from mbm.core.config import get_config
from mbm.core.constants import COLORS
from mbm.ai import AIAssistant, Intent


console = Console()


# AI Assistant Banner
AI_BANNER = r"""
    _    ___      _            _     _              _   
   / \  |_ _|    / \   ___ ___(_)___| |_ __ _ _ __ | |_ 
  / _ \  | |    / _ \ / __/ __| / __| __/ _` | '_ \| __|
 / ___ \ | |   / ___ \\__ \__ \ \__ \ || (_| | | | | |_ 
/_/   \_\___|_/_/   \_\___/___/_|___/\__\__,_|_| |_|\__|
"""


def print_ai_banner() -> None:
    """Display the AI assistant banner."""
    console.print(f"[{COLORS['info']}]{AI_BANNER}[/{COLORS['info']}]")
    console.print(
        f"[{COLORS['muted']}]Local NLP-powered assistant - No cloud, no tracking[/{COLORS['muted']}]",
        justify="center",
    )
    console.print()


def print_ai_help() -> None:
    """Display AI assistant help."""
    help_text = """
**Available Commands:**
- `help` - Show this help
- `exit` / `quit` - Exit the assistant
- `clear` - Clear the screen

**Example Queries:**
- "What is MBM University?"
- "Show image of Jodhpur"
- "Tell me about Python programming"

**Capabilities:**
- 🔍 Information lookup (Wikipedia)
- 🖼️ Image search (Wikimedia Commons)
- 🧠 Intent detection (local NLP)

**Privacy:**
- No data is sent to cloud services
- Uses local spaCy models only
- Images from legal sources only
"""
    console.print(Markdown(help_text))


@click.command(name='ai')
@click.option('--no-nlp', is_flag=True, help='Disable NLP processing (use keyword matching).')
@click.pass_context
def ai_command(ctx: click.Context, no_nlp: bool) -> None:
    """
    Start the MBM AI Assistant.
    
    An interactive assistant that can answer questions and show images
    using local NLP (no cloud services).
    
    Type 'help' for available commands, 'exit' to quit.
    """
    print_ai_banner()
    
    config = get_config()
    use_nlp = config.nlp_enabled and not no_nlp
    
    if use_nlp:
        console.print(f"[{COLORS['success']}]✓ NLP enabled (using spaCy)[/{COLORS['success']}]")
    else:
        console.print(f"[{COLORS['warning']}]⚠ NLP disabled (using keyword matching)[/{COLORS['warning']}]")
    
    console.print(f"[{COLORS['info']}]Type 'help' for commands, 'exit' to quit[/{COLORS['info']}]")
    console.print()
    
    # Initialize AI assistant
    assistant = AIAssistant(use_nlp=use_nlp)
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = console.input(f"[{COLORS['primary']}]mbm>[/{COLORS['primary']}] ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            lower_input = user_input.lower()
            
            if lower_input in ('exit', 'quit', 'q'):
                console.print(f"[{COLORS['muted']}]Goodbye![/{COLORS['muted']}]")
                break
            
            if lower_input == 'help':
                print_ai_help()
                continue
            
            if lower_input == 'clear':
                console.clear()
                print_ai_banner()
                continue
            
            # Process query
            console.print(f"[{COLORS['muted']}]Processing...[/{COLORS['muted']}]")
            
            try:
                response = assistant.process_query(user_input)
                
                if response.success:
                    # Display response based on intent
                    if response.intent == Intent.IMAGE:
                        console.print(f"\n[{COLORS['success']}]🖼️  Opening image...[/{COLORS['success']}]")
                        if response.message:
                            console.print(f"[{COLORS['muted']}]{response.message}[/{COLORS['muted']}]")
                    else:
                        console.print()
                        # Display as markdown panel
                        panel = Panel(
                            Markdown(response.text or "No information found."),
                            title=f"[{COLORS['info']}]{response.title or 'Result'}[/{COLORS['info']}]",
                            border_style=COLORS['info'],
                            padding=(1, 2),
                        )
                        console.print(panel)
                else:
                    console.print(f"\n[{COLORS['warning']}]⚠ {response.message}[/{COLORS['warning']}]")
                
            except Exception as e:
                console.print(f"\n[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
                if config.debug:
                    console.print_exception()
            
            console.print()
            
        except KeyboardInterrupt:
            console.print(f"\n[{COLORS['muted']}]Use 'exit' to quit[/{COLORS['muted']}]")
            continue
        except EOFError:
            console.print(f"\n[{COLORS['muted']}]Goodbye![/{COLORS['muted']}]")
            break
