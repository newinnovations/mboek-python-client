"""mboek-client: high-level Python client for the mBoek bookkeeping API."""

from mboek._client import MboekClient
from mboek._exceptions import (
    AuthError,
    ConflictError,
    ForbiddenError,
    MboekError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from mboek.models import (
    AdministratieResponse,
    AutoBookingRuleLineResponse,
    AutoBookingRuleResponse,
    BalansRegel,
    BalansReport,
    BoekingMetRegelsResponse,
    BoekingResponse,
    BoekingsregelResponse,
    Boekjaar,
    BoekjaarStatus,
    BtwAangifte,
    BtwBerekening,
    BtwCodeResponse,
    BtwSoort,
    # new canonical names
    NewAdministratie,
    NewAutoBookingRule,
    NewAutoBookingRuleLine,
    NewBoeking,
    NewBoekingsregel,
    NewBoekjaar,
    NewBtwCode,
    NewDagboek,
    NewGrootboekrekening,
    UpdateAdministratie,
    UpdateAutoBookingRule,
    UpdateBoeking,
    UpdateBoekjaar,
    UpdateBtwCode,
    UpdateDagboek,
    UpdateGrootboekrekening,
    DagboekResponse,
    DagboekType,
    DagboekWerkStatus,
    GrootboekMutatie,
    GrootboekrekeningMetSaldoResponse,
    GrootboekrekeningResponse,
    ImportFormaat,
    ImportResult,
    LoginResponse,
    MatchSuggestion,
    Regeltype,
    RekeningCategorie,
    RekeningType,
    RubriekBedragen,
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
    "MboekClient",
    # exceptions
    "MboekError",
    "AuthError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    # models — new canonical names
    "AdministratieResponse",
    "AutoBookingRuleLineResponse",
    "AutoBookingRuleResponse",
    "BalansRegel",
    "BalansReport",
    "BoekingMetRegelsResponse",
    "BoekingResponse",
    "Boekjaar",
    "BoekjaarStatus",
    "BoekingsregelResponse",
    "BtwAangifte",
    "BtwBerekening",
    "BtwCodeResponse",
    "BtwSoort",
    "DagboekResponse",
    "DagboekType",
    "DagboekWerkStatus",
    "GrootboekMutatie",
    "GrootboekrekeningMetSaldoResponse",
    "GrootboekrekeningResponse",
    "ImportFormaat",
    "ImportResult",
    "LoginResponse",
    "MatchSuggestion",
    "NewAdministratie",
    "NewAutoBookingRule",
    "NewAutoBookingRuleLine",
    "NewBoeking",
    "NewBoekingsregel",
    "NewBoekjaar",
    "NewBtwCode",
    "NewDagboek",
    "NewGrootboekrekening",
    "UpdateAdministratie",
    "UpdateAutoBookingRule",
    "UpdateBoeking",
    "UpdateBoekjaar",
    "UpdateBtwCode",
    "UpdateDagboek",
    "UpdateGrootboekrekening",
    "RekeningCategorie",
    "RekeningType",
    "Regeltype",
    "RubriekBedragen",
    "WinstVerliesRegel",
    "WinstVerliesReport",
    # backward-compatible aliases
    "CreateAdministratieInput",
    "UpdateAdministratieInput",
    "CreateAutoBookingRuleInput",
    "CreateAutoBookingRuleLineInput",
    "UpdateAutoBookingRuleInput",
    "CreateBoekingInput",
    "CreateBoekingsregelInput",
    "UpdateBoekingInput",
    "CreateBoekjaarInput",
    "UpdateBoekjaarInput",
    "CreateBtwCodeInput",
    "UpdateBtwCodeInput",
    "CreateDagboekInput",
    "UpdateDagboekInput",
    "CreateGrootboekrekeningInput",
    "UpdateGrootboekrekeningInput",
]
