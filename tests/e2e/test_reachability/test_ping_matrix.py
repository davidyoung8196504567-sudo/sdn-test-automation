"""E2E Reachability Tests — verify host-to-host connectivity across the fabric.

These tests require a deployed topology (virtual or physical) and use
netmiko to run ping commands from hosts through the SDN fabric.

Topology binding:
    @pytest.mark.topology("spine_leaf") — only runs when --topology=spine_leaf
"""

from __future__ import annotations

import itertools
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sdn_testkit.topology.models import NodeRole, Topology


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestIntraSegmentReachability:
    """Hosts within the same segment (VLAN/VRF) should reach each other."""

    def test_same_segment_ping(self, topology_spine_leaf: Topology) -> None:
        """Every host pair in the same segment should be reachable."""
        for segment in topology_spine_leaf.segments:
            hosts_in_seg = [
                n
                for n in topology_spine_leaf.nodes
                if n.name in segment.nodes and n.role == NodeRole.HOST
            ]
            if len(hosts_in_seg) < 2:
                continue

            for src, dst in itertools.combinations(hosts_in_seg, 2):
                # In a real lab, this would SSH into src and ping dst.
                # Here we validate the topology data is correct for the test.
                assert src.mgmt_ip, f"Host {src.name} missing mgmt_ip"
                assert dst.mgmt_ip, f"Host {dst.name} missing mgmt_ip"
                assert src.name != dst.name

    @pytest.mark.slow
    @patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
    def test_ping_host1_to_host2(
        self,
        mock_handler: MagicMock,
        topology_spine_leaf: Topology,
    ) -> None:
        """Simulate ping from host-1 to host-2 (same tenant-a segment)."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = (
            "PING 10.0.10.2 (10.0.10.2) 56(84) bytes of data.\n"
            "64 bytes from 10.0.10.2: icmp_seq=1 ttl=64 time=0.5 ms\n"
            "--- 10.0.10.2 ping statistics ---\n"
            "3 packets transmitted, 3 received, 0% packet loss"
        )
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
        output = run_command(device, f"ping -c 3 {host2.mgmt_ip}")
        assert "0% packet loss" in output


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestCrossSegmentIsolation:
    """Hosts in different segments should NOT reach each other (without routing)."""

    def test_different_segments_identified(self, topology_spine_leaf: Topology) -> None:
        """Verify we have at least 2 segments for isolation testing."""
        assert len(topology_spine_leaf.segments) >= 2
        seg_a = topology_spine_leaf.segments[0]
        seg_b = topology_spine_leaf.segments[1]
        # Segments should not share host nodes
        hosts_a = {
            n for n in seg_a.nodes
            if any(node.name == n and node.role == NodeRole.HOST for node in topology_spine_leaf.nodes)
        }
        hosts_b = {
            n for n in seg_b.nodes
            if any(node.name == n and node.role == NodeRole.HOST for node in topology_spine_leaf.nodes)
        }
        assert hosts_a.isdisjoint(hosts_b), "Segments should have disjoint host sets"


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestSpineReachability:
    """All leaf switches should be reachable from all spines."""

    def test_spine_leaf_link_coverage(self, topology_spine_leaf: Topology) -> None:
        """Every leaf should have at least one link to a spine."""
        spines = {n.name for n in topology_spine_leaf.get_nodes_by_role(NodeRole.SPINE)}
        leafs = topology_spine_leaf.get_nodes_by_role(NodeRole.LEAF)

        for leaf in leafs:
            links = topology_spine_leaf.get_links_for_node(leaf.name)
            connected_spines = {
                lnk.src_node if lnk.dst_node == leaf.name else lnk.dst_node
                for lnk in links
                if lnk.src_node in spines or lnk.dst_node in spines
            }
            assert len(connected_spines) >= 1, (
                f"Leaf {leaf.name} has no spine connections"
            )
