"""Model types for the mBoek API client."""

from mboek.models._enums import (
    AutoBookingActieType,
    AutoBookingBedragType,
    BoekingStatus,
    BoekjaarStatus,
    BtwAangifteStatus,
    BtwSoort,
    DagboekType,
    ImportFormaat,
    Regeltype,
    RekeningCategorie,
    RekeningType,
)
from mboek.models.administraties import Administratie
from mboek.models.auth import AuthToken
from mboek.models.auto_booking_rules import (
    AutoBookingRule,
    AutoBookingRuleLine,
    NewAutoBookingRuleLine,
)
from mboek.models.boekingen import Boeking, Boekingsregel, NewBoekingsregel
from mboek.models.boekjaren import Boekjaar
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCode
from mboek.models.dagboeken import Dagboek, DagboekWerkStatus
from mboek.models.export_import import ImportResult, MatchSuggestion
from mboek.models.grootboekrekeningen import GrootboekMutatie, Grootboekrekening
from mboek.models.reports import (
    BalansRegel,
    BalansReport,
    WinstVerliesRegel,
    WinstVerliesReport,
)

__all__ = [
    # enums
    "AutoBookingActieType",
    "AutoBookingBedragType",
    "BoekingStatus",
    "BoekjaarStatus",
    "BtwAangifteStatus",
    "BtwSoort",
    "DagboekType",
    "ImportFormaat",
    "RekeningCategorie",
    "RekeningType",
    "Regeltype",
    # auth
    "AuthToken",
    # administraties
    "Administratie",
    # boekjaren
    "Boekjaar",
    # dagboeken
    "Dagboek",
    "DagboekWerkStatus",
    # grootboekrekeningen
    "GrootboekMutatie",
    "Grootboekrekening",
    # boekingen
    "Boeking",
    "Boekingsregel",
    "NewBoekingsregel",
    # btw codes
    "BtwCode",
    # btw aangifte
    "BtwAangifte",
    "BtwBerekening",
    "RubriekBedragen",
    # auto booking rules
    "AutoBookingRule",
    "AutoBookingRuleLine",
    "NewAutoBookingRuleLine",
    # reports
    "BalansRegel",
    "BalansReport",
    "WinstVerliesRegel",
    "WinstVerliesReport",
    # import / export
    "ImportResult",
    "MatchSuggestion",
]
