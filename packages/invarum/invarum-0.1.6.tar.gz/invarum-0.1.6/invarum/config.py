# invarum-cli/invarum/config.py
import os
import json
from pathlib import Path
from typing import Optional

# Standard location: ~/.invarum/config.json
APP_DIR = Path.home() / ".invarum"
CONFIG_FILE = APP_DIR / "config.json"

def get_api_key() -> Optional[str]:
    """
    Priority:
    1. INVARUM_API_KEY environment variable (CI/CD)
    2. Local config file (Human)
    """
    # 1. Check Env
    env_key = os.getenv("INVARUM_API_KEY")
    if env_key:
        return env_key

    # 2. Check File
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return data.get("api_key")
        except:
            return None
    
    return None

def save_api_key(key: str):
    """
    Saves the API key to ~/.invarum/config.json
    """
    APP_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
        except:
            pass
    
    data["api_key"] = key
    CONFIG_FILE.write_text(json.dumps(data, indent=2))