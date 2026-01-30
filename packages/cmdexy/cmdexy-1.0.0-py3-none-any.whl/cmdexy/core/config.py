import os
import json
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".cmdexy"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
        
    def _load_config(self):
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self, key: str, value: str):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        # Restrict permissions to owner only (0600 = rw-------)
        os.chmod(self.config_file, 0o600)

    def get_api_key(self):
        # Priority: Env Var > Config File
        return os.getenv("COHERE_API_KEY") or self.config.get("api_key")

    def get_os_context(self):
        # We compute this live but could cache it
        system = platform.system()
        if system == "Darwin":
            # Return clearer macOS string for AI
            return f"macOS {platform.mac_ver()[0]} ({platform.machine()})"
        return f"{system} {platform.release()} ({platform.machine()})"
