"""Pydantic models for network topologies.

Topologies are defined in YAML and validated here before use in tests.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NodeRole(str, Enum):
    SPINE = "spine"
    LEAF = "leaf"
    BORDER = "border"
    HOST = "host"
    CONTROLLER = "controller"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"


class Node(BaseModel):
    """A network device or host in the topology."""

    name: str
    role: NodeRole
    mgmt_ip: str = ""
    device_type: str = "linux"
    interfaces: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Link(BaseModel):
    """A connection between two nodes."""

    src_node: str
    src_interface: str
    dst_node: str
    dst_interface: str
    bandwidth: str = "1G"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Segment(BaseModel):
    """A network segment / VLAN / VRF grouping."""

    name: str
    vlan_id: int | None = None
    vrf: str = ""
    nodes: list[str] = Field(default_factory=list)
    description: str = ""


class Topology(BaseModel):
    """Complete topology definition for a test bundle."""

    name: str
    description: str = ""
    nodes: list[Node]
    links: list[Link]
    segments: list[Segment] = Field(default_factory=list)
    controller: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_links_reference_known_nodes(self) -> "Topology":
        node_names = {n.name for n in self.nodes}
        for link in self.links:
            if link.src_node not in node_names:
                raise ValueError(
                    f"Link source '{link.src_node}' not found in topology nodes"
                )
            if link.dst_node not in node_names:
                raise ValueError(
                    f"Link destination '{link.dst_node}' not found in topology nodes"
                )
        return self

    @model_validator(mode="after")
    def validate_segments_reference_known_nodes(self) -> "Topology":
        node_names = {n.name for n in self.nodes}
        for seg in self.segments:
            for node_name in seg.nodes:
                if node_name not in node_names:
                    raise ValueError(
                        f"Segment '{seg.name}' references unknown node '{node_name}'"
                    )
        return self

    def get_nodes_by_role(self, role: NodeRole) -> list[Node]:
        return [n for n in self.nodes if n.role == role]

    def get_links_for_node(self, node_name: str) -> list[Link]:
        return [
            lnk
            for lnk in self.links
            if lnk.src_node == node_name or lnk.dst_node == node_name
        ]

    def get_segment_for_node(self, node_name: str) -> Segment | None:
        for seg in self.segments:
            if node_name in seg.nodes:
                return seg
        return None
