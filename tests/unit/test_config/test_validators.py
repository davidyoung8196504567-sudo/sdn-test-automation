"""Unit tests for network validators — no network access needed."""

from __future__ import annotations

import pytest

from sdn_testkit.utils.validators import (
    validate_cidr,
    validate_ip,
    validate_mac,
    validate_port_range,
    validate_vlan_id,
)


# ---------------------------------------------------------------------------
# IP address validation
# ---------------------------------------------------------------------------


class TestValidateIP:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "address",
        [
            "10.0.0.1",
            "192.168.1.1",
            "255.255.255.255",
            "0.0.0.0",
            "::1",
            "fe80::1",
            "2001:db8::1",
        ],
    )
    def test_valid_addresses(self, address: str) -> None:
        assert validate_ip(address) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "address",
        [
            "999.999.999.999",
            "10.0.0",
            "not-an-ip",
            "",
            "10.0.0.1/24",  # CIDR is not a bare IP
        ],
    )
    def test_invalid_addresses(self, address: str) -> None:
        assert validate_ip(address) is False


# ---------------------------------------------------------------------------
# CIDR validation
# ---------------------------------------------------------------------------


class TestValidateCIDR:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "cidr",
        [
            "10.0.0.0/8",
            "192.168.1.0/24",
            "172.16.0.0/12",
            "0.0.0.0/0",
            "10.0.0.1/32",
        ],
    )
    def test_valid_cidrs(self, cidr: str) -> None:
        assert validate_cidr(cidr) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "cidr",
        [
            "10.0.0.0/33",
            "10.0.0.0",
            "not-a-cidr",
            "",
        ],
    )
    def test_invalid_cidrs(self, cidr: str) -> None:
        assert validate_cidr(cidr) is False


# ---------------------------------------------------------------------------
# MAC address validation
# ---------------------------------------------------------------------------


class TestValidateMAC:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "mac",
        [
            "aa:bb:cc:dd:ee:ff",
            "AA:BB:CC:DD:EE:FF",
            "00:11:22:33:44:55",
            "00-11-22-33-44-55",
        ],
    )
    def test_valid_macs(self, mac: str) -> None:
        assert validate_mac(mac) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "mac",
        [
            "aa:bb:cc:dd:ee",  # too short
            "aa:bb:cc:dd:ee:ff:00",  # too long
            "zz:bb:cc:dd:ee:ff",  # invalid hex
            "",
        ],
    )
    def test_invalid_macs(self, mac: str) -> None:
        assert validate_mac(mac) is False


# ---------------------------------------------------------------------------
# VLAN ID validation
# ---------------------------------------------------------------------------


class TestValidateVLAN:
    @pytest.mark.unit
    @pytest.mark.parametrize("vlan_id", [1, 100, 4094])
    def test_valid_vlans(self, vlan_id: int) -> None:
        assert validate_vlan_id(vlan_id) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("vlan_id", [0, -1, 4095, 9999])
    def test_invalid_vlans(self, vlan_id: int) -> None:
        assert validate_vlan_id(vlan_id) is False


# ---------------------------------------------------------------------------
# Port range validation
# ---------------------------------------------------------------------------


class TestValidatePortRange:
    @pytest.mark.unit
    @pytest.mark.parametrize("port", [1, 22, 80, 443, 8181, 65535])
    def test_valid_ports(self, port: int) -> None:
        assert validate_port_range(port) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("port", [0, -1, 65536, 100000])
    def test_invalid_ports(self, port: int) -> None:
        assert validate_port_range(port) is False
