"""Unit tests for topology Pydantic models — pure validation, no I/O."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdn_testkit.topology.models import Link, Node, NodeRole, Segment, Topology


# ---------------------------------------------------------------------------
# Node model
# ---------------------------------------------------------------------------


class TestNodeModel:
    @pytest.mark.unit
    def test_create_valid_node(self) -> None:
        node = Node(name="spine-1", role=NodeRole.SPINE, mgmt_ip="10.0.0.1")
        assert node.name == "spine-1"
        assert node.role == NodeRole.SPINE

    @pytest.mark.unit
    def test_node_with_interfaces(self) -> None:
        node = Node(
            name="leaf-1",
            role=NodeRole.LEAF,
            interfaces=["Ethernet1", "Ethernet2"],
        )
        assert len(node.interfaces) == 2

    @pytest.mark.unit
    def test_invalid_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Node(name="bad", role="nonexistent_role")


# ---------------------------------------------------------------------------
# Link model
# ---------------------------------------------------------------------------


class TestLinkModel:
    @pytest.mark.unit
    def test_create_valid_link(self) -> None:
        link = Link(
            src_node="spine-1",
            src_interface="Ethernet1",
            dst_node="leaf-1",
            dst_interface="Ethernet1",
        )
        assert link.bandwidth == "1G"  # default

    @pytest.mark.unit
    def test_link_custom_bandwidth(self) -> None:
        link = Link(
            src_node="spine-1",
            src_interface="Ethernet1",
            dst_node="leaf-1",
            dst_interface="Ethernet1",
            bandwidth="100G",
        )
        assert link.bandwidth == "100G"


# ---------------------------------------------------------------------------
# Topology model (cross-validation)
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_topology_data() -> dict:
    return {
        "name": "test-topo",
        "nodes": [
            {"name": "sw-1", "role": "spine"},
            {"name": "sw-2", "role": "leaf"},
        ],
        "links": [
            {
                "src_node": "sw-1",
                "src_interface": "eth1",
                "dst_node": "sw-2",
                "dst_interface": "eth1",
            }
        ],
    }


class TestTopologyModel:
    @pytest.mark.unit
    def test_valid_topology(self, minimal_topology_data: dict) -> None:
        topo = Topology(**minimal_topology_data)
        assert topo.name == "test-topo"
        assert len(topo.nodes) == 2
        assert len(topo.links) == 1

    @pytest.mark.unit
    def test_link_references_unknown_node(self, minimal_topology_data: dict) -> None:
        """Links referencing non-existent nodes should fail validation."""
        minimal_topology_data["links"][0]["src_node"] = "ghost-node"
        with pytest.raises(ValidationError, match="ghost-node"):
            Topology(**minimal_topology_data)

    @pytest.mark.unit
    def test_segment_references_unknown_node(self, minimal_topology_data: dict) -> None:
        minimal_topology_data["segments"] = [
            {"name": "seg-1", "vlan_id": 100, "nodes": ["sw-1", "unknown-node"]}
        ]
        with pytest.raises(ValidationError, match="unknown-node"):
            Topology(**minimal_topology_data)

    @pytest.mark.unit
    def test_get_nodes_by_role(self, minimal_topology_data: dict) -> None:
        topo = Topology(**minimal_topology_data)
        spines = topo.get_nodes_by_role(NodeRole.SPINE)
        assert len(spines) == 1
        assert spines[0].name == "sw-1"

    @pytest.mark.unit
    def test_get_links_for_node(self, minimal_topology_data: dict) -> None:
        topo = Topology(**minimal_topology_data)
        links = topo.get_links_for_node("sw-1")
        assert len(links) == 1

    @pytest.mark.unit
    def test_empty_topology_allowed(self) -> None:
        topo = Topology(name="empty", nodes=[], links=[])
        assert len(topo.nodes) == 0


# ---------------------------------------------------------------------------
# Topology loading from YAML files
# ---------------------------------------------------------------------------


class TestTopologyLoader:
    @pytest.mark.unit
    def test_load_spine_leaf_topology(self) -> None:
        """Validate that the bundled spine_leaf topology parses correctly."""
        from pathlib import Path
        from sdn_testkit.topology.loader import load_topology

        topo_file = Path(__file__).resolve().parents[3] / "topologies" / "spine_leaf" / "topology.yaml"
        if not topo_file.exists():
            pytest.skip("spine_leaf topology file not present")

        topo = load_topology(topo_file)
        assert topo.name == "spine_leaf"
        assert len(topo.get_nodes_by_role(NodeRole.SPINE)) == 2
        assert len(topo.get_nodes_by_role(NodeRole.LEAF)) == 4
        assert len(topo.segments) >= 2

    @pytest.mark.unit
    def test_load_nonexistent_file(self) -> None:
        from sdn_testkit.topology.loader import load_topology

        with pytest.raises(FileNotFoundError):
            load_topology("/nonexistent/topology.yaml")

    @pytest.mark.unit
    def test_discover_topologies(self) -> None:
        from pathlib import Path
        from sdn_testkit.topology.loader import discover_topologies

        topo_dir = Path(__file__).resolve().parents[3] / "topologies"
        found = discover_topologies(topo_dir)
        assert isinstance(found, dict)
        # At minimum we should find the bundled topologies
        assert "spine_leaf" in found
