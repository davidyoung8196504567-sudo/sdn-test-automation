"""Nornir initialization and task-running helpers.

Supports loading inventory from YAML files or inline dicts,
with sensible defaults for SDN lab environments.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import AggregatedResult, Result, Task
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config

logger = logging.getLogger(__name__)

DEFAULT_INVENTORY_DIR = Path(__file__).resolve().parents[3] / "inventory"


def init_nornir(
    inventory_dir: str | Path | None = None,
    num_workers: int = 10,
    extras: dict[str, Any] | None = None,
) -> Nornir:
    """Initialize a Nornir instance with SimpleInventory.

    Args:
        inventory_dir: Directory containing hosts.yaml, groups.yaml, defaults.yaml.
        num_workers: Concurrent connections.
        extras: Additional Nornir config overrides.

    Returns:
        Configured Nornir instance.
    """
    inv_dir = Path(inventory_dir) if inventory_dir else DEFAULT_INVENTORY_DIR

    config: dict[str, Any] = {
        "runner": {"plugin": "threaded", "options": {"num_workers": num_workers}},
        "inventory": {
            "plugin": "SimpleInventory",
            "options": {
                "host_file": str(inv_dir / "hosts.yaml"),
                "group_file": str(inv_dir / "groups.yaml"),
                "defaults_file": str(inv_dir / "defaults.yaml"),
            },
        },
        "logging": {"enabled": False},  # Let pytest control logging
    }

    if extras:
        config.update(extras)

    return InitNornir(**config)


def run_nornir_task(
    nr: Nornir,
    command: str,
    filter_params: dict[str, Any] | None = None,
) -> AggregatedResult:
    """Run a show command across filtered hosts.

    Args:
        nr: Nornir instance.
        command: CLI command string.
        filter_params: Kwargs for ``nr.filter()`` — e.g. ``{"role": "spine"}``.

    Returns:
        AggregatedResult from the task run.
    """
    targets = nr.filter(**filter_params) if filter_params else nr
    result = targets.run(task=netmiko_send_command, command_string=command)
    return result


def run_nornir_config(
    nr: Nornir,
    config_commands: list[str],
    filter_params: dict[str, Any] | None = None,
) -> AggregatedResult:
    """Push config commands across filtered hosts.

    Args:
        nr: Nornir instance.
        config_commands: List of configuration commands.
        filter_params: Kwargs for ``nr.filter()``.

    Returns:
        AggregatedResult from the task run.
    """
    targets = nr.filter(**filter_params) if filter_params else nr
    result = targets.run(task=netmiko_send_config, config_commands=config_commands)
    return result


def collect_facts(nr: Nornir, filter_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect basic facts (hostname, interfaces, version) from devices.

    Returns a dict keyed by host name.
    """
    targets = nr.filter(**filter_params) if filter_params else nr
    facts: dict[str, Any] = {}

    commands = {
        "hostname": "hostname",
        "version": "show version",
        "interfaces": "show ip interface brief",
    }

    for fact_name, cmd in commands.items():
        result = targets.run(task=netmiko_send_command, command_string=cmd)
        for host_name, host_result in result.items():
            facts.setdefault(host_name, {})[fact_name] = host_result.result

    return facts
