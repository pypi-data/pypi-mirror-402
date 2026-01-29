import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToothFairyConfig:
    """Configuration for ToothFairy CLI."""

    base_url: str
    ai_url: str
    ai_stream_url: str
    api_key: str
    workspace_id: str

    @classmethod
    def from_env(cls) -> "ToothFairyConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("TF_BASE_URL", "https://api.toothfairyai.com"),
            ai_url=os.getenv("TF_AI_URL", "https://ai.toothfairyai.com"),
            ai_stream_url=os.getenv("TF_AI_STREAM_URL", "https://ais.toothfairyai.com"),
            api_key=os.getenv("TF_API_KEY", ""),
            workspace_id=os.getenv("TF_WORKSPACE_ID", ""),
        )

    @classmethod
    def from_file(cls, config_path: str) -> "ToothFairyConfig":
        """Load configuration from a file (JSON or YAML)."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            if path.suffix in [".yml", ".yaml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        return cls(
            base_url=data.get("base_url", "https://api.toothfairyai.com"),
            ai_url=data.get("ai_url", "https://ai.toothfairyai.com"),
            ai_stream_url=data.get("ai_stream_url", "https://ais.toothfairyai.com"),
            api_key=data.get("api_key", ""),
            workspace_id=data.get("workspace_id", ""),
        )

    def validate(self) -> bool:
        """Validate that all required fields are present."""
        return all([self.api_key, self.workspace_id])

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "base_url": self.base_url,
            "ai_url": self.ai_url,
            "ai_stream_url": self.ai_stream_url,
            "api_key": self.api_key,
            "workspace_id": self.workspace_id,
        }


def get_config_path() -> Path:
    """Get the default config file path."""
    return Path.home() / ".toothfairy" / "config.yml"


def load_config(config_path: Optional[str] = None) -> ToothFairyConfig:
    """
    Load configuration from various sources.

    Priority order:
    1. Provided config file path
    2. Default config file (~/.toothfairy/config.yml)
    3. Environment variables
    """
    if config_path:
        return ToothFairyConfig.from_file(config_path)

    default_config = get_config_path()
    if default_config.exists():
        return ToothFairyConfig.from_file(str(default_config))

    config = ToothFairyConfig.from_env()
    if not config.validate():
        raise ValueError(
            "Configuration incomplete. Please provide configuration via:\n"
            "1. Config file at ~/.toothfairy/config.yml\n"
            "2. Environment variables: TF_API_KEY, TF_WORKSPACE_ID\n"
            "3. CLI arguments\n"
            "Note: TF_BASE_URL and TF_AI_URL default to production endpoints"
        )

    return config


def save_config(config: ToothFairyConfig, config_path: Optional[str] = None) -> None:
    """Save configuration to file."""
    if config_path:
        path = Path(config_path)
    else:
        path = get_config_path()

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)
