"""Resource package exports."""

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
    "MaintenanceResource",
    "ReportsResource",
]
