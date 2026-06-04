# fintrack

A personal finance tracker that gives a single, accurate view of net worth, income, and spending across all your financial accounts.

The core problem it solves: when you pay your credit card from your bank account, most tools count it twice — once as an outflow from your bank, and again as individual expenses on the card. fintrack automatically detects these transfer pairs and excludes them from your spending figures, so your numbers are always correct.

---

## Features

- **Account management** — add checking, savings, credit card, and investment accounts with opening balances
- **CSV import** — upload exports from your bank with column mapping saved per account, so you only configure it once
- **Automatic transfer matching** — credit card payments, savings transfers, and other inter-account movements are detected and excluded from net spend automatically
- **Transaction ledger** — full history across all accounts, filterable by date range, account, type, and category; inline editing and manual add
- **Dashboard** — net worth, net in/out, net flow KPIs; time series chart of all three; spending breakdown by category; account balance chart
- **Backup & restore** — export your data as JSON and restore it at any time

---

## Getting Started
 
### Prerequisites
 
- [Node.js](https://nodejs.org) v18 or later and npm v8 or later
Verify your versions before starting:
 
```bash
node -v   # should be v18 or higher
npm -v    # should be v8 or higher
```
 
If your versions are older (especially npm 3.x which ships with old Anaconda environments), update Node first using [nvm](https://github.com/nvm-sh/nvm):
 
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# restart your terminal, then:
nvm install --lts
nvm use --lts
```
 
### Step 1 — Clone the repo
 
```bash
git clone https://github.com/uttssss/agentic-ai-course-submissions.git
```
 
### Step 2 — Scaffold a Vite + React project
 
The app is a single `.jsx` file. Use Vite to create a project to run it in. Run this from wherever you cloned the repo — **not** inside the `week1` folder:
 
```bash
npm create vite@latest fintrack -- --template react
cd fintrack
```
 
### Step 3 — Install dependencies
 
```bash
npm install
npm install recharts
```
 
### Step 4 — Copy the app file in
 
```bash
cp ../agentic-ai-course-submissions/week1/fintrack-v0.jsx src/App.jsx
```
 
### Step 5 — Start the dev server
 
```bash
npm run dev
```
 
The app opens at `http://localhost:5173`.
 
### Step 6 — First run
 
1. Go to **Accounts** in the sidebar and add your accounts — give each one a name, type (checking, savings, credit card, etc.), and opening balance
2. Go to **Import CSV** and upload your first bank export
3. Select the account it belongs to, then map the columns (date, description, amount) — the mapping is saved for next time
4. Review the transaction preview and confirm the import
5. Repeat for each account
6. Open **Dashboard** to see net worth, income, spending trends, and category breakdown
> **Demo data:** If you just want to explore the app without your own files, use the sample CSVs in `demo-data/` — see the [Demo Data](#demo-data) section below for setup instructions.
 
---

## CSV Import Guide

fintrack accepts any CSV with at least a date, description, and amount column. Column names are mapped on first import and saved per account.

### Supported formats

| Account type | Skip rows | Date column | Amount convention | Balance column |
|---|---|---|---|---|
| Bank checking / savings | 6 | `date` | Positive = credit, negative = debit | `running bal.` |
| Credit card | 0 | `date` or `posted date` | Positive = charge, negative = payment/credit | None |

### Sign conventions

- **Bank accounts:** negative amounts are expenses/transfers out, positive are income/transfers in
- **Credit cards:** positive amounts are charges (expenses), negative amounts are payments (transfers) or refunds

### Opening balance

If your CSV includes a running balance column, fintrack uses the first row's balance to suggest an opening balance. You can override this when setting up the account.

### Deduplication

Rows that exactly match an existing transaction (same account, date, description, and amount) are silently skipped. This means you can safely re-import overlapping exports without creating duplicates.

---

## Transfer Matching

When you import transactions from multiple accounts, fintrack automatically looks for transfer pairs — an outflow from one account that matches an inflow to another within a 5-day window.

**Matching rules:**
- Amounts match within $5.00 or 0.5% of the larger amount (to account for wire fees)
- Dates are within 5 calendar days of each other
- The two transactions are from different accounts

**What happens when a match is found:**
- Both transactions are typed as `transfer`
- They are excluded from net in / net out calculations
- They remain visible in the ledger with a `↔match` indicator
- Near-matches (within tolerance but not exact) show `≈match` so you can verify

**Manual controls:**
- Click **unmatch** on any matched transaction to break the pair
- Manually add a transaction and it will be matched on save if a counterpart exists

---

## Transaction Types

| Type | Description | Counted in net out? | Counted in net in? | Affects net worth? |
|---|---|---|---|---|
| expense | Money spent | ✓ | — | Via account balance |
| income | Money received | — | ✓ | Via account balance |
| transfer | Money moved between own accounts | — | — | Via account balance |
| investment | Investment activity | — | — | Via account balance |

---

## Categories

Transactions are assigned a category on import (from a CSV column if present) or manually in the ledger. The full category list:

`Food & Dining` · `Groceries` · `Transport` · `Travel` · `Shopping` · `Health & Medical` · `Entertainment` · `Utilities` · `Housing` · `Insurance` · `Education` · `Personal Care` · `Subscriptions` · `Fees & Charges` · `Other`

Transfer, Investment, and Income are auto-assigned from transaction type and excluded from the spending breakdown.

---

## Data & Privacy

All data is stored in your browser's `localStorage`. Nothing is sent to any server. There is no account, no login, and no cloud sync.

**Backup regularly:** localStorage can be cleared by the browser. Use **Settings → Export JSON backup** to save a copy of your data, and **Restore from JSON** to load it back.

---

## Demo Data

Three sample CSV files are included for testing:

| File | Account type | Transactions | Period |
|---|---|---|---|
| `week1/demo-data/demo_checking.csv` | Checking | 144 | Jun 2025 – May 2026 |
| `week1/demo-data/demo_savings.csv` | Savings | 28 | Jun 2025 – May 2026 |
| `week1/demo-data/demo_credit_card.csv` | Credit card | 206 | Jun 2025 – May 2026 |

**Setup for demo:**
Loom walkthrough: https://www.loom.com/share/631b1f42c13e492d856a2b397cf7e6f3

Add three accounts before importing:

| Name | Type | Opening balance | As-of date |
|---|---|---|---|
| Primary Checking | checking | 22432.50 | 2025-06-01 |
| Primary Savings | savings | 18500.00 | 2025-06-01 |
| Credit Card | credit_card | 0.00 | 2025-06-01 |

Then import each file with the following settings:

- **week1/demo-data/demo_checking.csv** and **week1/demo-data/demo_savings.csv:** skip rows `6`, date → `date`, description → `description`, amount → `amount`, balance → `running bal.`
- **week1/demo-data/demo_credit_card.csv:** skip rows `0`, date → `date`, description → `description`, amount → `amount`

---

## Roadmap

### V0 (current) — Browser prototype
React app with localStorage. Goal is to validate all UX flows before building a backend.

### V1 — Persistent backend
Streamlit + SQLite running locally. Same UI flows, real database, format profiles saved across sessions, LLM-assisted categorisation.

### V2 — Extended import & features
Multi-file import per account, Excel and PDF support, multi-currency, budget targets, in-app auto-categorisation.

---

## Tech Stack

- [React](https://react.dev) — UI
- [Recharts](https://recharts.org) — charts
- Browser `localStorage` — persistence (V0)


