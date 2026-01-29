"""Configuration loading and management."""

from pathlib import Path
from typing import Optional, Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import-not-found]

# Default config paths (XDG)
CONFIG_PATHS = [
    Path.cwd() / "xair.toml",
    Path.cwd() / "config.toml",
    Path.home() / ".config" / "xair" / "config.toml",
]

DEFAULT_CONFIG = """\
# xair CLI configuration

[connection]
# ip = "192.168.1.50"
# model = "XR18"

[defaults]
# timeout = 5.0
"""


def load_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    """Load configuration from TOML file."""
    paths = [config_path] if config_path else CONFIG_PATHS
    for path in paths:
        if path and path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)
    return {}
