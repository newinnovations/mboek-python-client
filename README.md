# Python mBoek client

A high-level, synchronous Python client library for the mBoek bookkeeping API.

## Installation

```bash
pip install mboek
# or from source:
pip install -e /path/to/python-mboek-client
```

Requires Python ≥ 3.10 and `requests`.

## Quick start

```python
from mboek import MboekClient

# Auto-login, auto-logout via context manager
with MboekClient("http://localhost:3000", "admin", "geheim") as client:

    # List all company administrations
    admins = client.administraties.list()
    admin = admins[0]
    print(f"Administration: {admin.naam}  (id={admin.id})")

    # List fiscal years
    years = client.boekjaren.list(admin.id)
    boekjaar = next(y for y in years if y.status.value == "open")
    print(f"Open boekjaar: {boekjaar.naam}  ({boekjaar.start_datum} → {boekjaar.eind_datum})")

    # List journals
    dagboeken = client.dagboeken.list(admin.id)
    bank = next(d for d in dagboeken if d.dagboek_type.value == "bank")

    # List journal entries
    boekingen = client.boekingen.list(dagboek_id=bank.id, boekjaar_id=boekjaar.id)
    for entry in boekingen[:5]:
        print(f"  {entry.boeking.datum}  {entry.boeking.omschrijving}")

    # Generate a balance sheet
    balans = client.reports.balans(admin.id, boekjaar.id)
    print(f"Activa: {balans.totaal_activa}  Passiva: {balans.totaal_passiva}  In balans: {balans.in_balans}")
```

## Environment variables

You can configure the client entirely through environment variables — useful for
scripts, CI, and twelve-factor apps:

| Variable         | Description             | Default                 |
| ---------------- | ----------------------- | ----------------------- |
| `MBOEK_URL`      | Backend base URL        | `http://localhost:3000` |
| `MBOEK_USERNAME` | Username for auto-login | *(none)*                |
| `MBOEK_PASSWORD` | Password for auto-login | *(none)*                |

```bash
export MBOEK_URL=http://mboek.example.com
export MBOEK_USERNAME=admin
export MBOEK_PASSWORD=geheim
```

```python
# No arguments needed — reads from environment
with MboekClient() as client:
    admins = client.administraties.list()
```

Explicitly-passed constructor arguments always override the environment variables.

## Authentication

All endpoints except `/api/auth/login` require a JWT bearer token. The client manages
the token transparently:

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
convenience over `list()` + filtering yourself. All return `None` when not found.

```python
# Find an administration by name
admin = client.administraties.find_by_naam("My Company BV")

# Find a fiscal year by name
boekjaar = client.boekjaren.find_by_naam(admin.id, "2024")

# Find a journal by name or short code (code comparison is case-insensitive)
bank = client.dagboeken.find_by_naam(admin.id, "Bankboek")
bank = client.dagboeken.find_by_code(admin.id, "bank")   # matches "BANK"

# Find a general-ledger account by name or account code
rekening = client.grootboekrekeningen.find_by_naam(admin.id, "Bank")
rekening = client.grootboekrekeningen.find_by_code(admin.id, "1220")

# Find a VAT code by its short code (case-insensitive)
btw = client.btw_codes.find_by_code(admin.id, "v21")     # matches "V21"
```

## Creating a journal entry

All boekingsregels must balance (`sum(bedrag) == 0`).
Amounts are in **euros** (the library converts to/from cents automatically).

```python
from decimal import Decimal
from datetime import date
from mboek import CreateBoekingInput, CreateBoekingsregelInput

regels = [
    CreateBoekingsregelInput(
        grootboekrekening_id=bank_account_id,
        omschrijving="Bank outflow",
        bedrag=Decimal("-121.00"),   # credit the bank account
    ),
    CreateBoekingsregelInput(
        grootboekrekening_id=kosten_id,
        omschrijving="Hosting",
        bedrag=Decimal("100.00"),    # debit costs (netto)
        btw_code_id=btw_i21_id,
        regeltype=Regeltype.NETTO,
    ),
    CreateBoekingsregelInput(
        grootboekrekening_id=btw_vorderen_id,
        omschrijving="BTW",
        bedrag=Decimal("21.00"),     # debit VAT receivable
        regeltype=Regeltype.BTW,
        netto_ref=1,                 # index of the netto regel above
    ),
]

entry = client.boekingen.create(
    dagboek_id=bank_dagboek_id,
    input=CreateBoekingInput(
        datum=date(2024, 3, 15),
        omschrijving="Hosting invoice March",
        boekjaar_id=boekjaar_id,
        regels=regels,
    ),
)
print(f"Created boeking {entry.boeking.id}")
```

## Setting up a new administration

```python
from datetime import date
from mboek import CreateAdministratieInput, CreateBoekjaarInput

# 1. Create the administration
admin = client.administraties.create(
    CreateAdministratieInput(naam="My Company BV", btw_nummer="NL123456789B01")
)

# 2. Seed the standard Dutch chart of accounts
client.grootboekrekeningen.seed_rgs(admin.id)

# 3. Seed the standard Dutch BTW (VAT) codes
client.btw_codes.seed_defaults(admin.id)

# 4. Create a fiscal year
boekjaar = client.boekjaren.create(
    admin.id,
    CreateBoekjaarInput(
        naam="2024",
        start_datum=date(2024, 1, 1),
        eind_datum=date(2024, 12, 31),
    ),
)

# 5. Set it as the current/active year
client.boekjaren.set_huidig(admin.id, boekjaar.id)
```

## BTW-aangifte (VAT return) workflow

```python
# 1. Calculate the Q1 VAT return (creates a concept)
aangifte = client.btw_aangifte.berekenen(admin.id, boekjaar_id=boekjaar.id, kwartaal=1)
print(f"Q1 VAT: {aangifte.r5g}")   # positive = te betalen, negative = te ontvangen

# 2. Close the fiscal year (required before vastleggen)
client.boekjaren.afsluiten(admin.id, boekjaar.id)

# 3. Lock the aangifte and create the balancing boeking
definitief = client.btw_aangifte.vastleggen(admin.id, aangifte.id)
```

## Bank statement import

```python
from pathlib import Path

result = client.import_.upload(admin.id, Path("afschrift-jan.940"))
print(f"Imported {result.imported} transactions, skipped {result.skipped} duplicates")
```

## Export and import

```python
# Full export to a JSON file
import json
payload = client.export_import.export_administratie(admin.id)
with open("backup.json", "w") as f:
    json.dump(payload, f, indent=2)

# Restore from backup
with open("backup.json") as f:
    payload = json.load(f)
client.export_import.import_administratie(payload)
```

## Automatic booking rules

```python
from mboek import CreateAutoBookingRuleInput, CreateAutoBookingRuleLineInput
from mboek.models._enums import AutoBookingActieType, AutoBookingBedragType

rule = client.auto_booking_rules.create(
    admin.id,
    CreateAutoBookingRuleInput(
        naam="Hetzner hosting",
        actie_type=AutoBookingActieType.ENKEL,
        tegenpartij_iban_patroon="DE75512308000000060004",
        lines=[
            CreateAutoBookingRuleLineInput(
                grootboekrekening_id=hosting_rekening_id,
                btw_code_id=btw_i21_id,
                bedrag_type=AutoBookingBedragType.REST,
            )
        ],
    ),
)

# Re-apply all rules to unprocessed entries in a dagboek
updated = client.auto_booking_rules.rerun(admin.id, bank_dagboek_id)
print(f"Auto-booked {len(updated)} entries")
```

## API reference

### Resources

| Property                     | Description                                             |
| ---------------------------- | ------------------------------------------------------- |
| `client.administraties`      | Company administrations (CRUD)                          |
| `client.boekjaren`           | Fiscal years (CRUD + open/close/reopen)                 |
| `client.dagboeken`           | Journals / sub-ledgers (CRUD + work status)             |
| `client.grootboekrekeningen` | Chart of accounts (CRUD + seed RGS + balances + ledger) |
| `client.boekingen`           | Journal entries (CRUD)                                  |
| `client.btw_codes`           | VAT codes (CRUD + seed defaults)                        |
| `client.btw_aangifte`        | Quarterly VAT returns (calculate + lock + delete)       |
| `client.auto_booking_rules`  | Automatic booking rules (CRUD + re-run)                 |
| `client.reports`             | Balance sheet and P&L reports                           |
| `client.import_`             | Bank statement upload (MT940 / CAMT.053)                |
| `client.export_import`       | Full export / import                                    |
| `client.maintenance`         | Database vacuum                                         |

### Error handling

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
    client.boekjaren.afsluiten(admin_id, boekjaar_id)
except ConflictError as e:
    print(f"Cannot close: {e}")  # e.g. already closed
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
cd python
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```
