"""OpenDaylight (ODL) controller client."""

from __future__ import annotations

import logging
from typing import Any

from sdn_testkit.controllers.base import BaseController

logger = logging.getLogger(__name__)

# ODL RESTCONF paths (RFC 8040)
_TOPO_PATH = "/restconf/operational/network-topology:network-topology"
_NODES_PATH = "/restconf/operational/opendaylight-inventory:nodes"
_FLOW_PATH = (
    "/restconf/config/opendaylight-inventory:nodes"
    "/node/{node_id}/table/{table_id}/flow/{flow_id}"
)


class OpenDaylightController(BaseController):
    """Client for the OpenDaylight RESTCONF API."""

    def get_topology(self) -> dict[str, Any]:
        resp = self._get(_TOPO_PATH)
        return resp.json()

    def get_flows(self, node_id: str, table_id: int = 0) -> list[dict[str, Any]]:
        path = f"/restconf/operational/opendaylight-inventory:nodes/node/{node_id}/table/{table_id}"
        resp = self._get(path)
        data = resp.json()
        table = data.get("flow-node-inventory:table", [{}])[0]
        return table.get("flow", [])

    def push_flow(self, node_id: str, flow: dict[str, Any]) -> None:
        table_id = flow.get("table_id", 0)
        flow_id = flow["id"]
        path = _FLOW_PATH.format(node_id=node_id, table_id=table_id, flow_id=flow_id)
        self._put(path, json_data=flow)
        logger.info("Pushed flow %s to node %s table %s", flow_id, node_id, table_id)

    def delete_flow(self, node_id: str, flow_id: str, table_id: int = 0) -> None:
        path = _FLOW_PATH.format(node_id=node_id, table_id=table_id, flow_id=flow_id)
        self._delete(path)
        logger.info("Deleted flow %s from node %s", flow_id, node_id)

    def get_nodes(self) -> list[dict[str, Any]]:
        resp = self._get(_NODES_PATH)
        data = resp.json()
        return data.get("nodes", {}).get("node", [])

    def get_node_status(self, node_id: str) -> dict[str, Any]:
        path = f"/restconf/operational/opendaylight-inventory:nodes/node/{node_id}"
        resp = self._get(path)
        return resp.json()
