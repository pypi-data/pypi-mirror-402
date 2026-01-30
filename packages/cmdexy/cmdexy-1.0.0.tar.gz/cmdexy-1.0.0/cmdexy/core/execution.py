import docker
import os
import asyncio
from typing import Tuple

class ExecutionEngine:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except:
            print("Warning: Docker not available. Sandboxed execution will be limited.")
            self.client = None

    async def execute_code(self, language: str, code: str) -> str:
        """
        Execute code in a sandbox (Docker).
        Handles interactive scripts by running in foreground if input() detected.
        """
        if not self.client:
            return "Error: Docker not running."

        # Support mainly Python for MVP
        image = "python:3.10-slim" 
        
        # Interactive Mode Check
        if "input(" in code:
            # We must run this attached to the user's terminal
            # Write code to a temp file on host first
            temp_file = "temp_script.py"
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Use subprocess to run docker run -it ...
            # Mounting current dir to /app so script is accessible
            cmd = ["docker", "run", "-it", "--rm", "-v", f"{os.getcwd()}:/app", "-w", "/app", image, "python", temp_file]
            
            # Using asyncio.create_subprocess_exec doesn't handle stdin/tty well for interactive
            # So we rely on standard subprocess for interactive session
            import subprocess
            try:
                subprocess.run(cmd)
                return "Interactive session ended."
            except Exception as e:
                return f"Interactive Execution Failed: {e}"
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        # Standard Detached Execution
        try:
            container = self.client.containers.run(
                image,
                command=f"python -c '{code}'",
                remove=True,
                detach=False, # Wait for output
                working_dir="/app",
                stderr=True
            )
            return container.decode("utf-8")
        except Exception as e:
            return f"Execution Failed: {e}"

    async def run_shell_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a shell command on the HOST system.
        Returns (exit_code, stdout, stderr).
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode().strip(), stderr.decode().strip()
