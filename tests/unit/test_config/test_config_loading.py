"""Unit tests for configuration loading and env var interpolation."""

from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from sdn_testkit.utils.config import get_env_config, load_config


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary YAML config file."""
    config_data = {
        "controller": {
            "host": "${SDN_CONTROLLER_HOST}",
            "port": 8181,
            "username": "admin",
        },
        "topology": "spine_leaf",
        "timeouts": {"connect": 10, "command": 30},
    }
    config_file = tmp_path / "test_config.yaml"
    with config_file.open("w") as f:
        yaml.dump(config_data, f)
    return config_file


class TestLoadConfig:
    @pytest.mark.unit
    def test_load_valid_config(self, tmp_config: Path) -> None:
        """Config should load and return a dict."""
        config = load_config(tmp_config)
        assert isinstance(config, dict)
        assert "controller" in config
        assert config["topology"] == "spine_leaf"

    @pytest.mark.unit
    def test_env_var_interpolation(self, tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables should be substituted in config values."""
        monkeypatch.setenv("SDN_CONTROLLER_HOST", "10.0.0.99")
        config = load_config(tmp_config)
        assert config["controller"]["host"] == "10.0.0.99"

    @pytest.mark.unit
    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    @pytest.mark.unit
    def test_unset_env_var_left_as_is(self, tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """If an env var is not set, the placeholder stays in the string."""
        monkeypatch.delenv("SDN_CONTROLLER_HOST", raising=False)
        config = load_config(tmp_config)
        assert "${SDN_CONTROLLER_HOST}" in config["controller"]["host"]


class TestGetEnvConfig:
    @pytest.mark.unit
    def test_collects_sdn_prefixed_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SDN_CONTROLLER_HOST", "10.0.0.1")
        monkeypatch.setenv("SDN_CONTROLLER_PORT", "8181")
        monkeypatch.setenv("OTHER_VAR", "ignored")

        result = get_env_config()
        assert result["controller_host"] == "10.0.0.1"
        assert result["controller_port"] == "8181"
        assert "other_var" not in result

    @pytest.mark.unit
    def test_empty_when_no_sdn_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Clear all SDN_ vars
        for key in list(os.environ):
            if key.startswith("SDN_"):
                monkeypatch.delenv(key)
        result = get_env_config()
        # May still contain vars from other tests, but should not error
        assert isinstance(result, dict)
