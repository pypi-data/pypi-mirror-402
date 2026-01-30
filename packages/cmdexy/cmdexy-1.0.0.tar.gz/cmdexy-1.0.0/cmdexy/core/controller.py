from rich.console import Console
from cmdexy.core.ai_engine import AIEngine
from cmdexy.core.execution import ExecutionEngine
import platform
import os

console = Console()

class Controller:
    def __init__(self):
        self.ai = AIEngine()
        self.execution = ExecutionEngine()
        self.os_context = f"{platform.system()} {platform.release()} ({platform.machine()})"

    async def process_input(self, user_input: str):
        # 1. Analyze Intent
        with console.status("[bold green]Acting...[/bold green]"):
            intent = await self.ai.analyze_intent(user_input)
        
        console.print(f"Intent detected: [bold cyan]{intent}[/bold cyan]")
        
        if "EXECUTE_CODE" in intent:
            with console.status("[bold green]Generating Code...[/bold green]"):
                code = await self.ai.generate_code(user_input)
            
            console.print("[bold]Generated Code:[/bold]")
            console.print(code, style="italic")
            
            confirm = console.input("[yellow]Execute? (y/n): [/yellow]")
            if confirm.lower() == 'y':
                result = await self.execution.execute_code("python", code)
                console.print("[bold]Result:[/bold]")
                console.print(result)
            else:
                console.print("[red]Aborted.[/red]")

        elif "SYSTEM_COMMAND" in intent:
            with console.status("[bold green]Generating Command...[/bold green]"):
                cmd = await self.ai.generate_shell_command(user_input, self.os_context)
            
            console.print(f"Generated Command: [bold yellow]{cmd}[/bold yellow]")
            
            confirm = console.input("[yellow]Execute on HOST? (y/n): [/yellow]")
            if confirm.lower() == 'y':
                exit_code, stdout, stderr = await self.execution.run_shell_command(cmd)
                
                if exit_code == 0:
                    console.print(stdout)
                else:
                    if stdout: console.print(stdout)
                    console.print(f"[bold red]Command Failed (Exit Code {exit_code})[/bold red]")
                    if stderr: console.print(stderr, style="red")
                    
                    
                    # Interactive Error Recovery
                    await self.trigger_error_recovery(cmd, stdout, stderr)
        
        else:
            # QUESTION
            # CoHere Client is synchronous by default unless AsyncClient is used
            ans = self.ai.client.chat(message=user_input, model='command-r-08-2024')
            console.print(f"[bold]AI Answer:[/bold] {ans.text}")

    async def trigger_error_recovery(self, cmd: str, stdout: str, stderr: str):
        """
        Public method to trigger the AI error analysis and fix loop.
        Useful for direct command execution wrapper.
        """
        analyze = console.input("[yellow]Analyze Error? (y/n): [/yellow]")
        if analyze.lower() == 'y':
            with console.status("[bold yellow]Analyzing Error & Generating Fix...[/bold yellow]"):
                # If the command involved a file, try to read it for context
                # Generalized heuristic: check every word in valid command args
                file_context = ""
                filename = None
                
                # Split command into words and check if they exist as files
                parts = cmd.split()
                for part in parts:
                    # Clean potential quotes or flags
                    candidate = part.strip("'\"")
                    if os.path.isfile(candidate):
                        try:
                            with open(candidate, 'r') as f:
                                # Read content to check encoding and capture context
                                content = f.read()
                                
                            filename = candidate
                            file_context = f"\nFile '{filename}' content:\n{content}"
                            # Found a valid text file, use it as context
                            break
                        except UnicodeDecodeError:
                            # Skip binary files (like executables)
                            continue
                
                fix_suggestion = await self.ai.suggest_fix(cmd, stderr + stdout, file_context, self.os_context)
            
            console.print("[bold]AI Suggestion:[/bold]")
            console.print(fix_suggestion, style="cyan")
            
            # Extract code block via XML tags (robust)
            new_code = None
            if "<FILE_CONTENT>" in fix_suggestion:
                try:
                    new_code = fix_suggestion.split("<FILE_CONTENT>")[1].split("</FILE_CONTENT>")[0].strip()
                    # Strip markdown fences if inside tags
                    if new_code.startswith("```"):
                        new_code = new_code.split("\n", 1)[1]
                    if new_code.endswith("```"):
                        new_code = new_code.rsplit("\n", 1)[0]
                    if new_code.startswith("python"): # simplified
                        new_code = new_code[6:].lstrip()
                except IndexError:
                    pass
            
            if new_code and filename:
                apply_fix = console.input(f"[bold green]Apply fix to {filename} and retry? (y/n): [/bold green]")
                if apply_fix.lower() == 'y':
                    with open(filename, 'w') as f:
                        f.write(new_code)
                    console.print(f"[green]Fixed {filename}. Retrying...[/green]")
                    # Let's just run it once more
                    # Note: For wrapper mode, this retry executes via shell on host
                    exit_code, stdout, stderr = await self.execution.run_shell_command(cmd)
                    if stdout: console.print(stdout)
                    if exit_code != 0:
                         console.print(f"[bold red]Retry Failed (Exit Code {exit_code})[/bold red]")
                         if stderr: console.print(stderr, style="red")
                         await self.trigger_error_recovery(cmd, stdout, stderr)
            else:
                # Check for Command Fix
                fix_cmd = None
                if "<COMMAND_FIX>" in fix_suggestion:
                    try:
                        fix_cmd = fix_suggestion.split("<COMMAND_FIX>")[1].split("</COMMAND_FIX>")[0].strip()
                    except IndexError:
                        pass
                
                if fix_cmd:
                    run_fix = console.input(f"[bold green]Run fix command: '{fix_cmd}'? (y/n): [/bold green]")
                    if run_fix.lower() == 'y':
                        console.print(f"[green]Running fix...[/green]")
                        await self.execution.run_shell_command(fix_cmd)
                        console.print(f"[green]Fix applied. Retrying original command...[/green]")
                        exit_code, stdout, stderr = await self.execution.run_shell_command(cmd)
                        if stdout: console.print(stdout)
                        if exit_code != 0:
                             console.print(f"[bold red]Retry Failed (Exit Code {exit_code})[/bold red]")
                             if stderr: console.print(stderr, style="red")
                             await self.trigger_error_recovery(cmd, stdout, stderr)
        else:
            console.print("[red]Aborted.[/red]")
