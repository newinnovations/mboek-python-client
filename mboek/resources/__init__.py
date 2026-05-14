"""Resource package exports.

Resources fall into two groups:

* **Top-level resources** — accessed directly via ``MboekClient``:
  ``auth`` (``AuthResource``), ``administraties``, ``boekingen``,
  ``export_import`` (``ExportImportResource``), ``jaarrekening``, and
  ``maintenance``.
  These are not scoped to a single administratie.

* **Admin-scoped resources** — accessed via
  ``MboekClient.administratie(id)`` (an
  :py:class:`~mboek.resources._admin_scope.AdministratieScope`):
  ``boekjaren``, ``dagboeken``, ``grootboekrekeningen``, ``btw_codes``,
  ``auto_booking_rules``, ``import_``, and the admin-level
  ``export_import`` (``AdminExportImportResource``).

``AuthResource`` is intentionally excluded from this public export list
because it is only used internally by :py:class:`~mboek._client.MboekClient`.
"""

from mboek.resources.administraties import AdministratiesResource
from mboek.resources.auto_booking_rules import AutoBookingRulesResource
from mboek.resources.boekingen import BoekingenResource
from mboek.resources.boekjaren import BoekjarenResource
from mboek.resources.btw_aangifte import BtwAangifteResource
from mboek.resources.btw_codes import BtwCodesResource
from mboek.resources.dagboeken import DagboekenResource
from mboek.resources.export_import import ExportImportResource
from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource
from mboek.resources.import_ import ImportResource
from mboek.resources.jaarrekening import JaarrekeningResource
from mboek.resources.maintenance import MaintenanceResource
from mboek.resources.reports import ReportsResource

__all__ = [
    "AdministratiesResource",
    "AutoBookingRulesResource",
    "BoekingenResource",
    "BoekjarenResource",
    "BtwAangifteResource",
    "BtwCodesResource",
    "DagboekenResource",
    "ExportImportResource",
    "GrootboekrekeningenResource",
    "ImportResource",
    "JaarrekeningResource",
    "MaintenanceResource",
    "ReportsResource",
]
