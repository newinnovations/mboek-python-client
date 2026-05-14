# mBoek Python client

A high-level, synchronous Python client library for the mBoek bookkeeping API.

## Installation

```bash
pip install mboek
```

Requires Python ≥ 3.10 and `requests`.

## Quick start

```python
from mboek import MboekClient

with MboekClient("http://localhost:3000", "admin", "geheim") as client:

    # List all company administrations
    admins = client.administraties.list()
    admin = admins[0]
    print(f"Administration: {admin.naam}  (id={admin.id})")

    # Scope all further calls to one administration
    a = client.administratie(admin.id)
    # or by name:  a = client.administratie(name=admin.naam)

    # List fiscal years
    years = a.boekjaren.list()
    boekjaar = next(y for y in years if y.status.value == "open")
    print(f"Open boekjaar: {boekjaar.naam}  ({boekjaar.start_datum} → {boekjaar.eind_datum})")

    # Get a single fiscal year (one GET request)
    bj = a.boekjaar(boekjaar.id)
    # or by name:  bj = a.boekjaar(name=boekjaar.naam)

    # List boekjaar-scoped journals
    bank = bj.dagboeken(code="BANK")[0]

    # List journal entries for the bank dagboek in this boekjaar
    entries = bank.boekingen.list()
    for entry in entries[:5]:
        print(f"  {entry.boeking.datum}  {entry.boeking.omschrijving}")

    # Generate a balance sheet
    balans = bj.reports.balans()
    print(f"Activa: {balans.totaal_activa}  Passiva: {balans.totaal_passiva}  In balans: {balans.in_balans}")
```

## API hierarchy

Resources are accessed through a scoped hierarchy that mirrors the domain model:

```text
MboekClient
├── administraties            ← cross-administration resources
├── boekingen                 ← get / update / delete by ID
├── export_import             ← import_administratie / import_administratie_xaf
├── maintenance               ← database vacuum
└── administratie(id|name=)  →  AdministratieScope
    ├── boekjaren             ← fiscal years (CRUD + open/close)
    ├── dagboeken             ← journals (CRUD + werkstatus)
    ├── grootboekrekeningen   ← chart of accounts (CRUD + balances + ledger)
    ├── btw_codes             ← VAT codes (CRUD)
    ├── auto_booking_rules    ← automatic booking rules (CRUD)
    ├── import_               ← bank statement upload
    ├── export_import         ← JSON export/import + XAF export/import
    ├── dagboek(id|name=|code=)  →  Dagboek  (rich domain object, no boekjaar scope)
    │   ├── naam, code, dagboek_type, …  ← always available
    │   ├── rerun_regels()
    │   ├── suggest(omschrijving, ...)
    │   ├── import_boekingen(exported_boekingen, boekjaar_id=...)
    │   └── with_boekjaar(id=|name=)  →  Dagboek  (boekjaar-scoped)
    │       └── boekingen     ← list / create
    └── boekjaar(id|name=)  →  Boekjaar  (rich domain object)
        ├── naam, start_datum, eind_datum, status, …  ← always available
        ├── reports                   ← balance sheet and P&L
        ├── btw_aangifte              ← quarterly VAT returns
        ├── grootboekrekeningen()     ← all accounts with balance for this year
        ├── grootboekrekening(code=)  ← single account with balance, by code
        ├── dagboeken()               ← all journals scoped to this year
        └── dagboek(id|name=|code=)  →  Dagboek  (boekjaar-scoped)
            └── boekingen     ← list / create
```

## Unified domain objects

`Dagboek`, `Grootboekrekening`, and `Boekjaar` are *rich domain objects*: they
always carry all data attributes **and** optionally hold a boekjaar scope that
unlocks additional operations.  Every code path returns the same type:

```python
# Both paths return a Dagboek with .naam, .code, .dagboek_type, etc.
dagboek = client.administratie(name="Demo BV").dagboeken.list(code="BTW")[0]
dagboek = client.administratie(name="Demo BV").boekjaar(name="2026").dagboek(code="BTW")

# Both expose .naam (previously the second path had no .naam!)
print(dagboek.naam)
```

### Adding / removing boekjaar scope

```python
# Obtained without scope — data attributes work, boekingen raises ScopeError
dagboek = admin.dagboeken.list(code="BANK")[0]
print(dagboek.naam)           # ✓ always works
dagboek.boekingen.list()      # ✗ raises ScopeError

# Add scope — returns a new object (original is not mutated)
scoped = dagboek.with_boekjaar(id=10)
scoped.boekingen.list()       # ✓ works

# Or look up the boekjaar by name
scoped = dagboek.with_boekjaar(name="2026")

# Remove scope
unscoped = scoped.without_boekjaar()
```

The same pattern applies to `Grootboekrekening.saldo`:

```python
gbr = admin.grootboekrekeningen.list(code=1220)[0]
gbr.saldo                            # ✗ raises ScopeError — no boekjaar
gbr.with_boekjaar(id=10).saldo  # ✓ lazily fetched and cached
```

### ScopeError

`ScopeError` (a subclass of `ValueError`) is raised when a scope-dependent
method is called without the required scope context.  Import it from `mboek`:

```python
from mboek import ScopeError
```

## Environment variables

| Variable         | Description             | Default                 |
| ---------------- | ----------------------- | ----------------------- |
| `MBOEK_URL`      | Backend base URL        | `http://localhost:3000` |
| `MBOEK_USERNAME` | Username for auto-login | *(none)*                |
| `MBOEK_PASSWORD` | Password for auto-login | *(none)*                |

```python
# No arguments needed when env vars are set
with MboekClient() as client:
    admins = client.administraties.list()
```

Explicitly-passed constructor arguments always override env vars.

## Authentication

```python
# Option 1: pass credentials to the constructor (recommended)
client = MboekClient("http://localhost:3000", "admin", "geheim")

# Option 2: use environment variables (MBOEK_URL, MBOEK_USERNAME, MBOEK_PASSWORD)
client = MboekClient()

# Option 3: call login() manually
client = MboekClient("http://localhost:3000")
client.login("admin", "geheim")

# Always call logout() when done (or use the context manager)
client.logout()
```

## Filtering list results

List-based resources support exact-match filters and always return lists.
Common filters are `id=`, `name=`, and `code=` when those fields exist.
Scoped `boekingen.list()` also supports `item=` (for `stuknummer`) and
`description=` (for `omschrijving`).

List-style methods now auto-paginate through backend pages by default, so the
high-level client still returns complete collections unless you explicitly pass
`limit=` and/or `offset=` to request a slice.

```python
a = client.administratie(1)

# Filter fiscal years by name
boekjaar = a.boekjaren.list(name="2024")[0]

# Filter journals by name or short code (code comparison is case-insensitive)
bank = a.dagboeken.list(name="Bankboek")[0]
bank = a.dagboeken.list(code="bank")[0]   # matches "BANK"

# Filter a general-ledger account by name or account code
rekening = a.grootboekrekeningen.list(name="Bank")[0]
rekening = a.grootboekrekeningen.list(code=1220)[0]

# Filter a VAT code by its short code (case-insensitive)
btw = a.btw_codes.list(code="v21")[0]    # matches "V21"

# Filter scoped boekingen by boekstuknummer or description
boekingen = a.boekjaar(name="2024").dagboek(code="BANK").boekingen.list(item="INV-42")
boekingen = a.boekjaar(name="2024").dagboek(code="BANK").boekingen.list(description="Factuur 42")

# Request an explicit slice instead of the full collection
eerste_100 = a.dagboeken.list(limit=100)
volgende_100 = a.dagboeken.list(limit=100, offset=100)
```

The scope factory methods also accept a `name` (or `code`) keyword as a
shorthand. A lookup request is performed and the result must be unique:

- `NotFoundError` is raised when nothing matches
- `ValueError` is raised when more than one item matches

```python
# Scope by name instead of ID — performs one list lookup per call
admin = client.administratie(name="Demo BV")
bj    = admin.boekjaar(name="2024")      # one GET /boekjaren/list call
d     = bj.dagboek(name="Bankboek")     # one GET /dagboeken/list call
d     = bj.dagboek(code="BANK")         # case-insensitive

# Chained form (each name= or ID triggers at most one HTTP call)
entries = (
    client.administratie(name="Demo BV")
          .boekjaar(name="2024")
          .dagboek(code="BANK")
          .boekingen.list()
)
```

> **Note:** `admin.boekjaar(10)` and `admin.dagboek(20)` always make one GET
> request (even when passing a numeric ID) so that the returned object is
> fully-populated with all data attributes.

## Grootboekrekeningen per boekjaar

Use `Boekjaar.grootboekrekeningen()` to list all accounts enriched with the
transaction count and net balance for a specific fiscal year.
Each item exposes `.code`, `.naam`, `.transacties`, and `.saldo` as flat attributes.

```python
bj = client.administratie(name="Demo BV").boekjaar(name="2026")

# Iterate all accounts with their year-to-date balance
for rekening in bj.grootboekrekeningen():
    print(rekening.code, rekening.naam, rekening.transacties, rekening.saldo)

# Look up a single account by code — raises NotFoundError when not found
rekening = bj.grootboekrekening(code=4000)
print("Saldo 4000:", rekening.saldo)
```

## Creating a journal entry

All boekingsregels must balance (`sum(bedrag) == 0`).
Amounts are in **euros** — the library converts to/from cents automatically.
`bedrag` must have at most 2 decimal places; `Decimal("1.005")` raises `ValueError`.

BTW lines (`regeltype=Regeltype.BTW_INPUT` or `BTW_OUTPUT`) **must** include a
`netto_ref` pointing to the index (0-based) of the corresponding netto regel.

```python
from decimal import Decimal
from datetime import date
from mboek import NewBoekingsregel, Regeltype

regels = [
    NewBoekingsregel(
        grootboekrekening_id=bank_account_id,
        omschrijving="Bank outflow",
        bedrag=Decimal("-121.00"),   # credit the bank account
    ),
    NewBoekingsregel(
        grootboekrekening_id=kosten_id,
        omschrijving="Hosting",
        bedrag=Decimal("100.00"),    # debit costs (netto)
        btw_code_id=btw_i21_id,
        regeltype=Regeltype.NETTO,
    ),
    NewBoekingsregel(
        grootboekrekening_id=btw_vorderen_id,
        omschrijving="BTW",
        bedrag=Decimal("21.00"),     # debit VAT receivable
        regeltype=Regeltype.BTW_INPUT,
        netto_ref=1,                 # index of the netto regel above
    ),
]

bj_dagboek = client.administratie(admin_id).boekjaar(boekjaar_id).dagboek(bank_dagboek_id)
entry = bj_dagboek.boekingen.create(
    regels=regels,
    datum=date(2024, 3, 15),
    omschrijving="Hosting invoice March",
    # boekjaar_id is injected automatically from the scope
)
print(f"Created boeking {entry.boeking.id}")
```

Alternatively, you can reference accounts by **name or code** instead of a
numeric ID — the library resolves them automatically (with caching):

```python
regels = [
    NewBoekingsregel(grootboekrekening_code=1220, omschrijving="Bank", bedrag=Decimal("-100.00")),
    NewBoekingsregel(grootboekrekening_naam="Kosten internet", omschrijving="Hosting", bedrag=Decimal("100.00")),
]
```

## Updating and deleting a journal entry

Every `Boeking` returned from the API carries a client reference, so you can
call `update()` and `delete()` directly on the object — no need to go through
`client.boekingen` again.

```python
# Retrieve a single entry by ID
boeking = client.boekingen.get(100)

# Update header fields (pass only the fields you want to change)
updated = boeking.update(
    omschrijving="Corrected description",
    gecontroleerd=True,
)
print(updated.omschrijving)   # "Corrected description"

# Entries returned from list() are also scoped
entries = (
    client.administratie(admin_id)
          .boekjaar(boekjaar_id)
          .dagboek(dagboek_id)
          .boekingen.list()
)
for entry in entries:
    if entry.omschrijving == "WRONG":
        entry.delete()
```

`update()` accepts the same keyword arguments as `BoekingenResource.update()`
(all optional): `datum`, `omschrijving`, `stuknummer`, `status`,
`tegenpartij_naam`, `tegenpartij_iban`, `gecontroleerd`, `auto_geboekt`, and
`regels` (full replacement set of boekingsregels).  It returns a fresh
`Boeking` with the updated data. Pass `None` explicitly to clear a nullable
field; omit a keyword to leave it unchanged.

`delete()` permanently removes the boeking and all its boekingsregels.

Both methods raise `ScopeError` when called on a `Boeking` that was not
obtained via a live client (e.g. built manually or deserialised from a backup).

## Setting up a new administration

```python
from datetime import date

# 1. Create the administration
admin = client.administraties.create(naam="My Company BV", btw_nummer="NL123456789B01")
a = client.administratie(admin.id)

# 2. Seed the standard Dutch chart of accounts
a.grootboekrekeningen.seed_rgs()

# 3. Seed the standard Dutch BTW (VAT) codes
a.btw_codes.seed_defaults()

# 4. Create a fiscal year
boekjaar = a.boekjaren.create(
    naam="2024",
    start_datum=date(2024, 1, 1),
    eind_datum=date(2024, 12, 31),
)

# 5. Set it as the current/active year
a.boekjaren.set_huidig(boekjaar.id)
```

## BTW-aangifte (VAT return) workflow

```python
bj = client.administratie(admin_id).boekjaar(boekjaar_id)

# 1. Calculate the Q1 VAT return (creates a concept)
aangifte = bj.btw_aangifte.berekenen(kwartaal=1)
print(f"Q1 VAT: {aangifte.r5g}")   # positive = te betalen, negative = te ontvangen

# 2. Close the fiscal year (required before vastleggen)
client.administratie(admin_id).boekjaren.afsluiten(boekjaar_id)

# 3. Lock the aangifte and create the balancing boeking
definitief = bj.btw_aangifte.vastleggen(aangifte.id)
```

## Bank statement import

```python
from pathlib import Path

result = client.administratie(admin_id).import_.upload(
    Path("afschrift-jan.940"),
    allow_duplicates=True,
)
print(f"Imported {result.imported} transactions")
print(
    "Skipped",
    result.duplicates_skipped,
    "duplicates and",
    result.zero_bedrag_skipped,
    "zero-amount transactions",
)
if result.unmatched_ibans:
    print("No dagboek matched:", ", ".join(result.unmatched_ibans))
if result.parse_warnings:
    print("Warnings:", result.parse_warnings)
```

## Export and import

```python
import json
from pathlib import Path

from mboek import AdministratieExport, BoekjaarExport

a = client.administratie(admin_id)

# Full export to a JSON file
payload = a.export_import.export_administratie()
with open("backup.json", "w") as f:
    json.dump(payload.to_dict(), f, indent=2)

# Export a single boekjaar
bj_payload = a.export_import.export_boekjaar(boekjaar_id)

# Restore a full backup into a new administration
with open("backup.json") as f:
    payload = AdministratieExport.from_dict(json.load(f))
result = client.export_import.import_administratie(payload, overwrite=True)
print(result.administratie_id, result.boekingen_imported)

# Export the full administration as Auditfile Financieel (XAF)
admin_xaf = a.export_import.export_administratie_xaf()
Path("administratie.xaf").write_text(admin_xaf, encoding="utf-8")

# Export a single boekjaar as Auditfile Financieel (XAF)
xaf_xml = a.export_import.export_boekjaar_xaf(boekjaar_id)
Path("boekjaar-2024.xaf").write_text(xaf_xml, encoding="utf-8")

# Import a XAF file into an existing administration
result = a.export_import.import_boekjaar_xaf(
    Path("boekjaar-2024.xaf"),
    create_missing=True,
)
print(result.boekjaar_id, result.boekingen_imported)

# Load a boekjaar JSON export from disk before importing it elsewhere
target_admin = client.administratie(other_admin_id)
with open("boekjaar-2024.json") as f:
    boekjaar_payload = BoekjaarExport.from_dict(json.load(f))
result = target_admin.export_import.import_boekjaar(boekjaar_payload)
print(result.boekjaar_id, result.boekingen_imported)

# Or create a brand-new administration directly from a XAF file
client.export_import.import_administratie_xaf(
    Path("boekjaar-2024.xaf"),
    overwrite=True,
    create_missing=True,
)

# Non-UTF-8 XAF files are normalized to UTF-8 automatically before upload.
```

## Automatic booking rules

```python
from decimal import Decimal

from mboek import AutoBookingActieType, AutoBookingBedragType, NewAutoBookingRuleLine

a = client.administratie(admin_id)

rule = a.auto_booking_rules.create(
    naam="Hosting Duitsland",
    actie_type=AutoBookingActieType.SPLITS,
    iban_tegenpartij="DE75512308000000060004",
    lines=[
        NewAutoBookingRuleLine(
            tegenrekening_code=4000,
            bedrag_type=AutoBookingBedragType.VAST,
            bedrag=Decimal("12.34"),
        ),
        NewAutoBookingRuleLine(
            tegenrekening_code=9990,
            bedrag_type=AutoBookingBedragType.REST,
        ),
    ],
)
# bedragen are passed in euros; the client serializes them as integer cents.

applied = a.auto_booking_rules.apply_to_boeking(boeking_id)
print(applied.matched, applied.reason)

# Ask the backend for matching contra-accounts
suggestions = a.dagboek(bank_dagboek_id).suggest(
    "SEPA INCASSO HOSTING GMBH",
    tegenpartij_naam="Hosting GmbH",
)
print(suggestions[0].contra_rekening_code, suggestions[0].confidence, suggestions[0].reason)

# Import exported boekingen into a dagboek + boekjaar
# exported_boekingen should be a list[BoekingExport]
result = a.dagboek(bank_dagboek_id).import_boekingen(
    exported_boekingen,
    boekjaar_id=boekjaar_id,
)
print(result.dagboek_id, result.boekingen_imported)

# Re-apply all rules to unprocessed entries in a dagboek (year-agnostic).
# The method returns the number of updated boekingen.
updated = a.dagboek(bank_dagboek_id).rerun_regels()
print(f"Auto-booked {updated} entries")
```

## Reports

```python
bj = client.administratie(admin_id).boekjaar(boekjaar_id)

# Balance sheet
balans = bj.reports.balans()
print(f"Activa: {balans.totaal_activa}  Passiva: {balans.totaal_passiva}")
print(f"In balans: {balans.in_balans}")

# Profit & loss
wv = bj.reports.winst_verlies()
print(f"Netto resultaat: {wv.netto_resultaat}")
```

## Error handling

```python
from mboek import (
    AuthError,         # 401 Unauthorized
    ForbiddenError,    # 403 Forbidden
    NotFoundError,     # 404 Not Found
    ConflictError,     # 409 Conflict
    ValidationError,   # 422 Unprocessable Entity
    RateLimitError,    # 429 Too Many Requests
    ScopeError,        # scope-dependent method called without required scope
    MboekError,        # base for all API errors
)

try:
    client.administratie(admin_id).boekjaren.afsluiten(boekjaar_id)
except ConflictError as e:
    print(f"Cannot close: {e}")   # e.g. already closed
except NotFoundError:
    print("Boekjaar not found")
```

All HTTP exceptions expose:

- `e.status_code` — HTTP status code
- `e.detail` — parsed response body, response text, or the underlying transport/parsing error

`ScopeError` (a subclass of `ValueError`) is raised when a scope-dependent
method is called without the required scope context and has no `status_code`.

`MboekError` is also the base class for transport failures and malformed JSON
responses, so `except MboekError` is the catch-all for client-side request /
response failures.

## Dutch accounting glossary

| Dutch term              | English equivalent                         |
| ----------------------- | ------------------------------------------ |
| Administratie           | Company administration / set of books      |
| Boekjaar                | Fiscal / financial year                    |
| Dagboek                 | Journal / sub-ledger                       |
| Grootboekrekening       | General-ledger account                     |
| Boeking                 | Journal entry                              |
| Boekingsregel           | Journal entry line                         |
| BTW                     | VAT (value-added tax)                      |
| BTW-aangifte            | VAT return (quarterly)                     |
| Netto bedrag            | Net amount (excluding VAT)                 |
| Te betalen BTW          | Output VAT (VAT payable to the tax office) |
| Te vorderen BTW         | Input VAT (VAT reclaimable)                |
| Balans                  | Balance sheet                              |
| Winst & verlies         | Profit & loss statement                    |
| Activa                  | Assets                                     |
| Passiva                 | Liabilities + equity                       |
| Kosten                  | Costs / expenses                           |
| Opbrengsten             | Revenues                                   |
| Debet                   | Debit                                      |
| Credit                  | Credit                                     |
| Saldo                   | Balance                                    |
| Stuknummer              | Document / invoice reference number        |
| Tegenpartij             | Counterparty                               |
| Banktransacties         | Bank transactions                          |
| Automatische boekregels | Automatic booking rules                    |

## Development

```bash
git clone https://github.com/newinnovations/mboek-python-client.git
cd mboek-python-client
uv venv
uv pip install -e ".[dev]"
uv run pytest
```
