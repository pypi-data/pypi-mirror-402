"""
Configuration settings for LeenO MCP Server.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UnoConfig:
    """LibreOffice UNO connection configuration."""

    host: str = "localhost"
    port: int = 2002
    connection_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

    @property
    def connection_string(self) -> str:
        """Generate UNO connection string."""
        return f"uno:socket,host={self.host},port={self.port};urp;StarOffice.ComponentContext"


@dataclass
class LeenoConfig:
    """LeenO paths and settings."""

    leeno_path: Optional[str] = None
    template_path: Optional[str] = None

    def __post_init__(self):
        if self.leeno_path is None:
            # Try to find LeenO installation
            self.leeno_path = self._find_leeno_path()

        if self.template_path is None and self.leeno_path:
            self.template_path = os.path.join(self.leeno_path, "template")

    def _find_leeno_path(self) -> Optional[str]:
        """Try to locate LeenO installation."""
        # Check environment variable first
        env_path = os.environ.get("LEENO_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # Check common locations
        possible_paths = [
            # Relative to this server
            Path(__file__).parent.parent.parent.parent / "src",
            # Standard installation paths
            Path.home() / ".config" / "libreoffice" / "4" / "user" / "Scripts" / "python" / "LeenO",
            Path("/usr/share/libreoffice/share/Scripts/python/LeenO"),
        ]

        for path in possible_paths:
            if path.exists() and (path / "pyleeno.py").exists():
                return str(path)

        return None


@dataclass
class ServerConfig:
    """MCP Server configuration."""

    name: str = "leeno-mcp"
    version: str = "0.1.0"
    log_level: str = "INFO"
    log_file: Optional[str] = None

    uno: UnoConfig = field(default_factory=UnoConfig)
    leeno: LeenoConfig = field(default_factory=LeenoConfig)


def load_config() -> ServerConfig:
    """Load configuration from environment variables."""
    config = ServerConfig()

    # Override from environment
    if host := os.environ.get("LEENO_UNO_HOST"):
        config.uno.host = host

    if port := os.environ.get("LEENO_UNO_PORT"):
        config.uno.port = int(port)

    if leeno_path := os.environ.get("LEENO_PATH"):
        config.leeno.leeno_path = leeno_path

    if log_level := os.environ.get("LEENO_LOG_LEVEL"):
        config.log_level = log_level

    if log_file := os.environ.get("LEENO_LOG_FILE"):
        config.log_file = log_file

    return config


# Global config instance
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get or create global configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
