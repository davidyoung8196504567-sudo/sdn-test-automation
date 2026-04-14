"""Input validators for network parameters."""

from __future__ import annotations

import ipaddress
import re


def validate_ip(address: str) -> bool:
    """Return True if ``address`` is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def validate_cidr(cidr: str) -> bool:
    """Return True if ``cidr`` is a valid CIDR notation (e.g. 10.0.0.0/24)."""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def validate_mac(mac: str) -> bool:
    """Return True if ``mac`` is a valid MAC address (colon or hyphen separated)."""
    pattern = re.compile(r"^([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}$")
    return bool(pattern.match(mac))


def validate_vlan_id(vlan_id: int) -> bool:
    """Return True if ``vlan_id`` is in the valid range (1–4094)."""
    return 1 <= vlan_id <= 4094


def validate_port_range(port: int) -> bool:
    """Return True if ``port`` is in valid TCP/UDP range (1–65535)."""
    return 1 <= port <= 65535
