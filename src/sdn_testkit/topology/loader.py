"""Load and discover topology YAML files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from sdn_testkit.topology.models import Topology

logger = logging.getLogger(__name__)

DEFAULT_TOPOLOGIES_DIR = Path(__file__).resolve().parents[3] / "topologies"


def load_topology(path: str | Path) -> Topology:
    """Load a topology from a YAML file.

    Args:
        path: Path to the topology YAML file.

    Returns:
        Validated Topology model.

    Raises:
        FileNotFoundError: If the file does not exist.
        pydantic.ValidationError: If the YAML does not match the schema.
    """
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Topology file not found: {filepath}")

    with filepath.open() as f:
        data = yaml.safe_load(f)

    logger.info("Loaded topology '%s' from %s", data.get("name", "unknown"), filepath)
    return Topology(**data)


def discover_topologies(
    topologies_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Discover all topology YAML files in a directory tree.

    Returns:
        Dict mapping topology name → file path.
    """
    base = Path(topologies_dir) if topologies_dir else DEFAULT_TOPOLOGIES_DIR
    found: dict[str, Path] = {}

    if not base.exists():
        logger.warning("Topologies directory does not exist: %s", base)
        return found

    for yaml_file in sorted(base.rglob("*.yaml")):
        try:
            with yaml_file.open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "name" in data and "nodes" in data:
                found[data["name"]] = yaml_file
                logger.debug("Discovered topology '%s' at %s", data["name"], yaml_file)
        except Exception:
            logger.warning("Skipping invalid YAML: %s", yaml_file, exc_info=True)

    return found
