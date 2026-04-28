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

    # Scope to a specific boekjaar
    bj = a.boekjaar(boekjaar.id)
    # or by name:  bj = a.boekjaar(name=boekjaar.naam)

    # List journals
    dagboeken = a.dagboeken.list()
    bank = next(d for d in dagboeken if d.dagboek_type.value == "bank")

    # List journal entries for the bank dagboek in this boekjaar
    entries = bj.dagboek(bank.id).boekingen.list()
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
├── export_import             ← import_administratie
├── maintenance               ← database vacuum
└── administratie(id|name=)  →  AdministratieScope
    ├── boekjaren             ← fiscal years (CRUD + open/close)
    ├── dagboeken             ← journals (CRUD + werkstatus)
    ├── grootboekrekeningen   ← chart of accounts (CRUD + balances + ledger)
    ├── btw_codes             ← VAT codes (CRUD)
    ├── auto_booking_rules    ← automatic booking rules (CRUD)
    ├── import_               ← bank statement upload
    ├── export_import         ← full export / boekjaar export / import
    ├── dagboek(id|name=|code=)  →  DagboekScope   (year-agnostic ops)
    │   ├── rerun_regels()
    │   ├── suggest(boeking_id)
    │   └── import_boekingen(boekingen)
    └── boekjaar(id|name=)  →  BoekjaarScope
        ├── reports                   ← balance sheet and P&L
        ├── btw_aangifte              ← quarterly VAT returns
        ├── grootboekrekeningen()     ← all accounts with balance for this year
        ├── grootboekrekening(code=)  ← single account with balance, by code
        └── dagboek(id|name=|code=)  →  BoekjaarDagboekScope
            └── boekingen     ← list / create
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

## Finding resources by name or code

Every list-based resource exposes `find_by_naam()` and/or `find_by_code()` as a
convenience. All return `None` when not found.

```python
a = client.administratie(admin_id)

# Find a fiscal year by name
boekjaar = a.boekjaren.find_by_naam("2024")

# Find a journal by name or short code (code comparison is case-insensitive)
bank = a.dagboeken.find_by_naam("Bankboek")
bank = a.dagboeken.find_by_code("bank")   # matches "BANK"

# Find a general-ledger account by name or account code
rekening = a.grootboekrekeningen.find_by_naam("Bank")
rekening = a.grootboekrekeningen.find_by_code("1220")

# Find a VAT code by its short code (case-insensitive)
btw = a.btw_codes.find_by_code("v21")    # matches "V21"
```

The scope factory methods also accept a `name` (or `code`) keyword as a
shorthand. A lookup request is performed and `NotFoundError` is raised when
nothing is found:

```python
# Scope by name instead of ID — performs one list lookup per call
admin = client.administratie(name="Demo BV")
bj    = admin.boekjaar(name="2024")
scope = bj.dagboek(name="Bankboek")
scope = bj.dagboek(code="BANK")  # case-insensitive

# Chained form (each name= triggers one HTTP call)
entries = (
    client.administratie(name="Demo BV")
          .boekjaar(name="2024")
          .dagboek(code="BANK")
          .boekingen.list()
)
```

## Grootboekrekeningen per boekjaar

Use `BoekjaarScope.grootboekrekeningen()` to list all accounts enriched with the
transaction count and net balance for a specific fiscal year.
Each item exposes `.code`, `.naam`, `.transacties`, and `.saldo` as flat attributes.

```python
bj = client.administratie(name="Demo BV").boekjaar(name="2026")

# Iterate all accounts with their year-to-date balance
for rekening in bj.grootboekrekeningen():
    print(rekening.code, rekening.naam, rekening.transacties, rekening.saldo)

# Look up a single account by code — raises NotFoundError when not found
rekening = bj.grootboekrekening(code="4000")
print("Saldo 4000:", rekening.saldo)
```

## Creating a journal entry

All boekingsregels must balance (`sum(bedrag) == 0`).
Amounts are in **euros** — the library converts to/from cents automatically.

```python
from decimal import Decimal
from datetime import date
from mboek import NewBoeking, NewBoekingsregel, Regeltype

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
        regeltype=Regeltype.BTW,
        netto_ref=1,                 # index of the netto regel above
    ),
]

bj_dagboek = client.administratie(admin_id).boekjaar(boekjaar_id).dagboek(bank_dagboek_id)
entry = bj_dagboek.boekingen.create(
    NewBoeking(
        datum=date(2024, 3, 15),
        omschrijving="Hosting invoice March",
        regels=regels,
        # boekjaar_id is injected automatically from the scope
    )
)
print(f"Created boeking {entry.boeking.id}")
```

Alternatively, you can reference accounts by **name or code** instead of a
numeric ID — the library resolves them automatically (with caching):

```python
regels = [
    NewBoekingsregel(grootboekrekening_code="1220", omschrijving="Bank", bedrag=Decimal("-100.00")),
    NewBoekingsregel(grootboekrekening_naam="Kosten internet", omschrijving="Hosting", bedrag=Decimal("100.00")),
]
```

## Setting up a new administration

```python
from datetime import date
from mboek import NewAdministratie, NewBoekjaar

# 1. Create the administration
admin = client.administraties.create(
    NewAdministratie(naam="My Company BV", btw_nummer="NL123456789B01")
)
a = client.administratie(admin.id)

# 2. Seed the standard Dutch chart of accounts
a.grootboekrekeningen.seed_rgs()

# 3. Seed the standard Dutch BTW (VAT) codes
a.btw_codes.seed_defaults()

# 4. Create a fiscal year
boekjaar = a.boekjaren.create(
    NewBoekjaar(
        naam="2024",
        start_datum=date(2024, 1, 1),
        eind_datum=date(2024, 12, 31),
    )
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

result = client.administratie(admin_id).import_.upload(Path("afschrift-jan.940"))
print(f"Imported {result.imported} transactions, skipped {result.skipped} duplicates")
```

## Export and import

```python
import json

a = client.administratie(admin_id)

# Full export to a JSON file
payload = a.export_import.export_administratie()
with open("backup.json", "w") as f:
    json.dump(payload, f, indent=2)

# Export a single boekjaar
bj_payload = a.export_import.export_boekjaar(boekjaar_id)

# Restore a full backup into a new administration
with open("backup.json") as f:
    payload = json.load(f)
client.export_import.import_administratie(payload)
```

## Automatic booking rules

```python
from mboek import NewAutoBookingRule

a = client.administratie(admin_id)

rule = a.auto_booking_rules.create(
    NewAutoBookingRule(
        naam="Hosting Duitsland",
        actie_type="enkel",
        tegenpartij_iban_patroon="DE75512308000000060004",
        lines=[...],
    )
)

# Re-apply all rules to unprocessed entries in a dagboek (year-agnostic)
updated = a.dagboek(bank_dagboek_id).rerun_regels()
print(f"Auto-booked {len(updated)} entries")
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
    MboekError,        # base for all API errors
)

try:
    client.administratie(admin_id).boekjaren.afsluiten(boekjaar_id)
except ConflictError as e:
    print(f"Cannot close: {e}")   # e.g. already closed
except NotFoundError:
    print("Boekjaar not found")
```

All exceptions expose:

- `e.status_code` — HTTP status code
- `e.detail` — parsed response body (dict or str)

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
