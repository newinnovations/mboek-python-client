"""Model types for the mBoek API client."""

from mboek.models._enums import (
    AutoBookingActieType,
    AutoBookingBedragType,
    BoekingStatus,
    BoekjaarStatus,
    BtwSoort,
    DagboekType,
    ImportFormaat,
    RekeningCategorie,
    RekeningType,
    Regeltype,
)
from mboek.models.administraties import (
    AdministratieResponse,
    CreateAdministratieInput,
    UpdateAdministratieInput,
)
from mboek.models.auth import LoginResponse
from mboek.models.auto_booking_rules import (
    AutoBookingRuleLineResponse,
    AutoBookingRuleResponse,
    CreateAutoBookingRuleInput,
    CreateAutoBookingRuleLineInput,
    UpdateAutoBookingRuleInput,
)
from mboek.models.boekingen import (
    BoekingMetRegelsResponse,
    BoekingResponse,
    BoekingsregelResponse,
    CreateBoekingInput,
    CreateBoekingsregelInput,
    UpdateBoekingInput,
)
from mboek.models.boekjaren import (
    Boekjaar,
    BoekjaarResponse,
    CreateBoekjaarInput,
    UpdateBoekjaarInput,
)
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCodeResponse, CreateBtwCodeInput, UpdateBtwCodeInput
from mboek.models.dagboeken import (
    CreateDagboekInput,
    DagboekResponse,
    DagboekWerkStatus,
    UpdateDagboekInput,
)
from mboek.models.export_import import ImportResult, MatchSuggestion
from mboek.models.grootboekrekeningen import (
    CreateGrootboekrekeningInput,
    GrootboekMutatie,
    GrootboekrekeningMetSaldoResponse,
    GrootboekrekeningResponse,
    UpdateGrootboekrekeningInput,
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
    "CreateAdministratieInput",
    "UpdateAdministratieInput",
    # boekjaren
    "Boekjaar",
    "BoekjaarResponse",
    "CreateBoekjaarInput",
    "UpdateBoekjaarInput",
    # dagboeken
    "CreateDagboekInput",
    "DagboekResponse",
    "DagboekWerkStatus",
    "UpdateDagboekInput",
    # grootboekrekeningen
    "CreateGrootboekrekeningInput",
    "GrootboekMutatie",
    "GrootboekrekeningMetSaldoResponse",
    "GrootboekrekeningResponse",
    "UpdateGrootboekrekeningInput",
    # boekingen
    "BoekingMetRegelsResponse",
    "BoekingResponse",
    "BoekingsregelResponse",
    "CreateBoekingInput",
    "CreateBoekingsregelInput",
    "UpdateBoekingInput",
    # btw codes
    "BtwCodeResponse",
    "CreateBtwCodeInput",
    "UpdateBtwCodeInput",
    # btw aangifte
    "BtwAangifte",
    "BtwBerekening",
    "RubriekBedragen",
    # auto booking rules
    "AutoBookingRuleLineResponse",
    "AutoBookingRuleResponse",
    "CreateAutoBookingRuleInput",
    "CreateAutoBookingRuleLineInput",
    "UpdateAutoBookingRuleInput",
    # reports
    "BalansRegel",
    "BalansReport",
    "WinstVerliesRegel",
    "WinstVerliesReport",
    # import / export
    "ImportResult",
    "MatchSuggestion",
]
