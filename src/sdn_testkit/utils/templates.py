"""Jinja2 template rendering for flow rules and ACLs.

Templates live in the ``templates/`` directory and can be overridden
by placing custom templates in the topology bundle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"


def _get_env(template_dir: str | Path | None = None) -> Environment:
    search_path = str(template_dir) if template_dir else str(TEMPLATES_DIR)
    return Environment(
        loader=FileSystemLoader(search_path),
        autoescape=select_autoescape(default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_flow_template(
    template_name: str = "flow_rule.json.j2",
    variables: dict[str, Any] | None = None,
    template_dir: str | Path | None = None,
) -> str:
    """Render a flow-rule JSON template.

    Args:
        template_name: Template file name.
        variables: Context variables for Jinja2 rendering.
        template_dir: Override the default templates directory.

    Returns:
        Rendered template string.
    """
    env = _get_env(template_dir)
    tmpl = env.get_template(template_name)
    return tmpl.render(**(variables or {}))


def render_acl_template(
    template_name: str = "acl_entry.json.j2",
    variables: dict[str, Any] | None = None,
    template_dir: str | Path | None = None,
) -> str:
    """Render an ACL entry template."""
    env = _get_env(template_dir)
    tmpl = env.get_template(template_name)
    return tmpl.render(**(variables or {}))
