import sys
from rich.console import Console
from cmdexy.core.controller import Controller
from cmdexy.core.execution import ExecutionEngine
import asyncio

console = Console()

async def execute_wrapper(command_parts: list[str]):
    """
    Directly execute a command and monitor for failure.
    If it fails, trigger AI error recovery.
    """
    controller = Controller()
    
    # Reconstruct command
    cmd = " ".join(command_parts)
    
    # console.print(f"[dim]Executing: {cmd}[/dim]")
    
    # Execute directly
    exit_code, stdout, stderr = await controller.execution.run_shell_command(cmd)
    
    # Identify if output should be printed based on successful execution or not?
    # Actually run_shell_command buffers output. For a wrapper we ideally want streaming.
    # But for MVP we just print result.
    
    if exit_code == 0:
        if stdout: print(stdout)
        if stderr: print(stderr, file=sys.stderr)
    else:
        # Failure case
        if stdout: print(stdout)
        if stderr: print(stderr, file=sys.stderr)
        
        console.print(f"\n[bold red]Command Failed (Exit Code {exit_code})[/bold red]")
        
        # Trigger Recovery
        try:
            await controller.trigger_error_recovery(cmd, stdout, stderr)
        except Exception as e:
            console.print(f"[red]Error during recovery:[/red] {e}")
