from cmdexy.core.controller import Controller
import asyncio

async def run_instruction(instruction: str):
    """Execute a single instruction."""
    try:
        controller = Controller()
        await controller.process_input(instruction)
    except Exception as e:
        print(f"Error: {e}")
