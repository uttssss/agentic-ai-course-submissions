"""query_router classification (§10.1, PRD §5.6)."""
import pytest

from copilot.eval.dataset import DATASET, EVAL_USER_GEO
from copilot.graph.nodes.router import query_router

GA = {"state": "GA", "county": "Fulton"}


@pytest.mark.parametrize("case", DATASET, ids=[c.id for c in DATASET])
def test_router_matches_expected_behavior(case):
    state = {"query": case.question, "user_geo": EVAL_USER_GEO}
    query_router(state)
    expected = "escalate" if case.behavior == "escalate" else "retrieve"
    assert state["route"] == expected


def test_in_scope_date_query_routes_to_retrieve():
    state = {"query": "When does my due diligence period expire?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "retrieve"


def test_legal_query_escalates_out_of_scope():
    state = {"query": "Can I sue the seller?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "escalate"
    assert state["escalation_reason"] == "out_of_scope"


def test_tax_query_escalates():
    state = {"query": "What are the tax implications for me?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "escalate"


def test_advice_query_escalates():
    state = {"query": "Should I waive the inspection contingency?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "escalate"


def test_wrong_state_blocked_before_retrieval():
    # User is in GA but asks about California -> geo isolation blocks pre-retrieval.
    state = {"query": "What is the real estate law in California for this?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "escalate"
    assert state["_router_topic"] == "wrong_geography"


def test_matching_state_mention_is_allowed():
    state = {"query": "What does Georgia law say about financing?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "retrieve"


def test_benign_should_i_timing_question_not_escalated():
    # "should I expect" is benign timing, not advice-seeking (review fix #7).
    state = {"query": "When should I expect the appraisal to be completed?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "retrieve"


def test_advice_seeking_should_i_still_escalates():
    state = {"query": "Should I waive the financing contingency?", "user_geo": GA}
    query_router(state)
    assert state["route"] == "escalate"
