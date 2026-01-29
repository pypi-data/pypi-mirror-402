
import json
import os
from pathlib import Path
from typing import Any, Dict

from viperx.constants import USER_CONFIG_DIR

SETTINGS_FILE = USER_CONFIG_DIR / "settings.json"

class Settings:
    """Persistent user settings manager."""
    
    def __init__(self):
        self._ensure_dir()
        self.data = self._load()

    def _ensure_dir(self):
        """Ensure local configuration directory exists."""
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        """Load settings from JSON."""
        if not SETTINGS_FILE.exists():
            return {"explain_mode": True}
        
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except json.JSONDecodeError:
            return {"explain_mode": True}

    def save(self):
        """Save settings to JSON."""
        SETTINGS_FILE.write_text(json.dumps(self.data, indent=2))

    @property
    def explain_mode(self) -> bool:
        return self.data.get("explain_mode", False)

    @explain_mode.setter
    def explain_mode(self, value: bool):
        self.data["explain_mode"] = value
        self.save()

# Global settings instance
settings = Settings()
