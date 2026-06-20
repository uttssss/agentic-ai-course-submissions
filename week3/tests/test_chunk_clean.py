"""Chunking + cleaning + date detection (§10.1, PRD §2)."""
from copilot.config.settings import settings
from copilot.ingest.chunk import chunk_document
from copilot.ingest.clean import clean_text, extract_section_headers, is_date_bearing

SAMPLE = """# Binding Agreement Date
The Binding Agreement Date is June 1, 2026 and all periods run from it.

# Due Diligence Period
The Due Diligence Period runs for 10 days from the Binding Agreement Date.

# Use Restrictions
Owners must obtain approval before exterior modifications.
"""


def test_chunks_are_section_bounded():
    chunks = chunk_document(SAMPLE)
    headers = {c["section_header"] for c in chunks}
    assert {"Binding Agreement Date", "Due Diligence Period", "Use Restrictions"} <= headers


def test_date_bearing_flag_set_correctly():
    chunks = {c["section_header"]: c for c in chunk_document(SAMPLE)}
    assert chunks["Binding Agreement Date"]["is_date_bearing"] is True
    assert chunks["Due Diligence Period"]["is_date_bearing"] is True
    assert chunks["Use Restrictions"]["is_date_bearing"] is False


def test_is_date_bearing_variants():
    assert is_date_bearing("closing is on 07/15/2026")
    assert is_date_bearing("within 10 days")
    assert is_date_bearing("June 1, 2026")
    assert not is_date_bearing("the buyer may inspect the property")


def test_clean_strips_markdown_images():
    assert "image" not in clean_text("text ![image](x.png) more").lower()


def test_extract_section_headers():
    headers = [h for h, _ in extract_section_headers(SAMPLE)]
    assert headers == ["Binding Agreement Date", "Due Diligence Period", "Use Restrictions"]


def test_large_section_is_windowed_with_overlap():
    big = "# Big\n" + " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_document(big)
    assert len(chunks) > 1  # exceeds chunk_size_tokens, so it must split
    assert all(c["section_header"] == "Big" for c in chunks)
