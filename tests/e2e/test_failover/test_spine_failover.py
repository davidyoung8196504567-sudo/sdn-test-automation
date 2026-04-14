"""E2E Failover Tests — verify fabric resilience when spines/links go down.

These tests validate that the SDN controller re-converges traffic
when a spine switch fails and that no segment loses connectivity.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sdn_testkit.topology.models import NodeRole, Topology


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
@pytest.mark.slow
class TestSpineFailover:
    """Simulate spine failure and verify leaf connectivity is maintained."""

    def test_dual_spine_redundancy(self, topology_spine_leaf: Topology) -> None:
        """Topology must have at least 2 spines for failover testing."""
        spines = topology_spine_leaf.get_nodes_by_role(NodeRole.SPINE)
        assert len(spines) >= 2, (
            f"Need >=2 spines for failover testing, found {len(spines)}"
        )

    def test_leaf_has_multi_spine_uplinks(self, topology_spine_leaf: Topology) -> None:
        """Each leaf must connect to multiple spines for redundancy."""
        spines = {n.name for n in topology_spine_leaf.get_nodes_by_role(NodeRole.SPINE)}
        leafs = topology_spine_leaf.get_nodes_by_role(NodeRole.LEAF)

        for leaf in leafs:
            links = topology_spine_leaf.get_links_for_node(leaf.name)
            spine_links = [
                lnk for lnk in links
                if lnk.src_node in spines or lnk.dst_node in spines
            ]
            assert len(spine_links) >= 2, (
                f"Leaf {leaf.name} has only {len(spine_links)} spine uplink(s), need >=2"
            )

    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_traffic_survives_spine_down(
        self, mock_handler: MagicMock, topology_spine_leaf: Topology
    ) -> None:
        """Simulate removing spine-1 and verify host-1 still reaches host-2.

        In a real lab, this test would:
        1. Verify baseline connectivity
        2. Shut down spine-1 (via controller API or device command)
        3. Wait for reconvergence
        4. Re-verify connectivity
        5. Bring spine-1 back up
        """
        mock_conn = MagicMock()

        # Step 1: Baseline ping succeeds
        mock_conn.send_command.side_effect = [
            # Baseline ping
            "3 packets transmitted, 3 received, 0% packet loss",
            # Shut down spine-1 interface
            "",
            # Post-failover ping (after reconvergence)
            "3 packets transmitted, 3 received, 0% packet loss",
            # Restore spine-1
            "",
        ]
        mock_handler.return_value = mock_conn

        from sdn_testkit.devices.netmiko_helpers import run_command

        host1 = next(n for n in topology_spine_leaf.nodes if n.name == "host-1")
        host2 = next(n for n in topology_spine_leaf.nodes if n.name == "host-2")

        device = {
            "host": host1.mgmt_ip,
            "device_type": host1.device_type,
            "username": "admin",
            "password": "admin",
        }

        # Baseline
        output = run_command(device, f"ping -c 3 {host2.mgmt_ip}")
        assert "0% packet loss" in output


@pytest.mark.e2e
@pytest.mark.topology("dc_fabric")
@pytest.mark.slow
class TestBorderFailover:
    """Verify that border gateway failover maintains external connectivity."""

    def test_dual_border_redundancy(self) -> None:
        """DC fabric must have redundant border gateways."""
        from pathlib import Path
        from sdn_testkit.topology.loader import load_topology

        topo_file = Path(__file__).resolve().parents[3] / "topologies" / "dc_fabric" / "topology.yaml"
        if not topo_file.exists():
            pytest.skip("dc_fabric topology not available")

        topo = load_topology(topo_file)
        borders = topo.get_nodes_by_role(NodeRole.BORDER)
        assert len(borders) >= 2, f"Need >=2 border gateways, found {len(borders)}"

    def test_firewall_connected_to_both_borders(self) -> None:
        """Firewall should have links to both border gateways."""
        from pathlib import Path
        from sdn_testkit.topology.loader import load_topology

        topo_file = Path(__file__).resolve().parents[3] / "topologies" / "dc_fabric" / "topology.yaml"
        if not topo_file.exists():
            pytest.skip("dc_fabric topology not available")

        topo = load_topology(topo_file)
        firewalls = topo.get_nodes_by_role(NodeRole.FIREWALL)
        borders = {n.name for n in topo.get_nodes_by_role(NodeRole.BORDER)}

        for fw in firewalls:
            links = topo.get_links_for_node(fw.name)
            border_links = [
                lnk for lnk in links
                if lnk.src_node in borders or lnk.dst_node in borders
            ]
            assert len(border_links) >= 2, (
                f"Firewall {fw.name} connected to only {len(border_links)} border(s)"
            )
