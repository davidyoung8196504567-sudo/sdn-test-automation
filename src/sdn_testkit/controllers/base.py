"""Base SDN controller abstraction."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class ControllerConfig:
    """Connection parameters for an SDN controller."""

    host: str
    port: int = 8181
    username: str = "admin"
    password: str = "admin"
    scheme: str = "http"
    verify_ssl: bool = False
    timeout: int = 30

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


class BaseController(ABC):
    """Abstract base for all SDN controller clients.

    Subclass this to add controller-specific API paths and data models.
    """

    def __init__(self, config: ControllerConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._session.auth = (config.username, config.password)
        self._session.verify = config.verify_ssl
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # -- HTTP helpers ----------------------------------------------------------

    def _get(self, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        logger.debug("GET %s", url)
        resp = self._session.get(url, timeout=self.config.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def _post(self, path: str, json_data: Any = None, **kwargs: Any) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        logger.debug("POST %s", url)
        resp = self._session.post(url, json=json_data, timeout=self.config.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def _put(self, path: str, json_data: Any = None, **kwargs: Any) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        logger.debug("PUT %s", url)
        resp = self._session.put(url, json=json_data, timeout=self.config.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def _delete(self, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        logger.debug("DELETE %s", url)
        resp = self._session.delete(url, timeout=self.config.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    # -- Abstract interface ----------------------------------------------------

    @abstractmethod
    def get_topology(self) -> dict[str, Any]:
        """Return the current network topology from the controller."""

    @abstractmethod
    def get_flows(self, node_id: str) -> list[dict[str, Any]]:
        """Return flow entries for a given network node."""

    @abstractmethod
    def push_flow(self, node_id: str, flow: dict[str, Any]) -> None:
        """Install a flow entry on a network node."""

    @abstractmethod
    def delete_flow(self, node_id: str, flow_id: str) -> None:
        """Remove a flow entry from a network node."""

    @abstractmethod
    def get_nodes(self) -> list[dict[str, Any]]:
        """List all managed network nodes."""

    @abstractmethod
    def get_node_status(self, node_id: str) -> dict[str, Any]:
        """Return operational status for a specific node."""

    # -- Convenience -----------------------------------------------------------

    def health_check(self) -> bool:
        """Return True if the controller API is reachable."""
        try:
            self._get("/")
            return True
        except (requests.RequestException, ConnectionError):
            return False

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> "BaseController":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
