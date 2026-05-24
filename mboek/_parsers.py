"""JSON → dataclass conversion helpers shared across resource modules."""

from __future__ import annotations

import base64
import binascii
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from mboek.models._enums import (
    AutoBookingActieType,
    AutoBookingBedragType,
    BoekingStatus,
    BoekjaarStatus,
    BtwAangifteStatus,
    BtwSoort,
    DagboekType,
    JaarrekeningLogLevel,
    Regeltype,
    RekeningCategorie,
    RekeningType,
)
from mboek.models.administraties import Administratie
from mboek.models.auth import AuthToken, CurrentUser
from mboek.models.auto_booking_rules import AutoBookingRule, AutoBookingRuleLine
from mboek.models.boekingen import Boeking, Boekingsregel
from mboek.models.boekjaren import Boekjaar
from mboek.models.btw_aangifte import BtwAangifte, BtwBerekening, RubriekBedragen
from mboek.models.btw_codes import BtwCode
from mboek.models.dagboeken import Dagboek, DagboekWerkStatus
from mboek.models.export_import import (
    AdministratieExport,
    AdministratieImportResult,
    AutoBookingRulesExport,
    AutoBookingRulesImportResult,
    BoekingenImportResult,
    BoekingExport,
    BoekjaarExport,
    BoekjaarImportResult,
    ImportResult,
    MatchSuggestion,
)
from mboek.models.grootboekrekeningen import GrootboekMutatie, Grootboekrekening
from mboek.models.jaarrekening import (
    JaarrekeningBalansRegel,
    JaarrekeningBeginbalans,
    JaarrekeningHtmlReport,
    JaarrekeningPdfReport,
    JaarrekeningRuntimeMessage,
    JaarrekeningSummary,
)
from mboek.models.maintenance import VacuumResult
from mboek.models.reports import (
    BalansRegel,
    BalansReport,
    WinstVerliesRegel,
    WinstVerliesReport,
)


def _require_object(payload: object, *, response_name: str) -> dict:
    if not isinstance(payload, dict):
        raise ValueError(f"{response_name} response must be a JSON object")
    return payload


def _require_keys(d: dict, *, response_name: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        if key not in d:
            raise ValueError(f"{response_name} response missing required key: {key!r}")


def _require_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_bool(value: object, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_list(value: object, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return cast(list[Any], value)


def _require_string_map(value: object, *, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be strings")
        if not isinstance(item, str):
            raise ValueError(f"{field_name} values must be strings")
        result[key] = item
    return result


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


def _require_dt(s: str | None) -> datetime:
    value = _dt(s)
    if value is None:
        raise ValueError("Expected datetime value")
    return value


def _require_date(s: str | None) -> date:
    value = _date(s)
    if value is None:
        raise ValueError("Expected date value")
    return value


def _require_cents(v: int | None) -> Decimal:
    value = _cents(v)
    if value is None:
        raise ValueError("Expected amount in cents")
    return value


def _require_decimal_string(value: object, *, field_name: str) -> Decimal:
    string_value = _require_string(value, field_name=field_name)
    try:
        return Decimal(string_value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc


def parse_login(d: dict) -> AuthToken:
    d = _require_object(d, response_name="Login")
    _require_keys(
        d,
        response_name="Login",
        keys=("token", "gebruikersnaam", "expires_at"),
    )
    return AuthToken(
        token=d["token"],
        gebruikersnaam=d["gebruikersnaam"],
        expires_at=datetime.fromtimestamp(d["expires_at"], tz=timezone.utc),
    )


def parse_current_user(payload: object) -> CurrentUser:
    d = _require_object(payload, response_name="Current user")
    _require_keys(
        d,
        response_name="Current user",
        keys=("gebruikersnaam", "sub"),
    )
    return CurrentUser(
        gebruikersnaam=d["gebruikersnaam"],
        sub=d["sub"],
    )


def parse_administratie(d: dict) -> Administratie:
    d = _require_object(d, response_name="Administratie")
    _require_keys(
        d,
        response_name="Administratie",
        keys=("id", "naam", "active", "created_at", "updated_at"),
    )
    return Administratie(
        id=d["id"],
        naam=d["naam"],
        beschrijving=d.get("beschrijving"),
        kvk_nummer=d.get("kvk_nummer"),
        btw_nummer=d.get("btw_nummer"),
        adres=d.get("adres"),
        active=_require_bool(
            d["active"], field_name="Administratie response field 'active'"
        ),
        huidig_boekjaar_id=d.get("huidig_boekjaar_id"),
        bankimport_rekening_id=d.get("bankimport_rekening_id"),
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
    )


def parse_boekjaar(d: dict, *, client=None) -> Boekjaar:
    d = _require_object(d, response_name="Boekjaar")
    return Boekjaar(
        id=d["id"],
        administratie_id=d["administratie_id"],
        naam=d["naam"],
        start_datum=_require_date(d["start_datum"]),
        eind_datum=_require_date(d["eind_datum"]),
        status=BoekjaarStatus(d["status"]),
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
        client=client,
    )


def parse_dagboek(d: dict, *, client=None, boekjaar_id=None) -> Dagboek:
    d = _require_object(d, response_name="Dagboek")
    if client is not None:
        client._dagboek_admin_cache[d["id"]] = d["administratie_id"]
    return Dagboek(
        id=d["id"],
        administratie_id=d["administratie_id"],
        code=d["code"],
        naam=d["naam"],
        dagboek_type=DagboekType(d["dagboek_type"]),
        grootboekrekening_id=d.get("grootboekrekening_id"),
        iban=d.get("iban"),
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
    )


def parse_werkstatus(d: dict) -> DagboekWerkStatus:
    d = _require_object(d, response_name="Dagboek werkstatus")
    return DagboekWerkStatus(
        dagboek_id=d["dagboek_id"],
        onverwerkt=d["onverwerkt"],
        te_bevestigen=d["te_bevestigen"],
    )


def parse_grootboekrekening(
    d: dict, *, client=None, boekjaar_id=None
) -> Grootboekrekening:
    d = _require_object(d, response_name="Grootboekrekening")
    _require_keys(
        d,
        response_name="Grootboekrekening",
        keys=(
            "id",
            "administratie_id",
            "code",
            "naam",
            "rekening_type",
            "categorie",
            "actief",
            "created_at",
            "updated_at",
        ),
    )
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
        actief=_require_bool(
            d["actief"], field_name="Grootboekrekening response field 'actief'"
        ),
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
    )


def parse_grootboekrekening_met_saldo(
    d: dict, *, client=None, boekjaar_id=None
) -> Grootboekrekening:
    d = _require_object(d, response_name="Grootboekrekening met saldo")
    rekening_data = d.get("rekening", d)
    _require_keys(
        rekening_data,
        response_name="Grootboekrekening met saldo",
        keys=(
            "id",
            "administratie_id",
            "code",
            "naam",
            "rekening_type",
            "categorie",
            "actief",
            "created_at",
            "updated_at",
        ),
    )
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
        actief=_require_bool(
            rekening_data["actief"],
            field_name="Grootboekrekening met saldo response field 'actief'",
        ),
        created_at=_require_dt(rekening_data["created_at"]),
        updated_at=_require_dt(rekening_data["updated_at"]),
        client=client,
        boekjaar_id=boekjaar_id,
        saldo=_require_cents(d["saldo"]),
        aantal_transacties=d["aantal_transacties"],
    )


def parse_grootboek_mutatie(d: dict) -> GrootboekMutatie:
    d = _require_object(d, response_name="Grootboek mutatie")
    return GrootboekMutatie(
        regel_id=d["regel_id"],
        boeking_id=d["boeking_id"],
        dagboek_id=d["dagboek_id"],
        dagboek_type=DagboekType(d["dagboek_type"]),
        datum=_require_date(d["datum"]),
        dagboek_code=d["dagboek_code"],
        dagboek_naam=d["dagboek_naam"],
        boeking_omschrijving=d["boeking_omschrijving"],
        regel_omschrijving=d["regel_omschrijving"],
        bedrag=_require_cents(d["bedrag"]),
    )


def parse_btw_code(d: dict) -> BtwCode:
    d = _require_object(d, response_name="BTW code")
    _require_keys(
        d,
        response_name="BTW code",
        keys=(
            "id",
            "administratie_id",
            "code",
            "omschrijving",
            "percentage",
            "soort",
            "pct_aftrek",
            "actief",
            "created_at",
            "updated_at",
        ),
    )
    return BtwCode(
        id=d["id"],
        administratie_id=d["administratie_id"],
        code=d["code"],
        omschrijving=d["omschrijving"],
        percentage=Decimal(str(d["percentage"])),
        soort=BtwSoort(d["soort"]),
        output_rekening_id=d.get("output_rekening_id"),
        input_rekening_id=d.get("input_rekening_id"),
        pct_aftrek=Decimal(str(d["pct_aftrek"])),
        actief=_require_bool(
            d["actief"], field_name="BTW code response field 'actief'"
        ),
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
    )


def parse_boekingsregel(d: dict) -> Boekingsregel:
    d = _require_object(d, response_name="Boekingsregel")
    _require_keys(
        d,
        response_name="Boekingsregel",
        keys=(
            "id",
            "boeking_id",
            "grootboekrekening_id",
            "omschrijving",
            "bedrag",
            "regeltype",
            "created_at",
        ),
    )
    return Boekingsregel(
        id=d["id"],
        boeking_id=d["boeking_id"],
        grootboekrekening_id=d["grootboekrekening_id"],
        omschrijving=_require_string(
            d["omschrijving"], field_name="Boekingsregel response field 'omschrijving'"
        ),
        bedrag=_require_cents(d["bedrag"]),
        btw_code_id=d.get("btw_code_id"),
        regeltype=Regeltype(d["regeltype"]),
        netto_id=d.get("netto_id"),
        created_at=_require_dt(d["created_at"]),
    )


def parse_boeking_met_regels(d: dict, *, client=None, administratie_id=None) -> Boeking:
    d = _require_object(d, response_name="Boeking")
    _require_keys(
        d,
        response_name="Boeking",
        keys=(
            "id",
            "dagboek_id",
            "boekjaar_id",
            "datum",
            "omschrijving",
            "status",
            "auto_geboekt",
            "gecontroleerd",
            "regels",
            "created_at",
            "updated_at",
        ),
    )
    regels_payload = _require_list(
        d["regels"], field_name="Boeking response field 'regels'"
    )
    resolved_admin_id = administratie_id
    if resolved_admin_id is None and client is not None:
        resolved_admin_id = client._dagboek_admin_cache.get(d["dagboek_id"])
    if resolved_admin_id is not None and client is not None:
        client._dagboek_admin_cache[d["dagboek_id"]] = resolved_admin_id
    return Boeking(
        id=d["id"],
        dagboek_id=d["dagboek_id"],
        boekjaar_id=d["boekjaar_id"],
        datum=_require_date(d["datum"]),
        omschrijving=_require_string(
            d["omschrijving"], field_name="Boeking response field 'omschrijving'"
        ),
        stuknummer=d.get("stuknummer"),
        status=BoekingStatus(
            _require_string(d["status"], field_name="Boeking response field 'status'")
        ),
        tegenpartij_naam=d.get("tegenpartij_naam"),
        tegenpartij_iban=d.get("tegenpartij_iban"),
        referentie_import=d.get("referentie_import"),
        import_hash=d.get("import_hash"),
        auto_geboekt=_require_bool(
            d["auto_geboekt"], field_name="Boeking response field 'auto_geboekt'"
        ),
        gecontroleerd=_require_bool(
            d["gecontroleerd"], field_name="Boeking response field 'gecontroleerd'"
        ),
        regels=[parse_boekingsregel(r) for r in regels_payload],
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
        client=client,
        administratie_id=resolved_admin_id,
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
    d = _require_object(d, response_name="BTW aangifte")
    return BtwAangifte(
        id=d["id"],
        administratie_id=d["administratie_id"],
        boekjaar_id=d["boekjaar_id"],
        kwartaal=d["kwartaal"],
        periode_start=_require_date(d["periode_start"]),
        periode_eind=_require_date(d["periode_eind"]),
        berekening=parse_btw_berekening(d["berekening"]),
        r5g=Decimal(str(d["r5g"])),
        status=BtwAangifteStatus(d["status"]),
    )


def parse_auto_booking_rule_line(d: dict) -> AutoBookingRuleLine:
    d = _require_object(d, response_name="Auto-booking rule line")
    _require_keys(
        d,
        response_name="Auto-booking rule line",
        keys=("id", "rule_id", "bedrag_type", "tegenrekening_id", "omschrijving"),
    )
    return AutoBookingRuleLine(
        id=d["id"],
        rule_id=d["rule_id"],
        tegenrekening_id=d["tegenrekening_id"],
        btw_code_id=d.get("btw_code_id"),
        omschrijving=_require_string(
            d["omschrijving"],
            field_name="Auto-booking rule line response field 'omschrijving'",
        ),
        bedrag_type=AutoBookingBedragType(d["bedrag_type"]),
        bedrag=_cents(d["bedrag"]) if d.get("bedrag") is not None else None,
    )


def parse_auto_booking_rule(d: dict) -> AutoBookingRule:
    d = _require_object(d, response_name="Auto-booking rule")
    _require_keys(
        d,
        response_name="Auto-booking rule",
        keys=(
            "id",
            "administratie_id",
            "naam",
            "prioriteit",
            "actie_type",
            "actief",
            "lines",
            "created_at",
            "updated_at",
        ),
    )
    lines_payload = _require_list(
        d["lines"], field_name="Auto-booking rule response field 'lines'"
    )
    return AutoBookingRule(
        id=d["id"],
        administratie_id=d["administratie_id"],
        naam=d["naam"],
        prioriteit=d["prioriteit"],
        actief=_require_bool(
            d["actief"], field_name="Auto-booking rule response field 'actief'"
        ),
        actie_type=AutoBookingActieType(d["actie_type"]),
        btw_code_id=d.get("btw_code_id"),
        iban_eigen=d.get("iban_eigen"),
        iban_tegenpartij=d.get("iban_tegenpartij"),
        omschrijving_regex=d.get("omschrijving_regex"),
        tegenrekening_id=d.get("tegenrekening_id"),
        lines=[parse_auto_booking_rule_line(ln) for ln in lines_payload],
        created_at=_require_dt(d["created_at"]),
        updated_at=_require_dt(d["updated_at"]),
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
    d = _require_object(d, response_name="Balans")
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
    d = _require_object(d, response_name="Winst/verlies")
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


def _parse_jaarrekening_runtime_message(payload: object) -> JaarrekeningRuntimeMessage:
    d = _require_object(payload, response_name="Jaarrekening runtime message")
    for key in ("level", "message"):
        if key not in d:
            raise ValueError(
                f"Jaarrekening runtime message missing required key: {key!r}"
            )
    return JaarrekeningRuntimeMessage(
        level=JaarrekeningLogLevel(
            _require_string(
                d["level"], field_name="Jaarrekening runtime message field 'level'"
            )
        ),
        message=_require_string(
            d["message"], field_name="Jaarrekening runtime message field 'message'"
        ),
    )


def _parse_jaarrekening_balans_regel(payload: object) -> JaarrekeningBalansRegel:
    d = _require_object(payload, response_name="Jaarrekening balansregel")
    _require_keys(
        d,
        response_name="Jaarrekening balansregel",
        keys=("nummer", "omschrijving", "bedrag"),
    )
    return JaarrekeningBalansRegel(
        nummer=d["nummer"],
        omschrijving=_require_string(
            d["omschrijving"],
            field_name="Jaarrekening balansregel field 'omschrijving'",
        ),
        bedrag=_require_decimal_string(
            d["bedrag"], field_name="Jaarrekening balansregel field 'bedrag'"
        ),
    )


def _parse_jaarrekening_beginbalans(payload: object) -> JaarrekeningBeginbalans:
    d = _require_object(payload, response_name="Jaarrekening beginbalans")
    _require_keys(
        d,
        response_name="Jaarrekening beginbalans",
        keys=("jaar", "regels"),
    )
    regels_payload = _require_list(
        d["regels"], field_name="Jaarrekening beginbalans field 'regels'"
    )
    afrondingsverschil_payload = d.get("afrondingsverschil")
    afrondingsverschil = (
        None
        if afrondingsverschil_payload is None
        else _parse_jaarrekening_balans_regel(afrondingsverschil_payload)
    )
    return JaarrekeningBeginbalans(
        jaar=d["jaar"],
        regels=[_parse_jaarrekening_balans_regel(item) for item in regels_payload],
        afrondingsverschil=afrondingsverschil,
    )


def _parse_jaarrekening_summary(payload: object) -> JaarrekeningSummary:
    d = _require_object(payload, response_name="Jaarrekening summary")
    _require_keys(
        d,
        response_name="Jaarrekening summary",
        keys=(
            "netto_resultaat",
            "vpb_resultaat_voor_belastingen",
            "vpb_belastbaar_bedrag",
            "vpb_berekend",
            "vpb_geboekt",
        ),
    )
    return JaarrekeningSummary(
        netto_resultaat=_require_decimal_string(
            d["netto_resultaat"],
            field_name="Jaarrekening summary field 'netto_resultaat'",
        ),
        vpb_resultaat_voor_belastingen=_require_decimal_string(
            d["vpb_resultaat_voor_belastingen"],
            field_name="Jaarrekening summary field 'vpb_resultaat_voor_belastingen'",
        ),
        vpb_belastbaar_bedrag=_require_decimal_string(
            d["vpb_belastbaar_bedrag"],
            field_name="Jaarrekening summary field 'vpb_belastbaar_bedrag'",
        ),
        vpb_berekend=_require_decimal_string(
            d["vpb_berekend"], field_name="Jaarrekening summary field 'vpb_berekend'"
        ),
        vpb_geboekt=_require_decimal_string(
            d["vpb_geboekt"], field_name="Jaarrekening summary field 'vpb_geboekt'"
        ),
    )


def _parse_jaarrekening_common(payload: object, *, response_name: str) -> tuple[
    JaarrekeningBeginbalans,
    JaarrekeningSummary,
    str,
    list[JaarrekeningRuntimeMessage],
]:
    d = _require_object(payload, response_name=response_name)
    _require_keys(
        d,
        response_name=response_name,
        keys=("beginbalans", "summary", "hash", "messages"),
    )
    messages_payload = _require_list(
        d["messages"], field_name=f"{response_name} response field 'messages'"
    )
    return (
        _parse_jaarrekening_beginbalans(d["beginbalans"]),
        _parse_jaarrekening_summary(d["summary"]),
        _require_string(d["hash"], field_name=f"{response_name} response field 'hash'"),
        [_parse_jaarrekening_runtime_message(item) for item in messages_payload],
    )


def parse_jaarrekening_html(payload: object) -> JaarrekeningHtmlReport:
    beginbalans, summary, hash_value, messages = _parse_jaarrekening_common(
        payload, response_name="Jaarrekening HTML"
    )
    d = _require_object(payload, response_name="Jaarrekening HTML")
    if "html" not in d:
        raise ValueError("Jaarrekening HTML response missing required key: 'html'")
    return JaarrekeningHtmlReport(
        beginbalans=beginbalans,
        summary=summary,
        html=_require_string(
            d["html"], field_name="Jaarrekening HTML response field 'html'"
        ),
        hash=hash_value,
        messages=messages,
    )


def parse_jaarrekening_pdf(payload: object) -> JaarrekeningPdfReport:
    beginbalans, summary, hash_value, messages = _parse_jaarrekening_common(
        payload, response_name="Jaarrekening PDF"
    )
    d = _require_object(payload, response_name="Jaarrekening PDF")
    if "pdf" not in d:
        raise ValueError("Jaarrekening PDF response missing required key: 'pdf'")
    pdf_base64 = _require_string(
        d["pdf"], field_name="Jaarrekening PDF response field 'pdf'"
    )
    try:
        pdf = base64.b64decode(pdf_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "Jaarrekening PDF response field 'pdf' must be valid base64"
        ) from exc
    return JaarrekeningPdfReport(
        beginbalans=beginbalans,
        summary=summary,
        hash=hash_value,
        messages=messages,
        pdf=pdf,
    )


def parse_import_result(d: dict) -> ImportResult:
    return ImportResult(
        imported=d["imported"],
        duplicates_skipped=d["duplicates_skipped"],
        zero_bedrag_skipped=d["zero_bedrag_skipped"],
        boekjaar_niet_gevonden_skipped=d["boekjaar_niet_gevonden_skipped"],
        auto_geboekt=d["auto_geboekt"],
        unmatched_ibans=d["unmatched_ibans"],
        parse_warnings=d.get("parse_warnings"),
    )


def parse_administratie_export(payload: object) -> AdministratieExport:
    d = _require_object(payload, response_name="Administratie export")
    return AdministratieExport.from_dict(d)


def parse_boekjaar_export(payload: object) -> BoekjaarExport:
    d = _require_object(payload, response_name="Boekjaar export")
    return BoekjaarExport.from_dict(d)


def parse_boeking_export(payload: object) -> BoekingExport:
    d = _require_object(payload, response_name="Boeking export")
    return BoekingExport.from_dict(d)


def parse_administratie_import_result(payload: object) -> AdministratieImportResult:
    d = _require_object(payload, response_name="Administratie import")
    for key in ("administratie_id", "naam", "boekingen_imported"):
        if key not in d:
            raise ValueError(
                f"Administratie import response missing required key: {key!r}"
            )
    return AdministratieImportResult(
        administratie_id=d["administratie_id"],
        naam=d["naam"],
        boekingen_imported=d["boekingen_imported"],
    )


def parse_boekjaar_import_result(payload: object) -> BoekjaarImportResult:
    d = _require_object(payload, response_name="Boekjaar import")
    for key in ("boekjaar_id", "naam", "boekingen_imported"):
        if key not in d:
            raise ValueError(f"Boekjaar import response missing required key: {key!r}")
    return BoekjaarImportResult(
        boekjaar_id=d["boekjaar_id"],
        naam=d["naam"],
        boekingen_imported=d["boekingen_imported"],
    )


def parse_boekingen_import_result(d: dict) -> BoekingenImportResult:
    d = _require_object(d, response_name="Boekingen import")
    return BoekingenImportResult(
        dagboek_id=d["dagboek_id"],
        boekingen_imported=d["boekingen_imported"],
    )


def parse_match_suggestion(d: dict) -> MatchSuggestion:
    d = _require_object(d, response_name="Match suggestion")
    return MatchSuggestion(
        contra_rekening_id=d["contra_rekening_id"],
        contra_rekening_code=d["contra_rekening_code"],
        contra_rekening_naam=d["contra_rekening_naam"],
        confidence=d["confidence"],
        reason=d["reason"],
    )


def parse_auto_booking_rules_export(payload: object) -> AutoBookingRulesExport:
    d = _require_object(payload, response_name="Auto-booking rules export")
    return AutoBookingRulesExport.from_dict(d)


def parse_auto_booking_rules_import_result(
    payload: object,
) -> AutoBookingRulesImportResult:
    d = _require_object(payload, response_name="Auto-booking rules import")
    _require_keys(
        d,
        response_name="Auto-booking rules import",
        keys=("imported", "replaced_existing"),
    )
    return AutoBookingRulesImportResult(
        imported=d["imported"],
        replaced_existing=_require_bool(
            d["replaced_existing"],
            field_name="Auto-booking rules import response field 'replaced_existing'",
        ),
    )


def parse_vacuum_result(payload: object) -> VacuumResult:
    d = _require_object(payload, response_name="Vacuum")
    if "message" not in d:
        raise ValueError("Vacuum response missing required key: 'message'")
    elapsed_ms = d.get("elapsed_ms")
    if elapsed_ms is not None and not isinstance(elapsed_ms, int):
        raise ValueError("Vacuum response field 'elapsed_ms' must be an int")
    return VacuumResult(
        message=d["message"],
        elapsed_ms=elapsed_ms,
    )
