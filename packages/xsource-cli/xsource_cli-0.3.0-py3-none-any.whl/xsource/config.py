"""
Configuration management for XSource CLI.

Handles API keys, settings, and persistent configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

# Config directory
CONFIG_DIR = Path.home() / ".xsource"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

# API settings
DEFAULT_API_URL = "https://api.xsourcesec.com"
DEFAULT_TIMEOUT = 60


@dataclass
class Config:
    """XSource CLI configuration."""
    api_url: str = DEFAULT_API_URL
    timeout: int = DEFAULT_TIMEOUT
    output_format: str = "rich"  # rich, json, plain
    color: bool = True

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)


@dataclass
class Credentials:
    """User credentials."""
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    def load(cls) -> "Credentials":
        """Load credentials from file."""
        if CREDENTIALS_FILE.exists():
            try:
                with open(CREDENTIALS_FILE) as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass

        # Also check environment variables
        api_key = os.environ.get("XSOURCE_API_KEY")
        if api_key:
            return cls(api_key=api_key)

        return cls()

    def save(self) -> None:
        """Save credentials to file (with restricted permissions)."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Write with restricted permissions
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)

        # Set file permissions to user-only read/write
        try:
            CREDENTIALS_FILE.chmod(0o600)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all credentials."""
        self.api_key = None
        self.access_token = None
        self.refresh_token = None
        self.email = None
        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()

    @property
    def is_authenticated(self) -> bool:
        """Check if user has valid credentials."""
        return bool(self.api_key or self.access_token)

    @property
    def auth_header(self) -> Optional[str]:
        """Get authorization header value."""
        if self.access_token:
            return f"Bearer {self.access_token}"
        elif self.api_key:
            return f"Bearer {self.api_key}"
        return None


def get_config() -> Config:
    """Get current configuration."""
    return Config.load()


def get_credentials() -> Credentials:
    """Get current credentials."""
    return Credentials.load()


def ensure_authenticated() -> Credentials:
    """Ensure user is authenticated, raise error if not."""
    creds = get_credentials()
    if not creds.is_authenticated:
        from rich.console import Console
        console = Console()
        console.print("\n[red]Error:[/red] Not authenticated. Run [cyan]xsource login[/cyan] first.\n")
        raise SystemExit(1)
    return creds
