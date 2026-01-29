import json
from pathlib import Path
from platformdirs import user_config_dir

# Import defaults
from .data.roasts import ROASTS as DEFAULT_ROASTS
from .data.praises import PRAISES as DEFAULT_PRAISES
from .data.forbidden import FORBIDDEN as DEFAULT_FORBIDDEN
from .data.nagging import NAG_MESSAGES as DEFAULT_NAG_MESSAGES
from .data.browsers import BROWSER_PROCESS_NAMES as DEFAULT_BROWSERS

APP_NAME = "guilt-3p"

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(user_config_dir(APP_NAME))
        self.config_path = self.config_dir / "config.json"
        self._ensure_config()
        self.config = self._load_config()

    def _ensure_config(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # We don't force create the file if it doesn't exist, 
        # but we can if we want the user to see it. 
        # For now, let's create it if it's missing to help the user.
        if not self.config_path.exists():
            self.create_default_config()

    def create_default_config(self):
        default_config = {
            "general": {
                "extend_defaults": True
            },
            "custom_roasts": DEFAULT_ROASTS,
            "custom_praises": DEFAULT_PRAISES,
            "custom_forbidden": DEFAULT_FORBIDDEN,
            "custom_nag_messages": DEFAULT_NAG_MESSAGES,
            "custom_browsers": DEFAULT_BROWSERS
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {self.config_path}")
        except Exception as e:
            print(f"Failed to create default config: {e}")

    def _load_config(self):
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return {}

    def get_list(self, key, default_list):
        custom = self.config.get(f"custom_{key}", [])
        extend = self.config.get("general", {}).get("extend_defaults", True)
        
        # Ensure custom is a list
        if not isinstance(custom, list):
            custom = []

        if extend:
            return default_list + custom
        return custom if custom else default_list

    @property
    def roasts(self):
        return self.get_list("roasts", DEFAULT_ROASTS)

    @property
    def praises(self):
        return self.get_list("praises", DEFAULT_PRAISES)

    @property
    def forbidden(self):
        return self.get_list("forbidden", DEFAULT_FORBIDDEN)
    
    @property
    def nag_messages(self):
        return self.get_list("nag_messages", DEFAULT_NAG_MESSAGES)

    @property
    def browsers(self):
        return self.get_list("browsers", DEFAULT_BROWSERS)

config = ConfigManager()
