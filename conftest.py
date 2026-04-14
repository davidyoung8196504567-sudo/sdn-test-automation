"""Root conftest.py — shared fixtures available to all test layers.

Fixtures are organized by scope:
  - session: controller clients, nornir instances, topology discovery
  - function: per-test device connections, fresh controller state

Compatible with pytest >=9.0 and Python >=3.10.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any, Generator

import pytest
import yaml

from sdn_testkit.controllers.base import ControllerConfig
from sdn_testkit.controllers.odl import OpenDaylightController
from sdn_testkit.controllers.onos import ONOSController
from sdn_testkit.topology.loader import load_topology, discover_topologies
from sdn_testkit.topology.models import Topology

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
TOPOLOGIES_DIR = ROOT_DIR / "topologies"
INVENTORY_DIR = ROOT_DIR / "inventory"
FIXTURES_DIR = ROOT_DIR / "fixtures"


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom CLI options for SDN test runs."""
    parser.addoption(
        "--controller-host",
        default=os.getenv("SDN_CONTROLLER_HOST", "127.0.0.1"),
        help="SDN controller hostname or IP",
    )
    parser.addoption(
        "--controller-port",
        default=int(os.getenv("SDN_CONTROLLER_PORT", "8181")),
        type=int,
        help="SDN controller API port",
    )
    parser.addoption(
        "--controller-type",
        default=os.getenv("SDN_CONTROLLER_TYPE", "odl"),
        choices=["odl", "onos"],
        help="Controller type: odl or onos",
    )
    parser.addoption(
        "--controller-user",
        default=os.getenv("SDN_CONTROLLER_USER", "admin"),
        help="Controller API username",
    )
    parser.addoption(
        "--controller-pass",
        default=os.getenv("SDN_CONTROLLER_PASS", "admin"),
        help="Controller API password",
    )
    parser.addoption(
        "--topology",
        default=os.getenv("SDN_TOPOLOGY", ""),
        help="Name of topology bundle to activate (empty = all)",
    )
    parser.addoption(
        "--inventory-dir",
        default=str(INVENTORY_DIR),
        help="Path to Nornir inventory directory",
    )


# ---------------------------------------------------------------------------
# Marker-based topology filtering
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip tests whose @pytest.mark.topology(name) doesn't match --topology."""
    requested = config.getoption("--topology")
    if not requested:
        return  # No filter — run everything

    for item in items:
        topo_markers = list(item.iter_markers(name="topology"))
        if topo_markers:
            names = [m.args[0] for m in topo_markers if m.args]
            if requested not in names:
                item.add_marker(
                    pytest.mark.skip(
                        reason=f"Topology '{requested}' not in {names}"
                    )
                )


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def controller_config(request: pytest.FixtureRequest) -> ControllerConfig:
    """Build controller config from CLI options / env vars."""
    return ControllerConfig(
        host=request.config.getoption("--controller-host"),
        port=request.config.getoption("--controller-port"),
        username=request.config.getoption("--controller-user"),
        password=request.config.getoption("--controller-pass"),
    )


@pytest.fixture(scope="session")
def controller(
    request: pytest.FixtureRequest, controller_config: ControllerConfig
) -> Generator[Any, None, None]:
    """Provide a session-scoped SDN controller client.

    Automatically selects ODL or ONOS based on ``--controller-type``.
    """
    ctype = request.config.getoption("--controller-type")
    if ctype == "onos":
        ctrl = ONOSController(controller_config)
    else:
        ctrl = OpenDaylightController(controller_config)

    yield ctrl
    ctrl.close()


@pytest.fixture(scope="session")
def all_topologies() -> dict[str, Path]:
    """Discover all available topology bundles."""
    return discover_topologies(TOPOLOGIES_DIR)


@pytest.fixture(scope="session")
def active_topology(request: pytest.FixtureRequest) -> Topology | None:
    """Load the topology specified by ``--topology``, or None if unset."""
    name = request.config.getoption("--topology")
    if not name:
        return None

    topologies = discover_topologies(TOPOLOGIES_DIR)
    if name not in topologies:
        pytest.skip(f"Topology '{name}' not found in {TOPOLOGIES_DIR}")

    return load_topology(topologies[name])


# ---------------------------------------------------------------------------
# Function-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_device() -> dict[str, Any]:
    """Return a sample device dict for unit tests (no real connection)."""
    return {
        "host": "192.168.1.1",
        "device_type": "linux",
        "username": "admin",
        "password": "admin",
        "port": 22,
    }


@pytest.fixture
def sample_flow() -> dict[str, Any]:
    """Return a sample OpenFlow-style flow rule dict."""
    return {
        "id": "test-flow-001",
        "table_id": 0,
        "priority": 100,
        "match": {
            "in-port": "1",
            "ethernet-match": {
                "ethernet-type": {"type": 2048}  # IPv4
            },
            "ipv4-destination": "10.0.0.0/24",
        },
        "instructions": {
            "instruction": [
                {
                    "order": 0,
                    "apply-actions": {
                        "action": [{"order": 0, "output-action": {"output-node-connector": "2"}}]
                    },
                }
            ]
        },
    }


@pytest.fixture
def topology_spine_leaf() -> Topology:
    """Load the spine-leaf topology for testing."""
    topo_file = TOPOLOGIES_DIR / "spine_leaf" / "topology.yaml"
    if not topo_file.exists():
        pytest.skip("spine_leaf topology not available")
    return load_topology(topo_file)
