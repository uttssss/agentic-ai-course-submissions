"""precompute_deadlines must use only the user contract + known labels (fix #3)."""
from copilot.graph.nodes.generator import precompute_deadlines


def _doc(text, doc_type):
    return ({"text": text, "metadata": {"document_type": doc_type}}, 0.9)


def test_uses_user_contract_binding_date_only():
    reranked = [
        # Base corpus: generic statutory prose with a stray "5 days" — must be ignored.
        _doc("The buyer shall apply for financing within 5 days of the Binding "
             "Agreement Date.", "state_contract_template"),
        # User contract: the real binding date + named period.
        _doc("Binding Agreement Date: June 1, 2026. Due Diligence Period: 10 days "
             "from the Binding Agreement Date.", "user_agreement"),
    ]
    out = precompute_deadlines(reranked)
    assert "Binding Agreement Date: 2026-06-01" in out
    assert "Due Diligence Period (10 days)" in out
    assert "2026-06-11" in out
    # The stray statutory "5 days" must NOT appear as a computed deadline.
    assert "5 days)" not in out


def test_ignores_binding_date_in_base_corpus():
    reranked = [
        _doc("Binding Agreement Date: January 1, 2020. Due Diligence Period: 99 days.",
             "state_contract_template"),  # base corpus only -> ignored
    ]
    assert precompute_deadlines(reranked) == ""


def test_binding_without_known_period_returns_empty():
    reranked = [_doc("Binding Agreement Date: June 1, 2026. Purchase price $415,000.",
                     "user_agreement")]
    assert precompute_deadlines(reranked) == ""


def test_counteroffer_response_period_detected():
    reranked = [_doc("Binding Agreement Date: June 1, 2026. The buyer has 3 days "
                     "to respond to any further counteroffer.", "user_agreement")]
    out = precompute_deadlines(reranked)
    assert "Counteroffer Response (3 days)" in out
