"""Hybrid blend normalization + cross-encoder sigmoid (review fixes #1, #2)."""
from copilot.graph.nodes.reranker import _sigmoid
from copilot.graph.nodes.retriever import _blend, _normalize


def test_sigmoid_maps_logits_to_unit_interval():
    assert _sigmoid(0.0) == 0.5
    assert 0.0 < _sigmoid(-8.0) < 0.5 < _sigmoid(8.0) < 1.0


def test_sigmoid_numerically_stable_for_large_magnitudes():
    assert _sigmoid(1000.0) == 1.0          # no overflow
    assert _sigmoid(-1000.0) == 0.0         # no overflow


def test_normalize_scales_to_zero_one():
    out = _normalize({"a": 2.0, "b": 7.0, "c": 12.0})
    assert out["a"] == 0.0 and out["c"] == 1.0
    assert 0.0 < out["b"] < 1.0


def test_normalize_all_equal_returns_full_match():
    assert _normalize({"a": 3.0, "b": 3.0}) == {"a": 1.0, "b": 1.0}


def test_blend_prevents_bm25_from_dominating():
    # Raw BM25 (0-20) would swamp dense cosine (0-1) without normalization.
    dense = {"x": 0.9, "y": 0.1}      # x clearly better on dense
    sparse = {"x": 1.0, "y": 20.0}    # y has a huge raw BM25 score
    blended = _blend(dense, sparse, w=0.5)
    # After normalization both signals are comparable; with equal weight the
    # strong-dense / weak-sparse doc and weak-dense / strong-sparse doc tie-ish.
    assert abs(blended["x"] - blended["y"]) < 0.6   # neither side dominates wholesale
    # Sanity: dense-favored doc beats nothing-special — give dense full weight:
    assert _blend(dense, sparse, w=1.0)["x"] > _blend(dense, sparse, w=1.0)["y"]
