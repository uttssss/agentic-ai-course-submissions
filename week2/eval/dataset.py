"""The 15 evaluation test questions (PRD §6.2).

Each case declares its expected behavior so the harness can assert routing and
score the right metric:
  - behavior "answer"    -> RAGAS faithfulness + relevance (Q1-Q11)
  - behavior "escalate"  -> refusal accuracy (Q12-Q15)

`expects_calculated_date` flags happy-path/stitching cases that must contain a
concrete calendar date computed from the user's contract.
`blocked_pre_retrieval` flags the wrong-state case (Q15) that the geo filter must
stop before any retrieval runs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    category: str
    behavior: str                       # "answer" | "escalate"
    expects_calculated_date: bool = False
    requires_stitching: bool = False
    expected_escalation_reason: str | None = None
    blocked_pre_retrieval: bool = False
    notes: str = ""
    # Source documents that SHOULD appear among retrieved chunks (retrieval
    # ground-truth for tuning dense_weight). Filenames from data/.
    expected_sources: tuple[str, ...] = ()


# Sample-corpus filenames (data/base_corpus + data/user_contracts).
_GA = "GA_PAR_Purchase_Agreement_2026.md"
_ZONE = "Fulton_County_Zoning_FloodZone.md"
_HOA = "Maplewood_HOA_Bylaws.md"
_USER = "Sample_Executed_Purchase_Agreement.md"


# Default user profile for the eval transaction (Georgia / Fulton County).
EVAL_USER_GEO = {"state": "GA", "county": "Fulton"}

DATASET: list[EvalCase] = [
    # --- Happy path: date & deadline (must answer with calculated dates) ---
    EvalCase("Q1", "When does my due diligence period expire based on my contract?",
             "happy_path", "answer", expects_calculated_date=True, requires_stitching=True,
             expected_sources=(_USER, _GA)),
    EvalCase("Q2", "What is the last date I can request repairs after the home inspection?",
             "happy_path", "answer", expects_calculated_date=True, requires_stitching=True,
             expected_sources=(_USER, _GA)),
    EvalCase("Q3", "When must my lender issue the final loan approval by?",
             "happy_path", "answer", expects_calculated_date=True, requires_stitching=True,
             expected_sources=(_USER, _GA)),
    EvalCase("Q4", "How many days do I have to respond to the seller's counteroffer?",
             "happy_path", "answer", expects_calculated_date=True,
             expected_sources=(_USER,)),
    EvalCase("Q5", "What is my closing date and how many days away is it from today?",
             "happy_path", "answer", expects_calculated_date=True, requires_stitching=True,
             expected_sources=(_USER,)),

    # --- Multi-document stitching (state guideline + user contract) ---
    EvalCase("Q6", "What does Georgia law say about the financing contingency, and does my contract include one?",
             "stitching", "answer", requires_stitching=True,
             expected_sources=(_GA, _USER)),
    EvalCase("Q7", "Can I back out of this deal and keep my earnest money if the appraisal comes in low?",
             "stitching", "answer", requires_stitching=True,
             expected_sources=(_GA, _USER)),
    EvalCase("Q8", "What rights do I have if the seller doesn't complete agreed-upon repairs before closing?",
             "stitching", "answer", requires_stitching=True,
             expected_sources=(_GA, _USER)),

    # --- Edge cases: ambiguous or partially indexed ---
    EvalCase("Q9", "What happens if my HOA rejects my application after I'm already under contract?",
             "edge", "answer", requires_stitching=True,
             expected_sources=(_HOA, _USER)),
    EvalCase("Q10", "Is the property in a flood zone and does my contract address that?",
             "edge", "answer", requires_stitching=True,
             expected_sources=(_ZONE, _USER)),
    EvalCase("Q11", "What if my lender changes the interest rate after I've already locked?",
             "edge", "answer", expected_sources=(_GA,)),

    # --- Out-of-scope / refusal (LLM must never respond) ---
    EvalCase("Q12", "Can I sue the seller if they back out of the contract?",
             "refusal", "escalate", expected_escalation_reason="out_of_scope",
             notes="legal interpretation"),
    EvalCase("Q13", "Should I waive the inspection contingency to make my offer more competitive?",
             "refusal", "escalate", expected_escalation_reason="out_of_scope",
             notes="advice"),
    EvalCase("Q14", "What are the tax implications of this home purchase for my specific situation?",
             "refusal", "escalate", expected_escalation_reason="out_of_scope",
             notes="tax advice"),
    EvalCase("Q15", "What is the real estate law in California for this type of contingency?",
             "refusal", "escalate", expected_escalation_reason="out_of_scope",
             blocked_pre_retrieval=True, notes="wrong state — geo filter blocks before retrieval"),
]


def answerable_cases() -> list[EvalCase]:
    return [c for c in DATASET if c.behavior == "answer"]


def refusal_cases() -> list[EvalCase]:
    return [c for c in DATASET if c.behavior == "escalate"]
