"""Unit tests for flow rule and ACL template rendering."""

from __future__ import annotations

import json

import pytest

from sdn_testkit.utils.templates import render_acl_template, render_flow_template


class TestFlowTemplateRendering:
    @pytest.mark.unit
    def test_basic_flow_rule(self) -> None:
        """Render a minimal flow rule and verify JSON structure."""
        result = render_flow_template(
            variables={
                "flow_id": "test-001",
                "table_id": 0,
                "priority": 200,
                "ipv4_dst": "10.0.0.0/24",
                "output_port": "2",
            }
        )
        data = json.loads(result)
        flow = data["flow"]
        assert flow["id"] == "test-001"
        assert flow["priority"] == 200
        assert flow["match"]["ipv4-destination"] == "10.0.0.0/24"

    @pytest.mark.unit
    def test_flow_rule_defaults(self) -> None:
        """Unspecified fields should use template defaults."""
        result = render_flow_template(
            variables={"flow_id": "default-test"}
        )
        data = json.loads(result)
        flow = data["flow"]
        assert flow["table_id"] == 0
        assert flow["priority"] == 100

    @pytest.mark.unit
    def test_flow_with_src_and_dst(self) -> None:
        result = render_flow_template(
            variables={
                "flow_id": "bidirectional-001",
                "ipv4_src": "10.1.0.0/16",
                "ipv4_dst": "10.2.0.0/16",
                "in_port": "1",
                "output_port": "3",
            }
        )
        data = json.loads(result)
        match = data["flow"]["match"]
        assert "ipv4-source" in match
        assert "ipv4-destination" in match
        assert match["in-port"] == "1"


class TestACLTemplateRendering:
    @pytest.mark.unit
    def test_basic_acl_entry(self) -> None:
        result = render_acl_template(
            variables={
                "rule_name": "allow-web",
                "sequence_id": 10,
                "src_ip": "10.0.0.0/8",
                "dst_ip": "0.0.0.0/0",
                "protocol": 6,
                "dst_port": 443,
                "action": "accept",
            }
        )
        data = json.loads(result)
        entry = data["acl-entry"]
        assert entry["rule-name"] == "allow-web"
        assert entry["matches"]["source-ipv4-network"] == "10.0.0.0/8"
        assert entry["actions"]["forwarding"] == "accept"

    @pytest.mark.unit
    def test_acl_deny_rule(self) -> None:
        result = render_acl_template(
            variables={
                "rule_name": "deny-all",
                "sequence_id": 999,
                "action": "drop",
            }
        )
        data = json.loads(result)
        assert data["acl-entry"]["actions"]["forwarding"] == "drop"
