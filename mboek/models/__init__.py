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
from mboek.models.administraties import (
    AdministratieResponse,
    NewAdministratie,
    UpdateAdministratie,
)
from mboek.models.auth import LoginResponse
from mboek.models.auto_booking_rules import (
    AutoBookingRuleLineResponse,
    AutoBookingRuleResponse,
    NewAutoBookingRule,
    NewAutoBookingRuleLine,
    UpdateAutoBookingRule,
)
from mboek.models.boekingen import (
    BoekingMetRegelsResponse,
    BoekingResponse,
    BoekingsregelResponse,
    NewBoeking,
    NewBoekingsregel,
    UpdateBoeking,
)
from mboek.models.boekjaren import (
    Boekjaar,
    BoekjaarResponse,
    NewBoekjaar,
    UpdateBoekjaar,
)
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCodeResponse, NewBtwCode, UpdateBtwCode
from mboek.models.dagboeken import (
    DagboekResponse,
    DagboekWerkStatus,
    NewDagboek,
    UpdateDagboek,
)
from mboek.models.export_import import ImportResult, MatchSuggestion
from mboek.models.grootboekrekeningen import (
    GrootboekMutatie,
    GrootboekrekeningMetSaldoResponse,
    GrootboekrekeningResponse,
    NewGrootboekrekening,
    UpdateGrootboekrekening,
)
from mboek.models.reports import (
    BalansRegel,
    BalansReport,
    WinstVerliesRegel,
    WinstVerliesReport,
)

# ---------------------------------------------------------------------------
# Backward-compatible aliases (old names → new names)
# ---------------------------------------------------------------------------
CreateAdministratieInput = NewAdministratie
UpdateAdministratieInput = UpdateAdministratie
CreateAutoBookingRuleInput = NewAutoBookingRule
CreateAutoBookingRuleLineInput = NewAutoBookingRuleLine
UpdateAutoBookingRuleInput = UpdateAutoBookingRule
CreateBoekingInput = NewBoeking
CreateBoekingsregelInput = NewBoekingsregel
UpdateBoekingInput = UpdateBoeking
CreateBoekjaarInput = NewBoekjaar
UpdateBoekjaarInput = UpdateBoekjaar
CreateBtwCodeInput = NewBtwCode
UpdateBtwCodeInput = UpdateBtwCode
CreateDagboekInput = NewDagboek
UpdateDagboekInput = UpdateDagboek
CreateGrootboekrekeningInput = NewGrootboekrekening
UpdateGrootboekrekeningInput = UpdateGrootboekrekening

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
    "NewAdministratie",
    "UpdateAdministratie",
    "CreateAdministratieInput",  # alias
    "UpdateAdministratieInput",  # alias
    # boekjaren
    "Boekjaar",
    "BoekjaarResponse",
    "NewBoekjaar",
    "UpdateBoekjaar",
    "CreateBoekjaarInput",  # alias
    "UpdateBoekjaarInput",  # alias
    # dagboeken
    "DagboekResponse",
    "DagboekWerkStatus",
    "NewDagboek",
    "UpdateDagboek",
    "CreateDagboekInput",  # alias
    "UpdateDagboekInput",  # alias
    # grootboekrekeningen
    "GrootboekMutatie",
    "GrootboekrekeningMetSaldoResponse",
    "GrootboekrekeningResponse",
    "NewGrootboekrekening",
    "UpdateGrootboekrekening",
    "CreateGrootboekrekeningInput",  # alias
    "UpdateGrootboekrekeningInput",  # alias
    # boekingen
    "BoekingMetRegelsResponse",
    "BoekingResponse",
    "BoekingsregelResponse",
    "NewBoeking",
    "NewBoekingsregel",
    "UpdateBoeking",
    "CreateBoekingInput",  # alias
    "CreateBoekingsregelInput",  # alias
    "UpdateBoekingInput",  # alias
    # btw codes
    "BtwCodeResponse",
    "NewBtwCode",
    "UpdateBtwCode",
    "CreateBtwCodeInput",  # alias
    "UpdateBtwCodeInput",  # alias
    # btw aangifte
    "BtwAangifte",
    "BtwBerekening",
    "RubriekBedragen",
    # auto booking rules
    "AutoBookingRuleLineResponse",
    "AutoBookingRuleResponse",
    "NewAutoBookingRule",
    "NewAutoBookingRuleLine",
    "UpdateAutoBookingRule",
    "CreateAutoBookingRuleInput",  # alias
    "CreateAutoBookingRuleLineInput",  # alias
    "UpdateAutoBookingRuleInput",  # alias
    # reports
    "BalansRegel",
    "BalansReport",
    "WinstVerliesRegel",
    "WinstVerliesReport",
    # import / export
    "ImportResult",
    "MatchSuggestion",
]
