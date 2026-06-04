# Mastering Agentic AI — Week 1 Submission

**Student:** Utthra  
**Course:** Mastering Agentic AI  
**Week:** 1  
**Project:** fintrack — Personal Finance Tracker

---

## Project Overview

fintrack is a personal finance tracker built to solve a specific problem: most finance apps double-count transactions when you move money between accounts. When you pay your credit card from your checking account, you get charged once as an outflow from the bank and again as the sum of individual expenses on the card. fintrack eliminates this by automatically detecting transfer pairs — matching outflows from one account to inflows in another within a 5-day window — and excluding them from net spend calculations.

**What was built (V0):**
- Account management with opening balance tracking
- CSV import with per-account format profiles (saved so you only map columns once)
- Automatic transfer matching with manual override
- Transaction ledger with filtering, search, and inline editing
- Dashboard with net worth, net in/out, time series charts, and spending by category
- JSON backup and restore (since data lives in localStorage)

**Stack:** React + Recharts + browser localStorage  
**Data range:** Jan 2025 – May 2026 across 10 account types  
**Total build time:** ~2–3 hours

---

## Datasets Used

Real CSV exports were collected from each financial institution and analyzed to build format profiles before any import code was written. The following sources were used:

| Institution | Account type | Format | Key characteristics |
|---|---|---|---|
| Primary Bank (checking) | Checking | CSV | 6 header/summary rows to skip; signed amount; running balance column |
| Primary Bank (credit card) | Credit card | CSV | No skip rows; positive = charge, negative = payment; no balance column |
| Credit Card Provider | Credit card | CSV | Positive = charge, negative = payment/credit; no category column |
| P2P Payment App | Payments | CSV | 3 skip rows; `+ $` / `- $` prefixed amounts; type column |
| HSA Provider Provider | HSA Provider | CSV | Clean format; description-based type mapping; running balance |
| Brokerage | Investment | CSV | Trans Code column drives type; parentheses-for-negative amounts; multi-line quoted fields |
| Retirement IRA | Investment | CSV | Same format as brokerage; CFRI trans code for Roth conversions |
| 401K Provider | 401K | PDF only | Quarterly statements; manually entered as balance snapshots |
| Brokerage IRA | Investment | PDF only | Monthly statements; manually entered as balance snapshots |

Three anonymised demo CSV files were also generated (checking, savings, credit card) covering 12 months of realistic transaction data for demonstration purposes.

---

## Prompts Used During the Process

The session followed a deliberate product-first workflow: spec before code.

| Prompt | Purpose |
|---|---|
| *"I want to build an app for keeping track of my finances... when I move money from one account to another, it is not clear if I am spending that money or just parking it."* | First attempt (Claude Code, outside this session). Built something technically impressive but unfocused — no spec meant no way to steer the output. Restarted. |
| *"Let's first write a clean PRD. Overall goal: track my net worth, expenses and earnings across all my financial accounts..."* | Kicked off the PRD process. Defined account types, transaction types, and core flows before any code. |
| *"Dashboard specs: date filter, account filter, net in/out, net worth, time series, expenditure by category."* | Locked dashboard requirements in one prompt. |
| *"We don't need to ask user for confirmation for counting. We just need to surface the information and then allow user to undo or add other matches."* | Settled the entire transfer matching UX: auto-match silently, surface results, make undo easy. No confirmation modals. |
| *"Ok write it as v0 as localstorage and v1 as lightweight backend (SQLite + local server)."* | Established V0 as a throwaway UI prototype and V1 as a Streamlit + SQLite backend. Kept the build focused. |
| *"Ok just suggest your (Claude's) own categories."* | Delegated category taxonomy to Claude rather than debating it — reviewed and accepted the output. |
| *"You tell me what else I am missing and not considering?"* | Surfaced 10 gaps including the credit card three-row problem, opening balance anchoring, and the need for a localStorage backup. |
| *"I am exporting from Primary Bank, Credit Card Provider, Brokerage and other 401K/HSA Provider/P2P Payment App data"* + uploaded files | Validated format profiles against real exports. Discovered: Primary Bank has 6 skip rows, Credit Card Provider has no category column, P2P Payment App uses `+ $`/`- $` strings, 401K is PDF-only. |
| *"yes let's build v0"* | The actual build prompt — one line, after ~3 hours of spec work. The entire app was generated in one pass. |
| *"no negative CSV amount is transfer. Look here: [uploaded activity.csv]"* | Fixed credit card sign convention by uploading the real file rather than reasoning about it. |

---

## Iterations Tried

| Iteration | What happened | Learning |
|---|---|---|
| Claude Code first pass | Asked Claude to build the app directly without specs. Got a working app but it consumed many tokens, lacked key features, and had no clear direction. | Starting without a spec is expensive and produces output you can't easily steer. |
| PRD-first restart | Stopped the build, wrote a full PRD, versioned requirements, debated edge cases. Felt slower but wasn't. | Time spent on specs pays back immediately during build — fewer revisions, clearer prompts. |
| File-driven spec validation | Uploaded real CSV exports before finalising format profiles. Discovered several incorrect assumptions (Credit Card Provider no categories, Brokerage PDF-only, P2P Payment App string amounts). | Never assume file formats. Always validate against real data before writing parser code. |
| Single-pass build | With specs locked, the entire app was built in one prompt. | The quality of the output scales with the quality of the context given. One good spec is worth ten iterative build prompts. |
| Real data bug fix | Credit card sign convention was wrong. Uploading the actual file fixed it in one exchange. | Real data finds bugs faster than any amount of reasoning about the data. |

---

## Learnings and Observations

**1. Specs before code is not slower — it's faster**
The instinct to start building immediately is strong, especially when the tools are this capable. But the first Claude Code attempt showed that unguided building consumes tokens without producing something you actually want. The PRD process took ~1–2 hours and made the actual build trivial.

**2. Claude is an excellent thought partner for product design**
Asking "what am I missing?" surfaced gaps I genuinely hadn't considered — the three-row credit card problem, investment account valuation vs transaction modelling, the localStorage backup risk. This kind of adversarial review is normally what a PM does with an engineering lead. Having it available on demand is genuinely useful.

**3. Real files beat assumptions every time**
Several format profiles in the PRD were wrong before the files were uploaded. Credit Card Provider was assumed to have a category column — it doesn't. Brokerage was assumed to have a CSV — the IRA accounts are PDF-only. Uploading real data resolved these instantly, where reasoning alone would have led to bugs discovered later.

**4. Versioning decisions explicitly pays off**
Making explicit decisions about what is and isn't in scope (V0 vs V1 vs V2) prevented scope creep during the build. When a feature came up that wasn't needed yet, it went into the roadmap rather than the current build. This kept the prompt context clean and the output focused.

**5. The right UX decision often comes from a single sentence**
The transfer matching philosophy — "surface it, don't confirm it, make undo easy" — was settled in one prompt. That single decision shaped the entire matching UX. Good product thinking doesn't require long discussions; it requires asking the right question.

**6. Token efficiency scales with preparation**
The first attempt used many tokens to build something incomplete. The second attempt used ~2–3 hours of conversation to produce a complete, working app with a full PRD, format profiles for 10 data sources, demo data, a README, and a social post. The difference was entirely in the preparation.

---

## What's Next

- **V1:** Port to Streamlit + SQLite for real persistence. Same flows, real backend, LLM-assisted categorisation.
- **Multi-account expansion:** Add Brokerage brokerage, HSA Provider, and P2P Payment App to the import flow
- **Balance snapshots UI:** Manual entry flow for PDF-only accounts (401K, Brokerage IRAs)
- **V2:** Multi-file import, Excel/PDF support, multi-currency, budget targets

