"""Integration tests for netmiko device interactions.

Uses unittest.mock to simulate netmiko sessions in CI.
For lab runs, set SDN_LAB_DEVICES=true and provide real inventory.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from sdn_testkit.devices.netmiko_helpers import (
    DeviceConnection,
    DeviceParams,
    run_command,
    run_commands,
    run_config_commands,
)


# ---------------------------------------------------------------------------
# Mocked tests (run in CI without real devices)
# ---------------------------------------------------------------------------


class TestNetmikoMocked:
    @pytest.mark.integration
    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_run_single_command(self, mock_handler: MagicMock) -> None:
        """run_command should call send_command and return output."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = "Ethernet1 is up"
        mock_handler.return_value = mock_conn

        device = {
            "host": "10.255.1.1",
            "device_type": "arista_eos",
            "username": "admin",
            "password": "admin",
        }
        output = run_command(device, "show interfaces status")
        assert "Ethernet1" in output
        mock_conn.send_command.assert_called_once_with("show interfaces status")
        mock_conn.disconnect.assert_called_once()

    @pytest.mark.integration
    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_run_multiple_commands(self, mock_handler: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = [
            "route table output",
            "arp table output",
        ]
        mock_handler.return_value = mock_conn

        device = {"host": "10.255.1.1", "device_type": "arista_eos",
                  "username": "admin", "password": "admin"}
        outputs = run_commands(device, ["show ip route", "show ip arp"])
        assert len(outputs) == 2
        assert "route table" in outputs[0]
        assert "arp table" in outputs[1]

    @pytest.mark.integration
    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_run_config_commands(self, mock_handler: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_conn.send_config_set.return_value = "config applied"
        mock_handler.return_value = mock_conn

        device = {"host": "10.255.1.1", "device_type": "arista_eos",
                  "username": "admin", "password": "admin"}
        output = run_config_commands(device, [
            "interface Ethernet1",
            "description test-link",
            "no shutdown",
        ])
        assert "config applied" in output

    @pytest.mark.integration
    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_device_connection_context_manager(self, mock_handler: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_handler.return_value = mock_conn

        params = DeviceParams(host="10.255.1.1", device_type="arista_eos")
        with DeviceConnection(params) as conn:
            conn.send_command("show version")
        mock_conn.disconnect.assert_called_once()


# ---------------------------------------------------------------------------
# Live device tests (only run in lab environment)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.getenv("SDN_LAB_DEVICES") != "true",
    reason="Live device tests require SDN_LAB_DEVICES=true",
)
class TestNetmikoLive:
    """Tests that run against real devices. Set SDN_LAB_DEVICES=true to enable."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_live_show_version(self, sample_device: dict) -> None:
        output = run_command(sample_device, "show version")
        assert output  # Non-empty response

    @pytest.mark.integration
    @pytest.mark.slow
    def test_live_interface_status(self, sample_device: dict) -> None:
        output = run_command(sample_device, "show ip interface brief")
        assert output
