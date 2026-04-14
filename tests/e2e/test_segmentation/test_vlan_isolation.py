"""E2E Segmentation Tests — verify VLAN/VRF isolation and policy enforcement.

Validates that the SDN controller correctly segments traffic between
tenants and that flow rules enforce expected boundaries.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import responses

from sdn_testkit.controllers.base import ControllerConfig
from sdn_testkit.controllers.odl import OpenDaylightController
from sdn_testkit.topology.models import NodeRole, Topology


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestVLANSegmentation:
    """Validate that VLANs are correctly assigned and isolated."""

    def test_each_segment_has_vlan(self, topology_spine_leaf: Topology) -> None:
        """Every segment should have a VLAN ID assigned."""
        for segment in topology_spine_leaf.segments:
            assert segment.vlan_id is not None, (
                f"Segment '{segment.name}' missing VLAN ID"
            )
            assert 1 <= segment.vlan_id <= 4094, (
                f"Segment '{segment.name}' has invalid VLAN {segment.vlan_id}"
            )

    def test_vlan_ids_are_unique(self, topology_spine_leaf: Topology) -> None:
        """No two segments should share a VLAN ID."""
        vlan_ids = [s.vlan_id for s in topology_spine_leaf.segments if s.vlan_id]
        assert len(vlan_ids) == len(set(vlan_ids)), "Duplicate VLAN IDs found"

    def test_segments_have_assigned_nodes(self, topology_spine_leaf: Topology) -> None:
        """Each segment should have at least one node."""
        for segment in topology_spine_leaf.segments:
            assert len(segment.nodes) > 0, (
                f"Segment '{segment.name}' has no assigned nodes"
            )


@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestFlowRuleVerification:
    """Verify that expected flow rules exist on leaf switches."""

    @responses.activate
    def test_leaf_has_flow_entries(self) -> None:
        """Each leaf should have at least one flow entry for its segment."""
        config = ControllerConfig(host="127.0.0.1", port=8181)
        odl = OpenDaylightController(config)

        responses.add(
            responses.GET,
            "http://127.0.0.1:8181/restconf/operational/opendaylight-inventory:nodes/node/openflow:1/table/0",
            json={
                "flow-node-inventory:table": [
                    {
                        "id": 0,
                        "flow": [
                            {"id": "vlan-10-permit", "priority": 100,
                             "match": {"vlan-match": {"vlan-id": {"vlan-id": 10}}}},
                            {"id": "vlan-20-deny", "priority": 50,
                             "match": {"vlan-match": {"vlan-id": {"vlan-id": 20}}}},
                        ],
                    }
                ]
            },
            status=200,
        )

        flows = odl.get_flows("openflow:1")
        assert len(flows) >= 1
        vlan_flows = [
            f for f in flows
            if "vlan-match" in f.get("match", {})
        ]
        assert len(vlan_flows) >= 1, "No VLAN-based flows found on leaf"


@pytest.mark.e2e
@pytest.mark.topology("dc_fabric")
class TestVRFIsolation:
    """Validate VRF-based segmentation for multi-tenant DC fabric."""

    def test_segments_have_vrf(self) -> None:
        """DC fabric segments should define VRF names."""
        from pathlib import Path
        from sdn_testkit.topology.loader import load_topology

        topo_file = Path(__file__).resolve().parents[3] / "topologies" / "dc_fabric" / "topology.yaml"
        if not topo_file.exists():
            pytest.skip("dc_fabric topology not available")

        topo = load_topology(topo_file)
        for segment in topo.segments:
            assert segment.vrf, f"Segment '{segment.name}' missing VRF in dc_fabric"

    def test_production_and_staging_separated(self) -> None:
        """Production and staging should use different VRFs and VLANs."""
        from pathlib import Path
        from sdn_testkit.topology.loader import load_topology

        topo_file = Path(__file__).resolve().parents[3] / "topologies" / "dc_fabric" / "topology.yaml"
        if not topo_file.exists():
            pytest.skip("dc_fabric topology not available")

        topo = load_topology(topo_file)
        prod = next((s for s in topo.segments if s.name == "production"), None)
        staging = next((s for s in topo.segments if s.name == "staging"), None)

        assert prod is not None and staging is not None
        assert prod.vrf != staging.vrf, "Production and staging must use different VRFs"
        assert prod.vlan_id != staging.vlan_id, "Production and staging must use different VLANs"
