"""Model types for the mBoek API client."""

from mboek.models._enums import (
    AutoBookingActieType,
    AutoBookingBedragType,
    BoekingStatus,
    BoekjaarStatus,
    BtwSoort,
    DagboekType,
    ImportFormaat,
    Regeltype,
    RekeningCategorie,
    RekeningType,
)
from mboek.models.administraties import AdministratieResponse
from mboek.models.auth import LoginResponse
from mboek.models.auto_booking_rules import (
    AutoBookingRuleLineResponse,
    AutoBookingRuleResponse,
    NewAutoBookingRuleLine,
)
from mboek.models.boekingen import (
    BoekingMetRegelsResponse,
    BoekingResponse,
    BoekingsregelResponse,
    NewBoekingsregel,
)
from mboek.models.boekjaren import (
    Boekjaar,
    BoekjaarResponse,
)
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCodeResponse
from mboek.models.dagboeken import (
    Dagboek,
    DagboekResponse,
    DagboekWerkStatus,
)
from mboek.models.export_import import ImportResult, MatchSuggestion
from mboek.models.grootboekrekeningen import (
    GrootboekMutatie,
    Grootboekrekening,
    GrootboekrekeningMetSaldoResponse,
    GrootboekrekeningResponse,
)
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
    "BtwSoort",
    "DagboekType",
    "ImportFormaat",
    "RekeningCategorie",
    "RekeningType",
    "Regeltype",
    # auth
    "LoginResponse",
    # administraties
    "AdministratieResponse",
    # boekjaren
    "Boekjaar",
    "BoekjaarResponse",
    # dagboeken
    "Dagboek",
    "DagboekResponse",
    "DagboekWerkStatus",
    # grootboekrekeningen
    "GrootboekMutatie",
    "Grootboekrekening",
    "GrootboekrekeningMetSaldoResponse",
    "GrootboekrekeningResponse",
    # boekingen
    "BoekingMetRegelsResponse",
    "BoekingResponse",
    "BoekingsregelResponse",
    "NewBoekingsregel",
    # btw codes
    "BtwCodeResponse",
    # btw aangifte
    "BtwAangifte",
    "BtwBerekening",
    "RubriekBedragen",
    # auto booking rules
    "AutoBookingRuleLineResponse",
    "AutoBookingRuleResponse",
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
