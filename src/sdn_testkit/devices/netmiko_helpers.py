"""Netmiko convenience wrappers for SDN device interaction.

Provides a context-managed DeviceConnection and standalone helpers
that accept inventory-style dicts so tests stay concise.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from netmiko import ConnectHandler, BaseConnection

logger = logging.getLogger(__name__)


@dataclass
class DeviceParams:
    """Normalized device connection parameters."""

    host: str
    device_type: str = "linux"
    username: str = "admin"
    password: str = "admin"
    port: int = 22
    secret: str = ""
    timeout: int = 30

    def to_netmiko_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "host": self.host,
            "device_type": self.device_type,
            "username": self.username,
            "password": self.password,
            "port": self.port,
            "timeout": self.timeout,
        }
        if self.secret:
            d["secret"] = self.secret
        return d


class DeviceConnection:
    """Context-managed netmiko connection.

    Usage::

        with DeviceConnection(params) as conn:
            output = conn.send_command("show ip route")
    """

    def __init__(self, params: DeviceParams) -> None:
        self.params = params
        self._conn: BaseConnection | None = None

    def __enter__(self) -> BaseConnection:
        logger.info("Connecting to %s (%s)", self.params.host, self.params.device_type)
        self._conn = ConnectHandler(**self.params.to_netmiko_dict())
        return self._conn

    def __exit__(self, *exc: Any) -> None:
        if self._conn:
            self._conn.disconnect()
            logger.info("Disconnected from %s", self.params.host)


def run_command(device: dict[str, Any], command: str) -> str:
    """Run a single command on a device and return the output.

    ``device`` is an inventory-style dict with keys matching DeviceParams fields.
    """
    params = DeviceParams(**{k: v for k, v in device.items() if k in DeviceParams.__dataclass_fields__})
    with DeviceConnection(params) as conn:
        output: str = conn.send_command(command)
    return output


def run_commands(device: dict[str, Any], commands: list[str]) -> list[str]:
    """Run multiple commands on a device, returning output for each."""
    params = DeviceParams(**{k: v for k, v in device.items() if k in DeviceParams.__dataclass_fields__})
    results: list[str] = []
    with DeviceConnection(params) as conn:
        for cmd in commands:
            results.append(conn.send_command(cmd))
    return results


def run_config_commands(device: dict[str, Any], config_commands: list[str]) -> str:
    """Send configuration commands to a device."""
    params = DeviceParams(**{k: v for k, v in device.items() if k in DeviceParams.__dataclass_fields__})
    with DeviceConnection(params) as conn:
        output: str = conn.send_config_set(config_commands)
    return output
