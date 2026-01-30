import sys
import typer
import asyncio
from rich.console import Console
from typing import List, Optional
from cmdexy.cli.wrapper import execute_wrapper
from cmdexy.cli.interactive import interactive_session
from cmdexy.cli.run import run_instruction
from cmdexy.core.config import ConfigManager

__version__ = "1.0.0"

def version_callback(value: bool):
    if value:
        print(f"cmdexy version {__version__}")
        raise typer.Exit()

app = typer.Typer(help="cmdexy: AI-powered CLI Assistant", 
                  context_settings={"help_option_names": ["-h", "--help"]})
console = Console()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit")
):
    """
    cmdexy: AI-powered CLI Assistant
    
    Run subcommands: config, int, run, shell
    """
    if ctx.invoked_subcommand is None:
        # Show help if no subcommand
        console.print("[dim]Use --help for more info[/dim]")
        ctx.get_help()

@app.command(name="shell", 
             context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def shell_command(ctx: typer.Context):
    """Run any shell command with AI error recovery. Example: cmdexy shell python3 hello.py"""
    if not ctx.args:
        console.print("[red]Usage: cmdexy shell <command> [args...][/red]")
        raise typer.Exit(1)
    asyncio.run(execute_wrapper(ctx.args))

def interactive():
    """Start the interactive AI session."""
    asyncio.run(interactive_session())

@app.command(name="int", hidden=True)
def interactive_alias():
    """Alias for interactive."""
    asyncio.run(interactive_session())

@app.command()
def run(instruction: str):
    """Execute a single instruction."""
    asyncio.run(run_instruction(instruction))

@app.command()
def config():
    """Configure cmdexy (API Key, etc)."""
    manager = ConfigManager()
    console.print("[bold]Configure cmdexy[/bold]")
    
    # API Key
    current_key = manager.get_api_key()
    if current_key:
        console.print(f"Current API Key: [green]{current_key[:4]}...{current_key[-4:]}[/green]")
    
    api_key = console.input("Enter Cohere API Key (leave blank to keep current): ", password=True)
    if api_key.strip():
        new_key = api_key.strip()
        console.print("[yellow]Validating API Key...[/yellow]")
        try:
            # Validate by making a lightweight call
            import cohere
            client = cohere.Client(new_key)
            # Use Chat API as Generate is deprecated
            client.chat(message="hi", model="command-r-08-2024")
            
            manager.save_config("api_key", new_key)
            console.print("[green]API Key valid and saved successfully![/green]")
        except Exception as e:
            console.print(f"[bold red]Invalid API Key:[/bold red] {e}")
            console.print("[red]Key NOT saved.[/red]")
    else:
        console.print("[yellow]API Key unchanged.[/yellow]")

def entry_point():
    """Main entry point."""
    app()

if __name__ == "__main__":
    entry_point()
