"""Integration tests for OpenDaylight controller API.

These tests require a running ODL instance. In CI, they use the
``responses`` library to mock HTTP calls. In a lab environment,
set ``--controller-host`` to a live controller.

Markers:
    integration — requires controller API or mock
    smoke — quick sanity checks
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
import responses

from sdn_testkit.controllers.base import ControllerConfig
from sdn_testkit.controllers.odl import OpenDaylightController


@pytest.fixture
def odl_config() -> ControllerConfig:
    return ControllerConfig(host="127.0.0.1", port=8181)


@pytest.fixture
def odl(odl_config: ControllerConfig) -> OpenDaylightController:
    return OpenDaylightController(odl_config)


class TestODLTopology:
    @pytest.mark.integration
    @pytest.mark.smoke
    @responses.activate
    def test_get_topology_returns_dict(self, odl: OpenDaylightController) -> None:
        """GET topology should return parsed JSON."""
        responses.add(
            responses.GET,
            "http://127.0.0.1:8181/restconf/operational/network-topology:network-topology",
            json={
                "network-topology": {
                    "topology": [
                        {
                            "topology-id": "flow:1",
                            "node": [{"node-id": "openflow:1"}],
                            "link": [],
                        }
                    ]
                }
            },
            status=200,
        )
        topo = odl.get_topology()
        assert "network-topology" in topo
        assert len(topo["network-topology"]["topology"]) >= 1

    @pytest.mark.integration
    @responses.activate
    def test_get_nodes_returns_list(self, odl: OpenDaylightController) -> None:
        responses.add(
            responses.GET,
            "http://127.0.0.1:8181/restconf/operational/opendaylight-inventory:nodes",
            json={
                "nodes": {
                    "node": [
                        {"id": "openflow:1", "manufacturer": "Nicira"},
                        {"id": "openflow:2", "manufacturer": "Nicira"},
                    ]
                }
            },
            status=200,
        )
        nodes = odl.get_nodes()
        assert len(nodes) == 2


class TestODLFlows:
    @pytest.mark.integration
    @responses.activate
    def test_get_flows_for_node(self, odl: OpenDaylightController) -> None:
        responses.add(
            responses.GET,
            "http://127.0.0.1:8181/restconf/operational/opendaylight-inventory:nodes/node/openflow:1/table/0",
            json={
                "flow-node-inventory:table": [
                    {
                        "id": 0,
                        "flow": [
                            {"id": "flow-1", "priority": 100},
                            {"id": "flow-2", "priority": 200},
                        ],
                    }
                ]
            },
            status=200,
        )
        flows = odl.get_flows("openflow:1")
        assert len(flows) == 2
        assert flows[0]["id"] == "flow-1"

    @pytest.mark.integration
    @responses.activate
    def test_push_flow(self, odl: OpenDaylightController, sample_flow: dict[str, Any]) -> None:
        flow_id = sample_flow["id"]
        responses.add(
            responses.PUT,
            f"http://127.0.0.1:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/{flow_id}",
            status=200,
        )
        # Should not raise
        odl.push_flow("openflow:1", sample_flow)

    @pytest.mark.integration
    @responses.activate
    def test_delete_flow(self, odl: OpenDaylightController) -> None:
        responses.add(
            responses.DELETE,
            "http://127.0.0.1:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/flow-1",
            status=200,
        )
        odl.delete_flow("openflow:1", "flow-1")


class TestODLHealthCheck:
    @pytest.mark.integration
    @pytest.mark.smoke
    @responses.activate
    def test_health_check_success(self, odl: OpenDaylightController) -> None:
        responses.add(responses.GET, "http://127.0.0.1:8181/", status=200)
        assert odl.health_check() is True

    @pytest.mark.integration
    @responses.activate
    def test_health_check_failure(self, odl: OpenDaylightController) -> None:
        responses.add(responses.GET, "http://127.0.0.1:8181/", body=ConnectionError())
        assert odl.health_check() is False
