"""ONOS controller client."""

from __future__ import annotations

import logging
from typing import Any

from sdn_testkit.controllers.base import BaseController

logger = logging.getLogger(__name__)

_API = "/onos/v1"


class ONOSController(BaseController):
    """Client for the ONOS REST API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # ONOS default port differs from ODL
        if self.config.port == 8181:
            self.config.port = 8181  # ONOS also uses 8181

    def get_topology(self) -> dict[str, Any]:
        resp = self._get(f"{_API}/topology")
        return resp.json()

    def get_flows(self, node_id: str) -> list[dict[str, Any]]:
        resp = self._get(f"{_API}/flows/{node_id}")
        return resp.json().get("flows", [])

    def push_flow(self, node_id: str, flow: dict[str, Any]) -> None:
        resp = self._post(f"{_API}/flows/{node_id}", json_data=flow)
        logger.info("Pushed flow to device %s (status %s)", node_id, resp.status_code)

    def delete_flow(self, node_id: str, flow_id: str) -> None:
        self._delete(f"{_API}/flows/{node_id}/{flow_id}")
        logger.info("Deleted flow %s from device %s", flow_id, node_id)

    def get_nodes(self) -> list[dict[str, Any]]:
        resp = self._get(f"{_API}/devices")
        return resp.json().get("devices", [])

    def get_node_status(self, node_id: str) -> dict[str, Any]:
        resp = self._get(f"{_API}/devices/{node_id}")
        return resp.json()

    def get_hosts(self) -> list[dict[str, Any]]:
        """ONOS-specific: list discovered hosts."""
        resp = self._get(f"{_API}/hosts")
        return resp.json().get("hosts", [])

    def get_links(self) -> list[dict[str, Any]]:
        """ONOS-specific: list discovered links."""
        resp = self._get(f"{_API}/links")
        return resp.json().get("links", [])

    def get_intents(self) -> list[dict[str, Any]]:
        """ONOS-specific: list installed intents."""
        resp = self._get(f"{_API}/intents")
        return resp.json().get("intents", [])
