"""confidence_gate boundary behavior (§10.1, PRD §5.2)."""
import pytest

from copilot.config.settings import settings
from copilot.graph.nodes.gate import confidence_gate, gate_decision


def test_just_below_threshold_escalates():
    s = confidence_gate({"top_score": 0.749})
    assert s["route"] == "escalate"
    assert s["escalation_reason"] == "low_confidence"


def test_exactly_at_threshold_generates():
    s = confidence_gate({"top_score": settings.confidence_threshold})
    assert s["route"] == "generate"


def test_above_threshold_generates():
    s = confidence_gate({"top_score": 0.91})
    assert s["route"] == "generate"


def test_missing_score_defaults_to_escalate():
    s = confidence_gate({})
    assert s["route"] == "escalate"


def test_gate_decision_returns_route():
    assert gate_decision({"route": "generate"}) == "generate"
    assert gate_decision({"route": "escalate"}) == "escalate"
