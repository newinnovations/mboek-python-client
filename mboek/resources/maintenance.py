"""Maintenance resource."""

from __future__ import annotations

from mboek._parsers import parse_vacuum_result
from mboek.models.maintenance import VacuumResult
from mboek.resources._base import BaseResource


class MaintenanceResource(BaseResource):
    """Database maintenance operations.

    Access via :py:attr:`MboekClient.maintenance`.
    """

    def vacuum(self) -> VacuumResult:
        """Run a database VACUUM to reclaim disk space.

        For SQLite this runs ``VACUUM``; for PostgreSQL it runs ``VACUUM ANALYZE``.

        Returns:
            :py:class:`~mboek.models.maintenance.VacuumResult`.
        """
        return parse_vacuum_result(self._post("/api/vacuum"))
