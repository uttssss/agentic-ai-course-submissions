"""Pure tuning-metric helpers (offline; live sweeps need API keys)."""
from copilot.eval.tune import mrr, recall_at_k, recommend_threshold


def test_recall_full_and_partial():
    assert recall_at_k(["a.md", "b.md"], ("a.md", "b.md")) == 1.0
    assert recall_at_k(["a.md"], ("a.md", "b.md")) == 0.5
    assert recall_at_k(["x.md"], ("a.md",)) == 0.0


def test_recall_empty_expected_is_one():
    assert recall_at_k(["anything.md"], ()) == 1.0


def test_mrr_rewards_higher_rank():
    assert mrr(["a.md", "b.md", "c.md"], ("a.md",)) == 1.0
    assert mrr(["x.md", "a.md"], ("a.md",)) == 0.5
    assert mrr(["x.md", "y.md"], ("a.md",)) == 0.0


def test_recommend_threshold_admits_all_with_margin():
    # min answerable score 0.82, margin 0.05 -> 0.77
    assert recommend_threshold([0.95, 0.82, 0.90], margin=0.05) == 0.77


def test_recommend_threshold_clamped_to_zero():
    assert recommend_threshold([0.02], margin=0.05) == 0.0


def test_recommend_threshold_empty_falls_back_to_config():
    from copilot.config.settings import settings
    assert recommend_threshold([]) == settings.confidence_threshold
