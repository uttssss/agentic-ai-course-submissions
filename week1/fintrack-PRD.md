# fintrack — Product Requirements Document

**Version:** 2.3  
**Status:** Draft  
**Last updated:** 2026-05-31

---

## 1. Purpose

Build a personal finance tracker that gives a single, accurate view of net worth, income, and spending across all financial accounts. The core challenge the product solves is eliminating double-counting when money moves between accounts (e.g. a credit card payment appearing both as an outflow from a bank account and as a balance reduction on the card).

---

## 2. Users

Single user (personal finance). No multi-user or sharing requirements at this stage.

---

## 3. Scope

### V0 — Browser prototype (localStorage)
The goal of V0 is to validate all UX flows and UI design before committing to a backend. Data is persisted in browser localStorage — no server, no setup. V0 is intentionally throwaway storage; the React frontend may be reused or referenced in V1 but is not required to be.

- Account management (opening balance derived from balance column in first imported row)
- CSV import with per-account tagging and format definition
- Transaction ledger with filtering, search, and manual editing
- Transfer matching (automatic + manual) to prevent double-counting
- Dashboard with net worth, net in/out, time series, and category breakdown
- All amounts in USD (single currency throughout)
- Brokerage Brokerage: CSV import with Trans Code-based type mapping
- Brokerage Roth IRA: CSV import (same format as brokerage, CFRI trans code = investment)
- Brokerage Traditional IRA: BalanceSnapshot only (empty in sample period; PDF only)
- 401K Provider (Traditional + Roth): BalanceSnapshot only, manual entry from PDF
- All other accounts (primary checking, Credit Card Provider, P2P Payment App, HSA): CSV import with format profiles defined in §4.2.3
- Deduplication of exact repeats on import (match on account + date + description + amount)
- Categories read from CSV column if present; no in-app categorisation engine
- Manual JSON export and import for localStorage backup and restore

### V1 — Streamlit + SQLite (local server)
V1 ports all logic from V0 into a Streamlit application backed by a local SQLite database. No separate API is needed — Streamlit talks to SQLite directly via Python. This gives real persistence, proper relational data model, and easy CSV/data manipulation in Python. Plotly charts carry over from the existing Streamlit prototype.

- All V0 features, now with persistent SQLite storage
- Format profiles saved per account and reused on future imports
- Deduplication on import (match on account + date + description + amount)
- Transaction batch tracking (which import session each row came from)
- Categories drawn from fixed app taxonomy (see §4.6); user pre-processes CSVs through an LLM to map to taxonomy before importing
- All amounts in USD (single currency, same as V0)

### V2 — Extended import and features
- Multi-CSV import (monthly batches per account, with deduplication)
- Excel (.xlsx) import
- PDF bank statement import (OCR-based, always requires review)
- Multi-currency support with conversion
- In-app auto-categorisation (LLM-assisted, no external pre-processing required)
- Budget targets and alerts
- Data export

---

## 4. Modules

---

### 4.1 Account Management

**Purpose:** Define all financial accounts before any data is imported. Every transaction must belong to an account.

**Accounts to support:**
- Bank accounts (current, savings)
- Credit cards
- Investment accounts
- Cash
- Loans / mortgages (negative balance)

**Fields per account:**
| Field | Type | Notes |
|---|---|---|
| Name | String | User-defined, e.g. "Monzo Current" |
| Type | Enum | bank, credit_card, investment, cash, loan |
| Currency | Enum | ISO 4217 code |
| Opening balance | Number | Balance at the point tracking begins |
| Active | Boolean | Hide closed accounts without deleting history |

**Behaviours:**
- Net worth = sum of all account balances (loans and credit card balances count as negative)
- Deleting an account is blocked if it has imported transactions; user must archive instead
- Currency conversion is out of scope for V1; all accounts assumed to share a display currency or are shown in native currency

---

### 4.2 CSV Import

**Purpose:** Ingest transaction data exported from banks and financial institutions.

#### 4.2.1 Import flow

1. User selects a target account (must exist before importing)
2. User uploads one CSV file
3. App detects the file's column structure and proposes a column mapping
4. User confirms or adjusts the mapping (date, description, amount, optional: category, balance)
5. App infers transaction direction (debit/credit) from amount sign or separate debit/credit columns
6. App auto-detects transfer candidates (see §4.4)
7. User reviews a preview of all rows with inferred types
8. User confirms import; rows are written to the transaction ledger

#### 4.2.2 CSV format definition

Because different banks export different formats, the app must let the user define and save a **format profile** per account. A format profile captures:

| Field | Description |
|---|---|
| Date column | Column name or index |
| Date format | e.g. `DD/MM/YYYY`, `YYYY-MM-DD`, `MMM DD YYYY` |
| Description column | Free-text narrative |
| Amount column | Single signed column, or separate debit/credit columns |
| Amount sign convention | Negative = debit, or Positive = debit |
| Balance column | Recommended — used to derive opening balance and validate running totals |
| Header rows to skip | Some exports have metadata rows before the header |
| Encoding | UTF-8, Latin-1, etc. |

Saved format profiles are reused on future imports from the same account, so the user only maps columns once.

**Opening balance derivation:** If a balance column is mapped, the opening balance for the account is set from the balance value in the row *before* the first imported transaction (i.e. the running balance prior to the earliest transaction in the file). If no balance column is present, the user sets the opening balance manually. The user can override the derived value at any time.

**Sample CSVs** will be attached by the user to finalise concrete format profiles for each of their banks. These will be used to build and validate the parser.

#### 4.2.3 Institution format profiles

Known format profiles for the institutions in scope. To be validated against sample CSVs before implementation.

| Institution | Account type | Date format | Amount convention | Category column | Notes |
|---|---|---|---|---|---|
| Primary Bank | Bank | MM/DD/YYYY | Negative = debit | No | Single signed amount column; has running balance column |
| Credit Card Provider | Credit card | MM/DD/YYYY | Positive = charge, negative = payment | Yes (Amex-provided) | Sign convention flipped vs bank accounts; category column used directly |
| Brokerage | Investment | YYYY-MM-DD | Signed | No | Type column distinguishes buy/sell/dividend/transfer; dividends → income, buys/sells → investment type |
| 401K / HSA | Investment | Varies by provider | Signed or snapshot | No | May be balance snapshots rather than transaction ledgers; treated as balance snapshot records for net worth purposes |
| P2P Payment App | Payment | YYYY-MM-DD | Positive = received, negative = sent | No | Note field used as description; outgoing payments default to expense type; user can reclassify as transfer |

#### 4.2.4 V2: multi-file import

Allow multiple CSVs to be uploaded in one import session for the same account (e.g. one file per month). The app deduplicates rows by matching on date + description + amount before writing, so overlapping exports do not create duplicate transactions.

#### 4.2.5 V2: Excel and PDF import

- Excel: read the first sheet (or let user select sheet); apply same column mapping flow
- PDF: OCR-based extraction for bank statement PDFs; lower confidence, always requires user review before import

---

### 4.3 Transaction Ledger

**Purpose:** A single unified view of all transactions across all accounts, with the ability to filter, search, and manually edit.

#### 4.3.1 Columns displayed

| Column | Notes |
|---|---|
| Date | Sortable |
| Description | Raw bank text; editable |
| Account | Which account this row belongs to |
| Category | User-assigned or auto-suggested |
| Amount | Signed; shown in account currency |
| Type | expense / income / transfer / investment |
| Match status | Unmatched / matched (for transfers) |

#### 4.3.2 Filters

- **Date range** — preset options (this month, last 3 months, this year, custom)
- **Account** — multi-select
- **Type** — expense / income / transfer / all
- **Category** — multi-select
- **Match status** — matched / unmatched / all

#### 4.3.3 Search

Free-text search across description field. Matches substring, case-insensitive.

#### 4.3.4 Manual operations

- **Edit** any field on any row (description, category, date, amount, type)
- **Add** a transaction manually (for cash or unimported items)
- **Delete** a transaction (with confirmation)
- **Split** a transaction into two rows with different categories (e.g. a supermarket shop split between food and household)

---

### 4.4 Transfer Matching

**Purpose:** When the user pays their credit card from their bank account, this creates two transactions — an outflow from the bank and a corresponding inflow (or balance reduction) on the card. Both are real movements of money but together they net to zero real expenditure. Matching links these two rows so dashboards exclude them from net spend.

#### 4.4.1 Automatic matching

Auto-matching runs silently on every import. No user confirmation is required. Two transactions are auto-matched as a transfer pair when:
- Absolute amounts are within tolerance: difference < $5.00 or < 0.5% of the larger amount, whichever is greater
- Dates are within a configurable window (default: 5 calendar days)
- One transaction is an outflow from one account and the other is an inflow to a different account
- Neither transaction is already matched

Matches are applied immediately and reflected in all dashboard figures without any confirmation step.

#### 4.4.2 Surfacing matches

Auto-matched pairs are visible and auditable in the transaction ledger:
- Matched rows are labelled as type = "transfer" with a link icon indicating the paired transaction
- The ledger can be filtered to show only transfers, making the full set of matches easy to review
- A dedicated **Matches** view (or ledger filter) lists all matched pairs side-by-side for quick scanning

#### 4.4.3 Undoing a match

The user can unmatch any auto-matched pair at any time:
- Unmatching restores both transactions to their original inferred types (expense / income)
- Both rows re-enter the net in / net out calculations immediately
- No confirmation dialog — the action is immediately applied and can be re-matched manually if undone by mistake

#### 4.4.4 Manual matching

The user can manually link any two unmatched transactions as a transfer pair:
- Select two transactions in the ledger (one outflow, one inflow) and apply "match as transfer"
- Manually matched pairs behave identically to auto-matched ones
- Manual matches can also be undone via the same unmatch action

#### 4.4.5 Effect on reporting

- Matched transfer pairs are excluded from net income and net expenditure calculations
- They remain visible in the ledger as type = "transfer" and can be filtered in/out
- Net worth is always calculated from account balances directly, so transfers do not affect it either way

---

### 4.5 Transaction Types

Every transaction has exactly one type. Type determines how it is counted in dashboard figures.

| Type | Description | Net in | Net out | Net worth |
|---|---|---|---|---|
| expense | Money genuinely spent (groceries, bills, P2P payments sent) | — | ✓ counted | Via account balance |
| income | Money genuinely received (salary, brokerage dividends, P2P payments received) | ✓ counted | — | Via account balance |
| transfer | Money moved between own accounts (checking → credit card payment, savings top-up) | excluded | excluded | Via account balance |
| investment | Asset movement within investment accounts (brokerage buy/sell, 401K contribution) | excluded | excluded | Via account balance |

**Type assignment rules by institution:**

- **Primary Bank:** Default expense (debit) / income (credit). Transfer matched against credit card payment row.
- **Amex:** Individual charges → expense. Payment rows → transfer (matched against checking outflow). Refunds → negative expense (reduces net out).
- **Robinhood:** Dividends → income. Buy / sell → investment. Deposits into brokerage from bank → transfer. Withdrawals to bank → transfer.
- **401K / HSA:** Contributions → investment. Employer match → investment. Balance snapshots do not generate transaction rows.
- **Venmo:** Sent → expense by default; user can reclassify as transfer (e.g. splitting a bill). Received → income by default; user can reclassify as transfer.

**Manual override:** The user can change the type of any transaction at any time from the ledger. Type changes take effect immediately in all dashboard figures.

---

### 4.5 Dashboard

**Purpose:** High-level financial overview with interactive filters.

#### 4.5.1 Global filters (applied to all widgets)

- **Date range** — preset + custom range picker
- **Account** — multi-select (default: all accounts)

#### 4.5.2 KPI cards

| Card | Definition |
|---|---|
| Net worth | Sum of all account opening balances + all transactions to date (transfers excluded from flow but balances always current) |
| Net in | Total income in selected period and accounts (transfers excluded) |
| Net out | Total expenses in selected period and accounts (transfers excluded) |

#### 4.5.3 Time series chart

- X axis: time (day / week / month — user selectable granularity)
- Y axis: amount
- Three series: net in, net out, net worth
- Filterable per account (toggling an account updates all three series)
- Hoverable tooltips showing exact values at each point

#### 4.5.4 Expenditure by category

- Breakdown of net out by category for the selected period and accounts
- Shown as both a donut/pie chart and a ranked list with amounts and percentages
- Clicking a category filters the transaction ledger to that category

---

---

### 4.6 Category Taxonomy

A fixed set of categories applied consistently across all accounts and institutions. Categories are assigned during import (from CSV column or LLM pre-processing) and can be changed manually on any transaction in the ledger.

| Category | Description | Auto-assigned? |
|---|---|---|
| Food & Dining | Restaurants, cafes, food delivery, bars | No |
| Groceries | Supermarkets, wholesale clubs (Costco etc.) | No |
| Transport | Gas, parking, tolls, Uber/Lyft, public transit | No |
| Travel | Flights, hotels, car rental, Airbnb | No |
| Shopping | Amazon, retail, clothing, electronics | No |
| Health & Medical | Pharmacy, doctor, dentist, gym, insurance copays | No |
| Entertainment | Streaming, concerts, movies, games, hobbies | No |
| Utilities | Electric, gas, water, internet, phone bill | No |
| Housing | Rent, mortgage, home improvement, furniture | No |
| Insurance | Health, car, home, life insurance premiums | No |
| Education | Tuition, books, online courses, learning subscriptions | No |
| Personal Care | Haircut, spa, beauty products | No |
| Subscriptions | Software, SaaS, memberships not elsewhere classified | No |
| Fees & Charges | Bank fees, late fees, foreign transaction fees | No |
| Transfers | Matched transfer pairs | Yes — set by transfer matching |
| Investment | Brokerage buys/sells, 401K/HSA contributions | Yes — set by account type rules |
| Income | Salary, dividends, P2P payments received | Yes — set by transaction type |
| Other | Catch-all for anything unclassified | Default fallback |

**Design notes:**
- Groceries and Food & Dining are intentionally separate — they behave differently in spending analysis
- Subscriptions is separate from Entertainment — recurring fixed costs vs discretionary spend
- Transfers, Investment, and Income are auto-assigned from transaction type and cannot be manually overridden to a spending category (they are excluded from expenditure breakdowns)
- The LLM pre-processing prompt for V1 instructs the model to map source categories (e.g. the card provider's native categories) to this taxonomy
- Other is the default when no category is assigned or matched; it appears in the expenditure breakdown so uncategorised spend is visible rather than silently excluded

---

## 5. Data Model (V1)

```
Account
  id            UUID
  name          String
  type          Enum (bank | credit_card | investment | cash | loan)
  currency      String (ISO 4217)
  opening_bal   Number
  active        Boolean

FormatProfile
  id            UUID
  account_id    FK → Account
  date_col      String
  date_format   String
  desc_col      String
  amount_col    String | null
  debit_col     String | null
  credit_col    String | null
  sign_conv     Enum (neg_is_debit | pos_is_debit)
  balance_col   String | null
  skip_rows     Integer
  encoding      String

Transaction
  id            UUID
  account_id    FK → Account
  date          Date
  description   String
  amount        Number  (negative = outflow from account)
  category      Enum (see §4.6 taxonomy) | null
  type          Enum (expense | income | transfer | investment)
  match_id      UUID | null  (links two transfer rows together)
  source        Enum (imported | manual)
  import_id     UUID | null  (which import batch this came from)
  raw_row       JSON  (original CSV row, for audit)

BalanceSnapshot
  id            UUID
  account_id    FK → Account
  date          Date
  balance       Number
  source        Enum (imported | manual)
  import_id     UUID | null
  note          String | null  (e.g. "Q1 2026 statement")

ImportBatch
  id            UUID
  account_id    FK → Account
  imported_at   DateTime
  filename      String
  row_count     Integer
```

---

## 6. Technical Notes

### V0
- **Stack:** React (JSX artifact), state managed in-memory and persisted to `localStorage`.
- **Purpose:** UI prototype only. All flows should work end-to-end but data is not portable between browsers or devices.
- **Currency:** USD only. No conversion, no selector needed.
- **Charting:** Recharts (runs in-browser without a build step).
- **CSV parsing:** Client-side in JavaScript.
- **Backup:** Manual export to JSON file and restore from JSON file. Prevents data loss from accidental localStorage clear.

### V1
- **Stack:** Streamlit (Python) + SQLite via the standard `sqlite3` module. No ORM required at this scale.
- **Run locally:** `streamlit run app.py`. Database file stored at a configurable local path (default: `./fintrack.db`).
- **No separate API:** Streamlit components call Python functions directly; SQLite reads/writes happen in the same process.
- **Charting:** Plotly (already prototyped). Carries over from existing Streamlit prototype with minimal changes.
- **CSV parsing:** Python + pandas. Same logic as existing prototype, extended with saved FormatProfiles.
- **Currency:** V1 still single display currency. Multi-currency is V2.
- **Deduplication:** On import, rows matching an existing transaction exactly on `(account_id, date, description, amount)` are silently skipped. The import summary shows a count of skipped duplicates. No fuzzy matching — exact only.
- **CSV samples:** User to attach sample exports from each bank. These will finalise FormatProfile defaults per institution and drive parser tests.
- **Migration from V0:** No automated migration. User re-imports CSVs into V1; localStorage data is not carried over (acceptable given V0 is a prototype).

---

## 7. Out of Scope

### V0
- Multi-device or multi-browser access
- Any backend or server
- Auto-categorisation (user pre-processes CSV externally)
- Pending transaction status

### V1
- Multi-user / sharing
- Budget targets or alerts
- Investment performance tracking (price feeds, unrealised gains)
- Currency conversion
- Mobile app (web only)
- Cloud sync or backup (data lives in a local SQLite file; user is responsible for backups)

---

## 8. Known Gaps and Deferred Decisions

### Resolved
| Decision | Resolution |
|---|---|
| Opening balance | Derived from balance column in first imported row; user can override |
| Currency | USD only for V0 and V1; multi-currency in V2 |
| Deduplication | Exact match on (account + date + description + amount); silently skipped |
| Categories | Fixed taxonomy defined in app (see §4.6). Applied via LLM pre-processing in V1; manually assignable in both V0 and V1. credit card provider native categories mapped to this taxonomy at import. |
| Transaction types | expense / income / transfer / investment (see §4.5) |
| brokerage dividends | Manually entered as income transactions from PDF statement Income and Expense Summary |
| Brokerage | CSV available. Trans Code column drives type mapping. ACH rows matched to checking BROKERAGE DES:DEBITS. |
| Brokerage Roth IRA | CSV available, same format as brokerage. CFRI (Roth conversion) → investment type. |
| Brokerage Traditional IRA | PDF only (empty in sample). BalanceSnapshot if activity found. |
| P2P Payment App outgoing | Default to expense; user can reclassify as transfer |
| Investment buys/sells | Type = investment; excluded from net in/out; counted in net worth via account balance |
| HSA | Full transaction ledger confirmed. Payroll Deduction → investment; Interest → income; Fee Distribution → expense; Transfer Cash to Investment → skipped |
| 401K Provider | PDF only; no CSV. Imported as manual quarterly BalanceSnapshot entries. Granular buy/sell detail ignored. |
| Credit Card Provider | No category column in provided export. LLM pre-processing required same as primary checking. |
| primary checking Credit Card | CSV confirmed. Negative = charge, positive = credit/payment. Payment row matched to primary checking by `CRD 4344` in description. Foreign fee rows kept as separate Fees & Charges expenses. |
| Pending transactions | Ignored; deduplication handles the case where a pending tx later clears |
| Persistence | V0 = localStorage with manual JSON export/import; V1 = SQLite |

### Unresolved — deferred to design/build phase

**Credit card three-row problem**
When a credit card payment is made, up to three rows can exist: (1) the outflow from the bank account (primary checking), (2) the payment inflow recorded on the credit card export, and (3) the individual credit card charges. Rows 1 and 2 are matched as a transfer. Row 3 (individual charges) are real expenses and are counted. The matching logic must correctly pair rows 1 and 2 by amount + date window without accidentally matching them to any individual charge row of the same amount. The credit card payment row is identifiable because it is a large credit (negative amount in credit card convention) matching the checking outflow amount. To be validated against sample CSVs.

**Split transactions — deferred to V2**
Split transactions (one row → two or more rows with different categories and amounts summing to the original) are out of scope for V0 and V1. The primary use case is categorisation of mixed purchases (e.g. a Costco run split between Groceries and Shopping). Workaround for V0/V1: user manually assigns the dominant category to the whole transaction.

Open design questions to resolve before V2 implementation:
- What happens to the original row — hidden and replaced by children, or kept as a parent record?
- Can a split child row be transfer-matched? (Likely blocked, but needs explicit rule)
- Should splits support more than two parts?

**Transfer fee tolerance**
Matching uses a composite tolerance: two amounts are considered equal if their difference is less than **$5.00 OR less than 0.5% of the larger amount**, whichever is greater. This handles both small transfers (where a flat dollar tolerance is appropriate) and large ones (e.g. a $5,000 wire with a $10 fee). The tolerance is applied to the absolute difference between the two amounts after the date window check passes. Near-matches flagged by tolerance (i.e. not exact) are surfaced in the ledger with a visual indicator so the user can verify or unmatch them.

**Bank CSV samples**
User to provide sample exports from each institution. These will finalise the FormatProfile field definitions and confirm whether a balance column is consistently available.

## 9. Open Questions

1. Credit Card Provider category column not present in the provided export format. LLM pre-processing required for Credit Card Provider, primary checking, and primary credit card.

---

*End of document*
