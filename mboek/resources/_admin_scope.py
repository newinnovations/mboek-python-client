"""AdministratieScope — scoped access to all resources of a single administratie."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mboek._exceptions import NotFoundError

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.resources._boekjaar_scope import BoekjaarScope
    from mboek.resources._dagboek_scope import DagboekScope


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

    def boekjaar(
        self, boekjaar_id: int | None = None, *, name: str | None = None
    ) -> "BoekjaarScope":
        """Return a :py:class:`~mboek.resources._boekjaar_scope.BoekjaarScope`.

        Pass either the numeric ``boekjaar_id`` (no HTTP call) or a ``name``
        to look up the boekjaar by exact name (one HTTP call)::

            bj = admin.boekjaar(10)
            bj = admin.boekjaar(name="2024")

        Args:
            boekjaar_id: Boekjaar ID. No HTTP call is made.
            name: Exact boekjaar name, e.g. ``"2024"`` (case-sensitive).
                Performs a
                :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.list`
                lookup request.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` given but
                no matching boekjaar found.
            :py:exc:`ValueError`: Neither or both of ``boekjaar_id`` and
                ``name`` provided.
        """
        provided = sum(x is not None for x in [boekjaar_id, name])
        if provided != 1:
            raise ValueError("Provide exactly one of: boekjaar_id, name")
        if name is not None:
            found = self.boekjaren.find_by_naam(name)
            if found is None:
                raise NotFoundError(f"Boekjaar '{name}' not found")
            boekjaar_id = found.id
        from mboek.resources._boekjaar_scope import BoekjaarScope

        return BoekjaarScope(self._client, self.admin_id, boekjaar_id)

    # ── Dagboek scope (year-agnostic operations) ──────────────────────────────

    def dagboek(
        self,
        dagboek_id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
    ) -> "DagboekScope":
        """Return a :py:class:`~mboek.resources._dagboek_scope.DagboekScope`.

        Pass the numeric ``dagboek_id`` (no HTTP call), a ``name``, or a
        ``code`` to look up by exact name or short code (one HTTP call each)::

            dagboek = admin.dagboek(20)
            dagboek = admin.dagboek(name="Bankboek")
            dagboek = admin.dagboek(code="BANK")

        Args:
            dagboek_id: Dagboek ID. No HTTP call is made.
            name: Exact dagboek name (case-sensitive). Performs a
                :py:meth:`~mboek.resources.dagboeken.DagboekenResource.list`
                lookup request.
            code: Dagboek short code (case-insensitive). Performs a
                :py:meth:`~mboek.resources.dagboeken.DagboekenResource.list`
                lookup request.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` or ``code``
                given but no matching dagboek found.
            :py:exc:`ValueError`: None or more than one of the arguments
                provided.
        """
        provided = sum(x is not None for x in [dagboek_id, name, code])
        if provided != 1:
            raise ValueError("Provide exactly one of: dagboek_id, name, code")
        if name is not None:
            found = self.dagboeken.find_by_naam(name)
            if found is None:
                raise NotFoundError(f"Dagboek '{name}' not found")
            dagboek_id = found.id
        elif code is not None:
            found = self.dagboeken.find_by_code(code)
            if found is None:
                raise NotFoundError(f"Dagboek with code '{code}' not found")
            dagboek_id = found.id
        from mboek.resources._dagboek_scope import DagboekScope

        return DagboekScope(self._client, self.admin_id, dagboek_id)
