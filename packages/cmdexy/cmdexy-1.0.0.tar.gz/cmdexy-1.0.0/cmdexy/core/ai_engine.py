import cohere
import os
from dotenv import load_dotenv

load_dotenv()

from .config import ConfigManager

class AIEngine:
    def __init__(self):
        self.config = ConfigManager()
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError(
                "API Key not found or configured.\n"
                "Please run 'cmdexy config' to set it.\n"
                "Get your key from: https://dashboard.cohere.com/api-keys"
            )
        self.client = cohere.Client(api_key)

    async def analyze_intent(self, user_input: str) -> str:
        """
        Simple intent classification using Cohere Chat.
        """
        prompt = f"""
        Classify the following user input into one of these categories:
        - EXECUTE_CODE: The user wants to write and run code (e.g. "calculate fibonacci", "plot this csv").
        - SYSTEM_COMMAND: The user wants to run a shell command (e.g. "ls -la", "mkdir foo").
        - QUESTION: The user is asking a general question.

        Input: "{user_input}"
        Category:"""
        
        response = self.client.chat(
            model='command-r-08-2024',
            message=prompt,
            temperature=0
        )
        return response.text.strip()

    async def generate_code(self, instruction: str, language: str = "python") -> str:
        """
        Generate a script based on instruction.
        """
        prompt = f"""
        Write a complete, runnable {language} script to: {instruction}.
        Return ONLY the code, no markdown, no explanation.
        If using third-party libraries, assume they are installed or standard.
        """
        response = self.client.chat(
            model='command-r-08-2024',
            message=prompt,
            temperature=0.3
        )
        code = response.text.strip()
        # Strip markdown fences if present
        if code.startswith("```"):
            code = code.split("\n", 1)[1]
        if code.endswith("```"):
            code = code.rsplit("\n", 1)[0]
        # Additional cleanup for fences like ```python
        if code.startswith("python"):
            code = code.split("\n", 1)[1]
        
        return code.strip()

    async def generate_shell_command(self, instruction: str, os_context: str = "Unknown Linux") -> str:
        """
        Generate a shell command based on instruction and OS context.
        """
        prompt = f"""
        You are an expert command line assistant for {os_context}.
        Write a shell command to: {instruction}.
        Return ONLY the command, no code blocks, no explanation.
        Ensure the command is appropriate for the detected OS ({os_context}).
        
        Guidelines:
        - For creating or writing files with multiple lines, USE Heredoc syntax (cat << 'EOF' > filename).
        - Avoid long one-line 'echo' chains for complex content.
        - Ensure the usage of Heredoc is compatible with standard shells (bash/zsh).
        
        Example:
        Input: create hello.py with print hello
        Output: 
        cat << 'EOF' > hello.py
        print("Hello")
        EOF
        """
        response = self.client.chat(
            model='command-r-08-2024',
            message=prompt,
            temperature=0
        )
        return response.text.strip()

    async def suggest_fix(self, command: str, error_log: str, context: str = "", os_context: str = "Unknown OS") -> str:
        """
        Analyze an error and suggest a fix.
        Returns text that describes the fix and provides the corrected code block if applicable.
        """
        prompt = f"""
        You are an expert command line assistant for {os_context}.
        I ran this command: `{command}`
        It failed with this error:
        {error_log}

        {f"Context: {context}" if context else ""}

        Analyze the error.
        If the error is in the code file (e.g. syntax error, name error):
        1. Explain the fix briefly.
        2. Provide the COMPLETELY CORRECTED file content wrapped in <FILE_CONTENT> tags. 
        Example:
        <FILE_CONTENT>
        def foo():
            return 1
        </FILE_CONTENT>
        
        If it's a 'command not found' error or tool missing error, YOU MUST PROVIDE the installation command wrapped in <COMMAND_FIX>.
        Example:
        <COMMAND_FIX>
        brew install cowsay
        </COMMAND_FIX>

        If it's just a wrong flag (e.g. ls -z), provide the corrected command in a standard code block.
        """
        response = self.client.chat(
            model='command-r-08-2024', 
            message=prompt,
            temperature=0
        )
        return response.text.strip()
