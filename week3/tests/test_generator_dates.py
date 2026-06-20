"""Generator's deterministic deadline precompute (§10.1, PRD §5.1).

Note: scoping/label rules are covered in test_deadline_scoping.py; these focus on
date-format parsing within a valid user-agreement chunk.
"""
from copilot.graph.nodes.generator import precompute_deadlines


def _contract(text):
    return ({"text": text, "metadata": {"document_type": "user_agreement"}}, 0.9)


def test_precompute_extracts_binding_and_known_period():
    reranked = [_contract(
        "Binding Agreement Date: June 1, 2026. "
        "Due Diligence Period: 10 days from the Binding Agreement Date."
    )]
    out = precompute_deadlines(reranked)
    assert "Binding Agreement Date: 2026-06-01" in out
    assert "2026-06-11" in out          # June 1 + 10 days
    assert "PRECOMPUTED DEADLINES" in out


def test_precompute_empty_without_binding_date():
    reranked = [_contract("The buyer may inspect the property during due diligence.")]
    assert precompute_deadlines(reranked) == ""


def test_precompute_handles_slash_date_format():
    reranked = [_contract("Binding date: 06/01/2026. Due Diligence Period: 10 days.")]
    out = precompute_deadlines(reranked)
    assert "2026-06-01" in out
    assert "Due Diligence Period (10 days)" in out
