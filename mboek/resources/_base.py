"""Base resource class with shared HTTP helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from mboek._unset import UNSET, UnsetType

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.auto_booking_rules import NewAutoBookingRuleLine
    from mboek.models.boekingen import NewBoekingsregel

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
    def _set_patch_value(data: dict[str, Any], key: str, value: Any) -> None:
        if value is not UNSET:
            data[key] = value

    @staticmethod
    def _set_patch_date(
        data: dict[str, Any], key: str, value: date | None | UnsetType
    ) -> None:
        if isinstance(value, UnsetType):
            return
        if value is None:
            data[key] = None
            return
        data[key] = value.isoformat()

    @staticmethod
    def _set_patch_decimal(
        data: dict[str, Any], key: str, value: Decimal | None | UnsetType
    ) -> None:
        if value is not UNSET:
            data[key] = None if value is None else str(value)

    @staticmethod
    def _set_patch_enum(
        data: dict[str, Any], key: str, value: Enum | None | UnsetType
    ) -> None:
        if isinstance(value, UnsetType):
            return
        if value is None:
            data[key] = None
            return
        data[key] = value.value

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
        code: int | None = None,
    ) -> int:
        """Resolve a grootboekrekening naam or code to its numeric ID.

        Uses the client-level cache, so repeated calls within the same session
        do not result in additional HTTP requests.

        Args:
            admin_id: Administratie ID to search within.
            naam: Exact account name (case-sensitive).
            code: Account code (e.g. ``1220``).

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
                not_found_message=f"Grootboekrekening named '{naam}' not found",
                multiple_message=f"Multiple grootboekrekeningen named '{naam}' found",
            ).id
        if code is not None:
            return gbr._require_single_match(
                gbr.list(code=code),
                not_found_message=f"Grootboekrekening with code '{code}' not found",
                multiple_message=f"Multiple grootboekrekeningen with code '{code}' found",
            ).id
        raise ValueError("Provide naam or code")

    def _resolve_rekening_reference(
        self,
        admin_id: int,
        *,
        id_value: int | None = None,
        name_value: str | None = None,
        code_value: int | None = None,
        field_prefix: str = "grootboekrekening",
    ) -> int | None:
        provided = sum(x is not None for x in [id_value, name_value, code_value])
        if provided > 1:
            raise ValueError(
                f"Provide only one of: {field_prefix}_id, {field_prefix}_naam, {field_prefix}_code"
            )
        if id_value is None and (name_value is not None or code_value is not None):
            return self._resolve_rekening_id(
                admin_id,
                naam=name_value,
                code=code_value,
            )
        return id_value

    def _resolve_rekening_reference_patch(
        self,
        admin_id: int,
        *,
        id_value: int | None | UnsetType = UNSET,
        name_value: str | None | UnsetType = UNSET,
        code_value: int | None | UnsetType = UNSET,
        field_prefix: str = "grootboekrekening",
    ) -> int | None | UnsetType:
        provided = int(id_value is not UNSET)
        provided += int(name_value is not UNSET and name_value is not None)
        provided += int(code_value is not UNSET and code_value is not None)
        if provided > 1:
            raise ValueError(
                f"Provide only one of: {field_prefix}_id, {field_prefix}_naam, {field_prefix}_code"
            )
        if id_value is not UNSET:
            return id_value
        if isinstance(name_value, str):
            return self._resolve_rekening_id(admin_id, naam=name_value)
        if isinstance(code_value, int) and not isinstance(code_value, bool):
            return self._resolve_rekening_id(admin_id, code=code_value)
        return UNSET

    def _serialize_boekingsregel(
        self, admin_id: int, regel: "NewBoekingsregel"
    ) -> dict[str, Any]:
        resolved_id = self._resolve_rekening_reference(
            admin_id,
            id_value=regel.grootboekrekening_id,
            name_value=regel.grootboekrekening_naam,
            code_value=regel.grootboekrekening_code,
        )
        if resolved_id is None:
            raise AssertionError(
                "NewBoekingsregel must resolve to a grootboekrekening_id"
            )
        return regel.to_dict(grootboekrekening_id=resolved_id)

    def _serialize_boekingsregels(
        self, admin_id: int, regels: list["NewBoekingsregel"]
    ) -> list[dict[str, Any]]:
        return [self._serialize_boekingsregel(admin_id, regel) for regel in regels]

    def _serialize_auto_booking_rule_line(
        self, admin_id: int, line: "NewAutoBookingRuleLine"
    ) -> dict[str, Any]:
        resolved_id = self._resolve_rekening_reference(
            admin_id,
            id_value=line.tegenrekening_id,
            name_value=line.tegenrekening_naam,
            code_value=line.tegenrekening_code,
            field_prefix="tegenrekening",
        )
        if resolved_id is None:
            raise AssertionError(
                "NewAutoBookingRuleLine must resolve to a tegenrekening_id"
            )
        return line.to_dict(tegenrekening_id=resolved_id)

    def _serialize_auto_booking_rule_lines(
        self, admin_id: int, lines: list["NewAutoBookingRuleLine"]
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_auto_booking_rule_line(admin_id, line) for line in lines
        ]
