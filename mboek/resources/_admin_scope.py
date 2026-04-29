"""AdministratieScope — scoped access to all resources of a single administratie."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekjaren import Boekjaar
    from mboek.models.dagboeken import Dagboek


class AdministratieScope:
    """A lightweight scope object that binds all child resources to one administratie.

    Obtain via :py:meth:`~mboek._client.MboekClient.administratie`::

        admin = client.administratie(1)
        boekjaren = admin.boekjaren.list()
        boekjaar = admin.boekjaar(10)
        dagboek = admin.dagboek(20)

    No HTTP call is made when creating this object.
    """

    def __init__(self, client: "MboekClient", admin_id: int) -> None:
        self._client = client
        self.admin_id = admin_id

        # Lazily-initialised child resources
        self._boekjaren = None
        self._dagboeken = None
        self._grootboekrekeningen = None
        self._btw_codes = None
        self._auto_booking_rules = None
        self._import_ = None
        self._export_import = None

    # ── Child resources ───────────────────────────────────────────────────────

    @property
    def boekjaren(self):
        """Boekjaren resource (:py:class:`~mboek.resources.boekjaren.BoekjarenResource`)."""
        if self._boekjaren is None:
            from mboek.resources.boekjaren import BoekjarenResource

            self._boekjaren = BoekjarenResource(self._client, self.admin_id)
        return self._boekjaren

    @property
    def dagboeken(self):
        """Dagboeken resource (:py:class:`~mboek.resources.dagboeken.DagboekenResource`)."""
        if self._dagboeken is None:
            from mboek.resources.dagboeken import DagboekenResource

            self._dagboeken = DagboekenResource(self._client, self.admin_id)
        return self._dagboeken

    @property
    def grootboekrekeningen(self):
        """Grootboekrekeningen resource (:py:class:`~mboek.resources.grootboekrekeningen.GrootboekrekeningenResource`)."""
        if self._grootboekrekeningen is None:
            from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

            self._grootboekrekeningen = GrootboekrekeningenResource(
                self._client, self.admin_id
            )
        return self._grootboekrekeningen

    @property
    def btw_codes(self):
        """BTW codes resource (:py:class:`~mboek.resources.btw_codes.BtwCodesResource`)."""
        if self._btw_codes is None:
            from mboek.resources.btw_codes import BtwCodesResource

            self._btw_codes = BtwCodesResource(self._client, self.admin_id)
        return self._btw_codes

    @property
    def auto_booking_rules(self):
        """Auto booking rules resource (:py:class:`~mboek.resources.auto_booking_rules.AutoBookingRulesResource`)."""
        if self._auto_booking_rules is None:
            from mboek.resources.auto_booking_rules import AutoBookingRulesResource

            self._auto_booking_rules = AutoBookingRulesResource(
                self._client, self.admin_id
            )
        return self._auto_booking_rules

    @property
    def import_(self):
        """Bank import resource (:py:class:`~mboek.resources.import_.ImportResource`)."""
        if self._import_ is None:
            from mboek.resources.import_ import ImportResource

            self._import_ = ImportResource(self._client, self.admin_id)
        return self._import_

    @property
    def export_import(self):
        """Export/import resource (:py:class:`~mboek.resources.export_import.AdminExportImportResource`)."""
        if self._export_import is None:
            from mboek.resources.export_import import AdminExportImportResource

            self._export_import = AdminExportImportResource(self._client, self.admin_id)
        return self._export_import

    # ── Boekjaar scope ────────────────────────────────────────────────────────

    def boekjaar(self, id: int | None = None, *, name: str | None = None) -> "Boekjaar":
        """Return a :py:class:`~mboek.models.boekjaren.Boekjaar` for this administratie.

        Pass either the numeric ``id`` (one HTTP call to fetch data)
        or a ``name`` to look up the boekjaar by exact name (one HTTP call)::

            bj = admin.boekjaar(10)
            bj = admin.boekjaar(name="2024")

        The returned :py:class:`~mboek.models.boekjaren.Boekjaar` is
        fully-populated and carries a client reference, so scope-specific
        methods (``reports``, ``btw_aangifte``, ``dagboek()``, etc.) work
        directly on it.

        Args:
            id: Boekjaar ID. Makes one GET request to fetch data.
            name: Exact boekjaar name, e.g. ``"2024"`` (case-sensitive).
                Performs a list lookup request.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` given but
                no matching boekjaar found.
            :py:exc:`ValueError`: Neither or both of ``id`` and
                ``name`` provided.
        """
        provided = sum(x is not None for x in [id, name])
        if provided != 1:
            raise ValueError("Provide exactly one of: id, name")
        if name is not None:
            found = self.boekjaren._require_single_match(
                self.boekjaren.list(name=name),
                not_found_message=f"Boekjaar '{name}' not found",
                multiple_message=f"Multiple boekjaren named '{name}' found",
            )
            return found
        if id is None:
            raise AssertionError("boekjaar() could not resolve a boekjaar ID")
        return self.boekjaren.get(id)

    # ── Dagboek scope ─────────────────────────────────────────────────────────

    def dagboek(
        self,
        id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
    ) -> "Dagboek":
        """Return a :py:class:`~mboek.models.dagboeken.Dagboek` for this administratie.

        Pass the numeric ``id`` (one HTTP call to fetch data), a
        ``name``, or a ``code`` to look up by exact name or short code::

            dagboek = admin.dagboek(20)
            dagboek = admin.dagboek(name="Bankboek")
            dagboek = admin.dagboek(code="BANK")

        The returned :py:class:`~mboek.models.dagboeken.Dagboek` is
        fully-populated (all data attributes available) and carries a client
        reference, so :py:meth:`~mboek.models.dagboeken.Dagboek.rerun_regels`,
        :py:meth:`~mboek.models.dagboeken.Dagboek.suggest`, and
        :py:meth:`~mboek.models.dagboeken.Dagboek.import_boekingen` work
        directly.  To access boekingen, add a boekjaar scope first::

            dagboek.with_boekjaar(name="2024").boekingen.list()

        .. note::
            Unlike the old ``DagboekScope``, this method always makes one HTTP
            call (even when ``id`` is provided) to ensure the returned
            object is fully populated.

        Args:
            id: Dagboek ID. Makes one GET request to fetch data.
            name: Exact dagboek name (case-sensitive). Performs a list lookup.
            code: Dagboek short code (case-insensitive). Performs a list lookup.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` or ``code``
                given but no matching dagboek found.
            :py:exc:`ValueError`: None or more than one of the arguments
                provided.
        """
        provided = sum(x is not None for x in [id, name, code])
        if provided != 1:
            raise ValueError("Provide exactly one of: id, name, code")
        if id is not None:
            return self.dagboeken.get(id)
        if name is not None:
            found = self.dagboeken._require_single_match(
                self.dagboeken.list(name=name),
                not_found_message=f"Dagboek '{name}' not found",
                multiple_message=f"Multiple dagboeken named '{name}' found",
            )
            return found
        if code is None:
            raise AssertionError("dagboek() could not resolve dagboek filters")
        return self.dagboeken._require_single_match(
            self.dagboeken.list(code=code),
            not_found_message=f"Dagboek with code '{code}' not found",
            multiple_message=f"Multiple dagboeken with code '{code}' found",
        )
