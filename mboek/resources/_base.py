"""Base resource class with shared HTTP helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mboek._client import MboekClient


class BaseResource:
    """Base class for all resource managers.

    Subclasses use the ``_get``, ``_post``, ``_patch``, and ``_delete``
    helpers which handle authentication headers and error raising automatically.
    """

    def __init__(self, client: "MboekClient") -> None:
        self._client = client

    # ── HTTP helpers ─────────────────────────────────────────────────────────

    def _get(self, path: str, *, params: dict | None = None) -> Any:
        return self._client._request("GET", path, params=params)

    def _post(self, path: str, *, json: Any = None, params: dict | None = None) -> Any:
        return self._client._request("POST", path, json=json, params=params)

    def _patch(self, path: str, *, json: Any = None) -> Any:
        return self._client._request("PATCH", path, json=json)

    def _delete(self, path: str) -> None:
        self._client._request("DELETE", path)

    def _post_multipart(self, path: str, *, files: dict, data: dict | None = None) -> Any:
        return self._client._request("POST", path, files=files, data=data)
