import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _default_config_dir() -> Path:
    # Windows: %APPDATA%\k8s-agent ; Others: ~/.config/k8s-agent
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "k8s-agent"
    return Path.home() / ".config" / "k8s-agent"


def _config_path() -> Path:
    return _default_config_dir() / "config.json"


@dataclass
class AgentConfig:
    api_url: str = ""
    access_token: str = ""
    refresh_token: str = ""

    @staticmethod
    def load() -> "AgentConfig":
        p = _config_path()
        if not p.exists():
            return AgentConfig()
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
        return AgentConfig(
            api_url=str(data.get("api_url", "")),
            access_token=str(data.get("access_token", "")),
            refresh_token=str(data.get("refresh_token", "")),
        )

    def save(self) -> None:
        p = _config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {
                    "api_url": self.api_url,
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_logged_in(self) -> bool:
        return bool(self.api_url and self.access_token)

    def clear_tokens(self) -> None:
        self.access_token = ""
        self.refresh_token = ""


