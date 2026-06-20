"""escalation node returns refusal copy and never calls the LLM (§10.1, PRD §5.2)."""
import copilot.graph.nodes.escalation as esc_mod
from copilot.graph.nodes.escalation import escalation


def test_escalation_returns_refusal_copy():
    state = {"query": "Can I sue the seller?", "escalation_reason": "out_of_scope",
             "_router_topic": "legal_advice"}
    out = escalation(state)
    assert out["escalated"] is True
    assert "flagged this message and forwarded it to your agent" in out["answer"]
    assert out["source_citations"] == []


def test_low_confidence_uses_query_topic():
    state = {"query": "What happens with my escrow holdback?", "escalation_reason": "low_confidence"}
    out = escalation(state)
    assert "escrow holdback" in out["answer"]


def test_escalation_does_not_import_or_call_generator(monkeypatch):
    # Guard: if anything in escalation tries to call the generator, fail loudly.
    called = {"flag": False}

    def boom(*a, **k):
        called["flag"] = True
        raise AssertionError("LLM generator called during escalation")

    monkeypatch.setattr("copilot.graph.nodes.generator.generator", boom, raising=True)
    escalation({"query": "tax question", "escalation_reason": "out_of_scope",
                "_router_topic": "tax_advice"})
    assert called["flag"] is False


def test_agent_review_hook_invoked(monkeypatch):
    hits = {"n": 0}
    monkeypatch.setattr(esc_mod, "_flag_for_agent_review", lambda s: hits.__setitem__("n", hits["n"] + 1))
    escalation({"query": "q", "escalation_reason": "out_of_scope"})
    assert hits["n"] == 1
