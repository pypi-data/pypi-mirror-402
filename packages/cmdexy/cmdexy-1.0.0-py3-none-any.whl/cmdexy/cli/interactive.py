from rich.console import Console
from cmdexy.core.controller import Controller
import asyncio

console = Console()

async def interactive_session():
    """Start the interactive AI session."""
    try:
        controller = Controller()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return

    console.print("[bold green]Welcome to cmdexy![/bold green] Type 'exit' to quit.")
    
    while True:
        try:
            user_input = console.input("[bold blue]cmdexy >[/bold blue] ")
            if user_input.lower() in ("exit", "quit"):
                break
            
            await controller.process_input(user_input)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
