"""Maintenance resource."""

from __future__ import annotations

from mboek.resources._base import BaseResource


class MaintenanceResource(BaseResource):
    """Database maintenance operations.

    Access via :py:attr:`MboekClient.maintenance`.
    """

    def vacuum(self) -> dict:
        """Run a database VACUUM to reclaim disk space.

        For SQLite this runs ``VACUUM``; for PostgreSQL it runs ``VACUUM ANALYZE``.

        Returns:
            A dict with ``message`` and ``elapsed_ms`` fields.
        """
        return self._post("/api/vacuum")
