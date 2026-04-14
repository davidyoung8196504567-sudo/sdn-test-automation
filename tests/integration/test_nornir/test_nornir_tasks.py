"""Integration tests for Nornir task execution.

Mocks the Nornir/netmiko transport layer to validate task orchestration
logic without requiring live devices.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sdn_testkit.devices.nornir_helpers import (
    collect_facts,
    init_nornir,
    run_nornir_config,
    run_nornir_task,
)


@pytest.fixture
def mock_nornir() -> MagicMock:
    """Create a mock Nornir instance with realistic structure."""
    nr = MagicMock()

    # Mock filter to return self (no-op filter)
    nr.filter.return_value = nr

    # Mock a successful AggregatedResult
    mock_result = MagicMock()
    mock_host_result = MagicMock()
    mock_host_result.result = "command output here"
    mock_host_result.failed = False
    mock_result.items.return_value = [("spine-1", mock_host_result)]
    mock_result.__iter__ = lambda self: iter(["spine-1"])
    mock_result.__getitem__ = lambda self, key: mock_host_result

    nr.run.return_value = mock_result
    return nr


class TestNornirTaskExecution:
    @pytest.mark.integration
    def test_run_task_without_filter(self, mock_nornir: MagicMock) -> None:
        """Running without filter should use all hosts."""
        result = run_nornir_task(mock_nornir, "show version")
        mock_nornir.run.assert_called_once()
        mock_nornir.filter.assert_not_called()

    @pytest.mark.integration
    def test_run_task_with_role_filter(self, mock_nornir: MagicMock) -> None:
        """Running with filter should call nr.filter() first."""
        run_nornir_task(mock_nornir, "show ip route", filter_params={"role": "spine"})
        mock_nornir.filter.assert_called_once_with(role="spine")

    @pytest.mark.integration
    def test_run_config_commands(self, mock_nornir: MagicMock) -> None:
        run_nornir_config(mock_nornir, ["interface Ethernet1", "shutdown"])
        mock_nornir.run.assert_called_once()


class TestNornirInit:
    @pytest.mark.integration
    @patch("sdn_testkit.devices.nornir_helpers.InitNornir")
    def test_init_with_default_inventory(self, mock_init: MagicMock) -> None:
        """init_nornir should configure SimpleInventory with default paths."""
        mock_init.return_value = MagicMock()
        nr = init_nornir()
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args
        inv_options = call_kwargs.kwargs.get("inventory") or call_kwargs[1].get("inventory", {})
        assert inv_options["plugin"] == "SimpleInventory"

    @pytest.mark.integration
    @patch("sdn_testkit.devices.nornir_helpers.InitNornir")
    def test_init_with_custom_inventory(self, mock_init: MagicMock, tmp_path: Path) -> None:
        """Custom inventory dir should override defaults."""
        mock_init.return_value = MagicMock()
        nr = init_nornir(inventory_dir=tmp_path, num_workers=5)
        call_kwargs = mock_init.call_args
        inv_options = call_kwargs.kwargs.get("inventory") or call_kwargs[1].get("inventory", {})
        assert str(tmp_path) in inv_options["options"]["host_file"]

    @pytest.mark.integration
    @patch("sdn_testkit.devices.nornir_helpers.InitNornir")
    def test_init_custom_workers(self, mock_init: MagicMock) -> None:
        mock_init.return_value = MagicMock()
        init_nornir(num_workers=20)
        call_kwargs = mock_init.call_args
        runner = call_kwargs.kwargs.get("runner") or call_kwargs[1].get("runner", {})
        assert runner["options"]["num_workers"] == 20


class TestCollectFacts:
    @pytest.mark.integration
    def test_collect_facts_structure(self, mock_nornir: MagicMock) -> None:
        """collect_facts should return dict keyed by hostname."""
        # Make items() return proper data for iteration
        mock_host_result = MagicMock()
        mock_host_result.result = "some output"
        mock_result = MagicMock()
        mock_result.items.return_value = [("spine-1", mock_host_result)]
        mock_nornir.run.return_value = mock_result

        facts = collect_facts(mock_nornir)
        assert isinstance(facts, dict)
        # Should have called run 3 times (hostname, version, interfaces)
        assert mock_nornir.run.call_count == 3
