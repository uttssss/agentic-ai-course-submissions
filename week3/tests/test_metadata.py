"""Metadata validation rejecting incomplete chunks (§10.1, PRD §5.3)."""
import pytest

from copilot.ingest.metadata import (
    MetadataError, build_metadata, make_chunk_id, validate, VALID_DOC_TYPES,
)


def _valid_kwargs(**overrides):
    base = dict(
        state="GA", county="Fulton", document_type="state_contract_template",
        source_document="GA_PAR_2026.md", section_header="Due Diligence Period",
        page=7, is_date_bearing=True, session_id=None, text="some text",
    )
    base.update(overrides)
    return base


def test_build_metadata_valid():
    md = build_metadata(**_valid_kwargs())
    assert md["state"] == "GA"
    assert md["document_type"] in VALID_DOC_TYPES
    assert md["ingested_at"].endswith("Z")
    assert md["text"] == "some text"


@pytest.mark.parametrize("missing", ["state", "county", "document_type"])
def test_missing_required_field_raises(missing):
    bad = {"state": "GA", "county": "Fulton", "document_type": "hoa_bylaws"}
    bad[missing] = ""
    with pytest.raises(MetadataError):
        validate(bad)


def test_invalid_document_type_raises():
    with pytest.raises(MetadataError):
        validate({"state": "GA", "county": "Fulton", "document_type": "nonsense"})


def test_chunk_id_is_slugged_and_indexed():
    cid = make_chunk_id("GA", "GA_PAR_2026.md", "Due Diligence Period", 3)
    assert cid == "ga_ga_par_2026_md_due_diligence_period_003"


def test_user_agreement_carries_session_id():
    md = build_metadata(**_valid_kwargs(document_type="user_agreement", session_id="abc123"))
    assert md["session_id"] == "abc123"
