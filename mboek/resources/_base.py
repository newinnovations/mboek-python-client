"""Base resource class with shared HTTP helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from mboek._client import MboekClient

T = TypeVar("T")


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

    def _post_multipart(
        self, path: str, *, files: dict, data: dict | None = None
    ) -> Any:
        return self._client._request("POST", path, files=files, data=data)

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
