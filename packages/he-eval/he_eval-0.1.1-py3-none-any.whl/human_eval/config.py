"""Configuration management for he-cli.

Handles reading and writing config from ~/.config/he-cli/config.toml.
The config stores server connection details and authentication credentials.

Set HE_CLI_CONFIG_DIR environment variable to override the config directory
(useful for testing).
"""

import os
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _get_config_dir() -> Path:
    """Get config directory, respecting HE_CLI_CONFIG_DIR env var."""
    if env_dir := os.environ.get("HE_CLI_CONFIG_DIR"):
        return Path(env_dir)
    return Path.home() / ".config" / "he-cli"


def _get_config_file() -> Path:
    """Get config file path."""
    return _get_config_dir() / "config.toml"


@dataclass
class ServerConfig:
    """Server connection configuration."""

    url: str = ""


@dataclass
class AuthConfig:
    """Authentication credentials."""

    api_key: str = ""
    expires_at: datetime | None = None
    user_email: str = ""
    user_name: str = ""


@dataclass
class Config:
    """Full CLI configuration."""

    server: ServerConfig
    auth: AuthConfig

    def is_authenticated(self) -> bool:
        """Check if we have valid, non-expired credentials."""
        if not self.auth.api_key:
            return False
        if self.auth.expires_at and self.auth.expires_at < datetime.now():
            return False
        return True

    def has_server(self) -> bool:
        """Check if server URL is configured."""
        return bool(self.server.url)


def load_config() -> Config:
    """Load config from disk, returning defaults if not found."""
    config_file = _get_config_file()
    if not config_file.exists():
        return Config(server=ServerConfig(), auth=AuthConfig())

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    server_data = data.get("server", {})
    auth_data = data.get("auth", {})

    # Parse expiry timestamp if present
    expires_at = None
    if expires_str := auth_data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(expires_str)
        except ValueError:
            pass

    return Config(
        server=ServerConfig(url=server_data.get("url", "")),
        auth=AuthConfig(
            api_key=auth_data.get("api_key", ""),
            expires_at=expires_at,
            user_email=auth_data.get("user_email", ""),
            user_name=auth_data.get("user_name", ""),
        ),
    )


def save_config(config: Config) -> None:
    """Save config to disk."""
    config_dir = _get_config_dir()
    config_file = _get_config_file()

    config_dir.mkdir(parents=True, exist_ok=True)

    # Build TOML content manually (tomllib is read-only)
    lines = []

    # Server section
    lines.append("[server]")
    lines.append(f'url = "{config.server.url}"')
    lines.append("")

    # Auth section
    lines.append("[auth]")
    lines.append(f'api_key = "{config.auth.api_key}"')
    if config.auth.expires_at:
        lines.append(f'expires_at = "{config.auth.expires_at.isoformat()}"')
    lines.append(f'user_email = "{config.auth.user_email}"')
    lines.append(f'user_name = "{config.auth.user_name}"')
    lines.append("")

    config_file.write_text("\n".join(lines))

    # Set restrictive permissions (contains API key)
    config_file.chmod(0o600)


def clear_auth() -> None:
    """Clear authentication credentials from config."""
    config = load_config()
    config.auth = AuthConfig()
    save_config(config)


def set_server_url(url: str) -> None:
    """Set the server URL in config."""
    config = load_config()
    config.server.url = url.rstrip("/")
    save_config(config)


def set_auth(
    api_key: str,
    expires_at: datetime | None = None,
    user_email: str = "",
    user_name: str = "",
) -> None:
    """Set authentication credentials in config."""
    config = load_config()
    config.auth = AuthConfig(
        api_key=api_key,
        expires_at=expires_at,
        user_email=user_email,
        user_name=user_name,
    )
    save_config(config)
