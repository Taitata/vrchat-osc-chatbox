
from dataclasses import dataclass
import os

def _getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

@dataclass
class Settings:
    vrchat_ip: str = os.getenv("VRCHAT_IP", "127.0.0.1")
    osc_in_port: int = _getenv_int("OSC_IN_PORT", 9000)
    chatbox_max_len: int = _getenv_int("CHATBOX_MAX_LEN", 140)
    debug: bool = os.getenv("DEBUG", "0") == "1"

SETTINGS = Settings()
