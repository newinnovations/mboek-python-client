"""Base resource class with shared HTTP helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from mboek._client import MboekClient

T = TypeVar("T")
MAX_PAGE_SIZE = 1000


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

    def _post(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self._client._request(
            "POST", path, json=json, params=params, data=data, headers=headers
        )

    def _patch(self, path: str, *, json: Any = None) -> Any:
        return self._client._request("PATCH", path, json=json)

    def _delete(self, path: str) -> None:
        self._client._request("DELETE", path)

    def _post_multipart(self, path: str, *, files: dict, data: Any = None) -> Any:
        return self._client._request("POST", path, files=files, data=data)

    @staticmethod
    def _slice_items(
        items: list[T], *, limit: int | None = None, offset: int | None = None
    ) -> list[T]:
        """Return a client-side slice after validating ``limit`` and ``offset``."""
        if limit is not None and limit < 0:
            raise ValueError("limit must be >= 0")
        if offset is not None and offset < 0:
            raise ValueError("offset must be >= 0")

        start = offset or 0
        if limit is None:
            return items[start:]
        return items[start : start + limit]

    def _get_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        page_size: int = MAX_PAGE_SIZE,
    ) -> list[Any]:
        """Fetch a paginated list endpoint until the requested slice is complete.

        When ``limit`` is omitted, all remaining pages are fetched starting at
        ``offset``. When ``limit`` is provided, the method keeps requesting
        pages until the requested number of items has been collected.
        """
        if page_size <= 0:
            raise ValueError("page_size must be > 0")
        if limit is not None and limit < 0:
            raise ValueError("limit must be >= 0")
        if offset is not None and offset < 0:
            raise ValueError("offset must be >= 0")
        if limit == 0:
            return []

        base_params = {
            key: value for key, value in (params or {}).items() if value is not None
        }
        next_offset = offset or 0
        remaining = limit
        items: list[Any] = []

        while True:
            chunk_limit = page_size if remaining is None else min(remaining, page_size)
            page_params = dict(base_params)
            page_params["limit"] = chunk_limit
            page_params["offset"] = next_offset

            page = self._get(path, params=page_params)
            if not isinstance(page, list):
                raise TypeError("Expected paginated endpoint to return a list")

            items.extend(page)
            received = len(page)

            if remaining is not None:
                remaining -= received
                if remaining <= 0:
                    break

            if received < chunk_limit:
                break

            next_offset += received

        return items

    @staticmethod
    def _require_single_match(
        matches: list[T],
        *,
        not_found_message: str,
        multiple_message: str,
    ) -> T:
        from mboek._exceptions import NotFoundError

        if not matches:
            raise NotFoundError(not_found_message)
        if len(matches) > 1:
            raise ValueError(multiple_message)
        return matches[0]

    # ── Grootboekrekening resolution helper ──────────────────────────────────

    def _resolve_rekening_id(
        self,
        admin_id: int,
        *,
        naam: str | None = None,
        code: str | None = None,
    ) -> int:
        """Resolve a grootboekrekening naam or code to its numeric ID.

        Uses the client-level cache, so repeated calls within the same session
        do not result in additional HTTP requests.

        Args:
            admin_id: Administratie ID to search within.
            naam: Exact account name (case-sensitive).
            code: Account code (e.g. ``"1220"``).

        Returns:
            The ``id`` of the matching grootboekrekening.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: No account matched.
            :py:exc:`ValueError`: Neither ``naam`` nor ``code`` was provided.
        """
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        gbr = GrootboekrekeningenResource(self._client, admin_id)
        if naam is not None:
            return gbr._require_single_match(
                gbr.list(name=naam),
                not_found_message=f"Grootboekrekening met naam '{naam}' niet gevonden",
                multiple_message=f"Meerdere grootboekrekeningen met naam '{naam}' gevonden",
            ).id
        if code is not None:
            return gbr._require_single_match(
                gbr.list(code=code),
                not_found_message=f"Grootboekrekening met code '{code}' niet gevonden",
                multiple_message=f"Meerdere grootboekrekeningen met code '{code}' gevonden",
            ).id
        raise ValueError("Provide naam or code")
