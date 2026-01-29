import json
import os
from typing import Optional, Dict

CONFIG_FILE = os.path.expanduser("~/.checkpaste.json")

def load_config() -> Dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_config(config: Dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_server_info() -> Optional[Dict]:
    config = load_config()
    return config.get("server")

def save_server_info(host: str, port: int, password: Optional[str] = None):
    config = load_config()
    config["server"] = {
        "host": host,
        "port": port,
        "password": password
    }
    save_config(config)

def clear_server_info():
    config = load_config()
    if "server" in config:
        del config["server"]
        save_config(config)
