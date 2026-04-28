"""JSON → dataclass conversion helpers shared across resource modules."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from mboek.models._enums import (
    AutoBookingActieType,
    AutoBookingBedragType,
    BoekingStatus,
    BoekjaarStatus,
    BtwSoort,
    DagboekType,
    Regeltype,
    RekeningCategorie,
    RekeningType,
)
from mboek.models.administraties import AdministratieResponse
from mboek.models.auth import LoginResponse
from mboek.models.auto_booking_rules import (
    AutoBookingRuleLineResponse,
    AutoBookingRuleResponse,
)
from mboek.models.boekingen import (
    BoekingMetRegelsResponse,
    BoekingResponse,
    BoekingsregelResponse,
)
from mboek.models.boekjaren import Boekjaar
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCodeResponse
from mboek.models.dagboeken import Dagboek, DagboekWerkStatus
from mboek.models.export_import import ImportResult, MatchSuggestion
from mboek.models.grootboekrekeningen import GrootboekMutatie, Grootboekrekening
from mboek.models.reports import (
    BalansRegel,
    BalansReport,
    WinstVerliesRegel,
    WinstVerliesReport,
)


def _dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    # ISO-8601 with optional trailing Z
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _date(s: str | None) -> date | None:
    if s is None:
        return None
    return date.fromisoformat(s)


def _cents(v: int | None) -> Decimal | None:
    if v is None:
        return None
    return Decimal(v) / 100


def parse_login(d: dict) -> LoginResponse:
    return LoginResponse(
        token=d["token"],
        gebruikersnaam=d["gebruikersnaam"],
        expires_at=datetime.fromtimestamp(d["expires_at"]),
    )


def parse_administratie(d: dict) -> AdministratieResponse:
    return AdministratieResponse(
        id=d["id"],
        naam=d["naam"],
        beschrijving=d.get("beschrijving"),
        kvk_nummer=d.get("kvk_nummer"),
        btw_nummer=d.get("btw_nummer"),
        adres=d.get("adres"),
        active=d.get("active", True),
        huidig_boekjaar_id=d.get("huidig_boekjaar_id"),
        bankimport_rekening_id=d.get("bankimport_rekening_id"),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
    )


def parse_boekjaar(d: dict, *, client=None) -> Boekjaar:
    return Boekjaar(
        id=d["id"],
        administratie_id=d["administratie_id"],
        naam=d["naam"],
        start_datum=_date(d["start_datum"]),
        eind_datum=_date(d["eind_datum"]),
        status=BoekjaarStatus(d["status"]),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
        client=client,
    )


def parse_dagboek(d: dict, *, client=None, boekjaar_id=None) -> Dagboek:
    return Dagboek(
        id=d["id"],
        administratie_id=d["administratie_id"],
        code=d["code"],
        naam=d["naam"],
        dagboek_type=DagboekType(d["dagboek_type"]),
        grootboekrekening_id=d.get("grootboekrekening_id"),
        iban=d.get("iban"),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
    )


def parse_werkstatus(d: dict) -> DagboekWerkStatus:
    return DagboekWerkStatus(
        dagboek_id=d["dagboek_id"],
        onverwerkt=d["onverwerkt"],
        te_bevestigen=d["te_bevestigen"],
    )


def parse_grootboekrekening(
    d: dict, *, client=None, boekjaar_id=None
) -> Grootboekrekening:
    return Grootboekrekening(
        id=d["id"],
        administratie_id=d["administratie_id"],
        code=d["code"],
        naam=d["naam"],
        rekening_type=RekeningType(d["rekening_type"]),
        categorie=RekeningCategorie(d["categorie"]),
        rgs_code=d.get("rgs_code"),
        parent_id=d.get("parent_id"),
        default_btw_id=d.get("default_btw_id"),
        actief=d.get("actief", True),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
    )


def parse_grootboekrekening_met_saldo(
    d: dict, *, client=None, boekjaar_id=None
) -> Grootboekrekening:
    rekening_data = d.get("rekening", d)
    return Grootboekrekening(
        id=rekening_data["id"],
        administratie_id=rekening_data["administratie_id"],
        code=rekening_data["code"],
        naam=rekening_data["naam"],
        rekening_type=RekeningType(rekening_data["rekening_type"]),
        categorie=RekeningCategorie(rekening_data["categorie"]),
        rgs_code=rekening_data.get("rgs_code"),
        parent_id=rekening_data.get("parent_id"),
        default_btw_id=rekening_data.get("default_btw_id"),
        actief=rekening_data.get("actief", True),
        created_at=_dt(rekening_data["created_at"]),
        updated_at=_dt(rekening_data["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
        saldo=_cents(d["saldo"]),
        aantal_transacties=d["aantal_transacties"],
    )


def parse_grootboek_mutatie(d: dict) -> GrootboekMutatie:
    return GrootboekMutatie(
        regel_id=d["regel_id"],
        boeking_id=d["boeking_id"],
        dagboek_id=d["dagboek_id"],
        datum=d["datum"],
        dagboek_code=d["dagboek_code"],
        dagboek_naam=d["dagboek_naam"],
        boeking_omschrijving=d["boeking_omschrijving"],
        regel_omschrijving=d["regel_omschrijving"],
        bedrag=_cents(d["bedrag"]),
    )


def parse_btw_code(d: dict) -> BtwCodeResponse:
    return BtwCodeResponse(
        id=d["id"],
        administratie_id=d["administratie_id"],
        code=d["code"],
        omschrijving=d["omschrijving"],
        percentage=Decimal(str(d["percentage"])),
        soort=BtwSoort(d["soort"]),
        output_rekening_id=d.get("output_rekening_id"),
        input_rekening_id=d.get("input_rekening_id"),
        pct_aftrek=Decimal(str(d["pct_aftrek"])),
        actief=d.get("actief", True),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
    )


def parse_boekingsregel(d: dict) -> BoekingsregelResponse:
    return BoekingsregelResponse(
        id=d["id"],
        boeking_id=d["boeking_id"],
        grootboekrekening_id=d["grootboekrekening_id"],
        omschrijving=d.get("omschrijving", ""),
        bedrag=_cents(d["bedrag"]),
        btw_code_id=d.get("btw_code_id"),
        regeltype=Regeltype(d["regeltype"]),
        netto_id=d.get("netto_id"),
        created_at=_dt(d["created_at"]),
    )


def parse_boeking(d: dict) -> BoekingResponse:
    return BoekingResponse(
        id=d["id"],
        dagboek_id=d["dagboek_id"],
        boekjaar_id=d["boekjaar_id"],
        datum=_date(d["datum"]),
        omschrijving=d.get("omschrijving", ""),
        stuknummer=d.get("stuknummer"),
        status=BoekingStatus(d.get("status", "concept")),
        tegenpartij_naam=d.get("tegenpartij_naam"),
        tegenpartij_iban=d.get("tegenpartij_iban"),
        referentie_import=d.get("referentie_import"),
        import_hash=d.get("import_hash"),
        auto_geboekt=d.get("auto_geboekt", False),
        gecontroleerd=d.get("gecontroleerd", False),
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
    )


def parse_boeking_met_regels(d: dict) -> BoekingMetRegelsResponse:
    return BoekingMetRegelsResponse(
        boeking=parse_boeking(d),
        regels=[parse_boekingsregel(r) for r in d.get("regels", [])],
    )


def _parse_rubriek(d: dict) -> RubriekBedragen:
    return RubriekBedragen(
        grondslag=Decimal(str(d["grondslag"])),
        btw=Decimal(str(d["btw"])),
    )


def parse_btw_berekening(d: dict) -> BtwBerekening:
    return BtwBerekening(
        r1a=_parse_rubriek(d["r1a"]),
        r1b=_parse_rubriek(d["r1b"]),
        r1c=_parse_rubriek(d["r1c"]),
        r1d=_parse_rubriek(d["r1d"]),
        r1e=_parse_rubriek(d["r1e"]),
        r2a=_parse_rubriek(d["r2a"]),
        r3a=_parse_rubriek(d["r3a"]),
        r3b=_parse_rubriek(d["r3b"]),
        r3c=_parse_rubriek(d["r3c"]),
        r4a=_parse_rubriek(d["r4a"]),
        r4b=_parse_rubriek(d["r4b"]),
        r5a=Decimal(str(d["r5a"])),
        r5b=Decimal(str(d["r5b"])),
        r5g=Decimal(str(d["r5g"])),
    )


def parse_btw_aangifte(d: dict) -> BtwAangifte:
    return BtwAangifte(
        id=d["id"],
        administratie_id=d["administratie_id"],
        boekjaar_id=d["boekjaar_id"],
        kwartaal=d["kwartaal"],
        periode_start=_date(d["periode_start"]),
        periode_eind=_date(d["periode_eind"]),
        berekening=parse_btw_berekening(d["berekening"]),
        r5g=Decimal(str(d["r5g"])),
        status=d["status"],
    )


def parse_auto_booking_rule_line(d: dict) -> AutoBookingRuleLineResponse:
    return AutoBookingRuleLineResponse(
        id=d["id"],
        rule_id=d["rule_id"],
        volgorde=d["volgorde"],
        grootboekrekening_id=d["grootboekrekening_id"],
        btw_code_id=d.get("btw_code_id"),
        omschrijving=d.get("omschrijving"),
        bedrag_type=AutoBookingBedragType(d["bedrag_type"]),
        bedrag=_cents(d["bedrag"]) if d.get("bedrag") is not None else None,
    )


def parse_auto_booking_rule(d: dict) -> AutoBookingRuleResponse:
    return AutoBookingRuleResponse(
        id=d["id"],
        administratie_id=d["administratie_id"],
        naam=d["naam"],
        prioriteit=d["prioriteit"],
        actief=d["actief"],
        actie_type=AutoBookingActieType(d["actie_type"]),
        eigen_iban_patroon=d.get("eigen_iban_patroon"),
        tegenpartij_iban_patroon=d.get("tegenpartij_iban_patroon"),
        omschrijving_patroon=d.get("omschrijving_patroon"),
        lines=[parse_auto_booking_rule_line(ln) for ln in d.get("lines", [])],
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
    )


def _parse_balans_regel(d: dict) -> BalansRegel:
    return BalansRegel(
        code=d["code"],
        naam=d["naam"],
        debet=Decimal(str(d["debet"])),
        credit=Decimal(str(d["credit"])),
        saldo=Decimal(str(d["saldo"])),
    )


def parse_balans(d: dict) -> BalansReport:
    return BalansReport(
        boekjaar_naam=d["boekjaar_naam"],
        activa=[_parse_balans_regel(r) for r in d["activa"]],
        passiva=[_parse_balans_regel(r) for r in d["passiva"]],
        totaal_activa=Decimal(str(d["totaal_activa"])),
        totaal_passiva=Decimal(str(d["totaal_passiva"])),
        in_balans=d["in_balans"],
    )


def _parse_winst_verlies_regel(d: dict) -> WinstVerliesRegel:
    return WinstVerliesRegel(
        code=d["code"],
        naam=d["naam"],
        bedrag=Decimal(str(d["bedrag"])),
    )


def parse_winst_verlies(d: dict) -> WinstVerliesReport:
    return WinstVerliesReport(
        boekjaar_naam=d["boekjaar_naam"],
        opbrengsten=[_parse_winst_verlies_regel(r) for r in d["opbrengsten"]],
        kosten=[_parse_winst_verlies_regel(r) for r in d["kosten"]],
        bijzonder=[_parse_winst_verlies_regel(r) for r in d["bijzonder"]],
        totaal_opbrengsten=Decimal(str(d["totaal_opbrengsten"])),
        totaal_kosten=Decimal(str(d["totaal_kosten"])),
        totaal_bijzonder=Decimal(str(d["totaal_bijzonder"])),
        netto_resultaat=Decimal(str(d["netto_resultaat"])),
    )


def parse_import_result(d: dict) -> ImportResult:
    return ImportResult(
        imported=d["imported"],
        skipped=d.get("skipped", 0),
        boeking_ids=d.get("boeking_ids", []),
    )


def parse_match_suggestion(d: dict) -> MatchSuggestion:
    return MatchSuggestion(
        grootboekrekening_id=d["grootboekrekening_id"],
        code=d["code"],
        naam=d["naam"],
        btw_code_id=d.get("btw_code_id"),
        btw_code=d.get("btw_code"),
        confidence=Decimal(str(d.get("confidence", 0))),
    )
