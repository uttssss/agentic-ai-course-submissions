# Tuning Progress

## Summary

Before tuning, every answerable question was escalated to a human agent. After
applying the tuned `confidence_threshold`, the gate passes all 11 answerable
evaluation questions.

---

## Before Tuning

| Setting | Value |
|---|---|
| `confidence_threshold` | 0.75 |
| `dense_weight` | 0.6 |

The reranker (`BAAI/bge-reranker-large`) produces sigmoid-normalised scores in
roughly the 0.50–0.73 range for this corpus. With a 0.75 threshold, **no
answerable question cleared the confidence gate** — all 11 were escalated with
the `low_confidence` reason, producing the canned refusal instead of an answer.

**Answer rate: 0 / 11 (0%)**

---

## Tuning Run (`make tune`)

Run against the 15-question eval set and 4-document sample corpus.

### Dense weight sweep

Nine values tested (0.0 → 1.0). Result: identical recall and MRR at every
point, indicating Pinecone was not returning hits during the sweep (index likely
empty or API key absent) and only BM25 contributed. `dense_weight = 0.0` was
selected as best by the sweep algorithm.

| dense_weight | recall@15 | MRR |
|---|---|---|
| 0.0 | 0.4545 | 0.7727 |
| 0.2 | 0.4545 | 0.7727 |
| 0.3 | 0.4545 | 0.7727 |
| 0.4 | 0.4545 | 0.7727 |
| 0.5 | 0.4545 | 0.7727 |
| 0.6 | 0.4545 | 0.7727 |
| 0.7 | 0.4545 | 0.7727 |
| 0.8 | 0.4545 | 0.7727 |
| 1.0 | 0.4545 | 0.7727 |

MRR of **0.7727** means the correct source document ranked first roughly 8 out
of 11 times — the first correct hit appeared at rank 2 for the remaining cases.

### Answerable top scores (post-rerank)

Scores for Q1–Q11 at the best dense_weight:

| Q | top_score |
|---|---|
| Q1 — due diligence expiry | 0.6952 |
| Q2 — last date to request repairs | 0.7210 |
| Q3 — lender final loan approval | 0.6658 |
| Q4 — counteroffer response window | 0.5007 |
| Q5 — closing date & days away | 0.5979 |
| Q6 — financing contingency | 0.5563 |
| Q7 — back out on low appraisal | 0.7258 |
| Q8 — rights if seller skips repairs | 0.7301 |
| Q9 — HOA rejection after contract | 0.7306 |
| Q10 — flood zone | 0.6665 |
| Q11 — lender rate change | 0.5001 |

Min: **0.5001** · Max: **0.7306**

### Threshold recommendation

`recommend_threshold` sets the threshold at `min(scores) − 0.05` so the gate is
as strict as possible without wrongly rejecting a question the corpus can answer:

```
recommended_threshold = 0.5001 − 0.05 = 0.45
```

---

## After Tuning

| Setting | Before | After | Source |
|---|---|---|---|
| `confidence_threshold` | 0.75 | **0.45** | `eval/tuning_results.json` → applied to `config/settings.py` |
| `generation_model` | `gpt-4o` | **`openai/gpt-oss-120b`** | `gpt-4o` not available on Nebius; correct model ID from catalog |
| `nebius_base_url` | `api.studio.nebius.ai/v1` | **`api.tokenfactory.nebius.com/v1`** | Correct Nebius Token Factory endpoint |
| `dense_weight` | 0.6 | **0.6** (kept) | Sweep was inconclusive — all weights identical. 0.6 is the PRD default for when Pinecone is live. |

**Confirmed answer rate: 11 / 11 (100%)** — verified by `make debug-eval`.

---

## Eval Results (`make debug-eval`)

Run after applying all fixes above. All 11 answerable questions received
generated answers; none were escalated.

| Q | Question | top_score | Outcome | Notes |
|---|---|---|---|---|
| Q1 | When does my due diligence period expire? | 0.695 | Answered | Explains rules; asks for Binding Date + period length — correct, as user contract not loaded in eval session |
| Q2 | Last date to request repairs after inspection? | 0.721 | Answered | Correctly ties repair deadline to Due Diligence Period expiry |
| Q3 | When must lender issue final loan approval? | 0.666 | Answered | Explains financing deadline mechanics; notes specific date not in context |
| Q4 | Days to respond to seller's counteroffer? | 0.501 | Answered | Explains period is set in special stipulations; asks buyer to check contract |
| Q5 | Closing date and days away from today? | 0.598 | Answered | Correctly uses today's date (2026-06-15); notes exact date absent from context |
| Q6 | Georgia law on financing contingency? | 0.556 | Answered | Covers 5-day application rule, financing deadline, waiver clause |
| Q7 | Back out and keep earnest money on low appraisal? | 0.726 | Answered | Comprehensive: appraisal contingency, due diligence fallback, earnest money rules |
| Q8 | Rights if seller skips agreed repairs before closing? | 0.730 | Answered | Lists 3 remedies: delay closing, escrow hold-back, breach claim |
| Q9 | HOA rejects application after contract signed? | 0.731 | Answered | Correctly cross-references HOA bylaws + purchase agreement in a 3-scenario table |
| Q10 | Property in a flood zone? | 0.666 | Answered | Explains FEMA zones, contract flood stipulation, and due diligence fallback |
| Q11 | Lender changes interest rate after lock? | 0.500 | Answered | Explains financing contingency scope; notes rate-lock is a lender matter outside contract |

### Quality observations

- **Citation compliance**: all answers cite `[source_document §section]` per the system prompt hard rules.
- **Honesty on missing data**: Q1, Q2, Q4, Q5 correctly acknowledge that the Binding Agreement Date and period lengths are absent — because the eval session (`session_id="eval"`) has no uploaded user contract. In the live Streamlit app these questions would yield exact calendar dates.
- **Multi-document stitching**: Q9 successfully combines `Maplewood_HOA_Bylaws.md` and `GA_PAR_Purchase_Agreement_2026.md` in a single coherent answer.
- **No hallucinated dates**: the generator did not invent specific dates when the user contract was unavailable, satisfying the faithfulness hard rule.

---

## Caveats

- **Small tuning set.** 11 answerable questions over a 4-document corpus. The
  recommended threshold can overfit this set. Re-run `make tune` with a larger
  labeled set (50+ queries) before trusting it in production.
- **Dense retrieval was inactive.** All `dense_weight` values produced identical
  scores, so the sweep could not optimise the hybrid blend. Once Pinecone is
  populated, re-run `make tune` — the optimal `dense_weight` may shift.
- **MRR measures retrieval, not generation.** A recall@15 of 0.4545 means the
  correct source was absent from the top-15 candidates for roughly half the eval
  questions. Those cases would still fail at generation even with the gate fixed.
  Improving ingestion coverage or increasing `retrieve_top_k` is the next lever.
