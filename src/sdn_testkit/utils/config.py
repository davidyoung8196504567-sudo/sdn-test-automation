"""Configuration loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Supports environment variable interpolation via ``${VAR_NAME}`` syntax.
    """
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with filepath.open() as f:
        raw = f.read()

    # Simple env var interpolation
    for key, value in os.environ.items():
        raw = raw.replace(f"${{{key}}}", value)

    return yaml.safe_load(raw)


def get_env_config() -> dict[str, str]:
    """Collect SDN-related environment variables.

    Looks for vars prefixed with ``SDN_`` and returns them as a dict
    with the prefix stripped and keys lowercased.
    """
    prefix = "SDN_"
    return {
        k[len(prefix):].lower(): v
        for k, v in os.environ.items()
        if k.startswith(prefix)
    }
