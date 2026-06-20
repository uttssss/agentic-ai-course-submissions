"""generator node (PRD §5.4).

Calls GPT-4o via Nebius. The prompt contract enforces: (1) grounding in the
supplied chunks only, (2) a citation (source document + section) for every claim,
and (3) explicit calendar-date calculation from binding date + period when a
deadline is implied (multi-document stitching, §5.1).
"""
from __future__ import annotations

import datetime as dt
import re

from ...config.settings import settings
from ...utils.dates import days_until, deadline_from
from ..state import RAGState

SYSTEM_PROMPT = """You are a real estate transaction assistant for first-time homebuyers.

HARD RULES:
1. Answer ONLY using the provided context chunks. If the context is insufficient, say so plainly — never invent facts, dates, or rules.
2. Cite the source document and section for every factual claim, formatted as [source_document §section_header].
3. When a deadline is implied, compute the explicit calendar date from the binding/effective date plus the stated period. Show the arithmetic briefly.
4. Combine statutory/guideline rules (baseline) with the buyer's executed contract details (specific dates) into one coherent answer.

Today's date is {today}.
"""

USER_TEMPLATE = """Question: {query}

Context chunks:
{context}

Answer:"""


def _format_context(reranked) -> str:
    blocks = []
    for doc, score in reranked:
        md = doc["metadata"]
        tag = f"{md.get('source_document', '?')} §{md.get('section_header', '?')}"
        blocks.append(f"[{tag}] (rel={score:.2f})\n{doc['text']}")
    return "\n\n".join(blocks)


def _citations(reranked) -> list[str]:
    seen, out = set(), []
    for doc, _ in reranked:
        md = doc["metadata"]
        tag = f"{md.get('source_document', '?')} §{md.get('section_header', '?')}"
        if tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


_BINDING_RE = re.compile(
    r"binding(?:\s+agreement)?\s+date[:\s]+"
    r"([A-Z][a-z]+ \d{1,2},? \d{4}|\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE)

# Only compute deadlines for known, named contractual periods — never arbitrary
# "N days" phrases in statutory prose (review fix #3). Each entry maps a label to
# the regex that captures its day count.
_KNOWN_PERIODS = {
    "Due Diligence Period": re.compile(
        r"due\s+diligence\s+period[:\s]+(?:runs?\s+for\s+)?(\d{1,3})\s+(?:calendar\s+)?days",
        re.IGNORECASE),
    "Counteroffer Response": re.compile(
        r"(\d{1,3})\s+days\s+to\s+respond", re.IGNORECASE),
}


def _parse_date(s: str) -> dt.date | None:
    for fmt in ("%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _user_contract_text(reranked) -> str:
    """Concatenate ONLY the buyer's executed-agreement chunks.

    The binding date and personal periods must come from the user's contract, not
    from generic statutory examples in the base corpus (review fix #3).
    """
    return "\n".join(
        d["text"] for d, _ in reranked
        if d.get("metadata", {}).get("document_type") == "user_agreement"
    )


def precompute_deadlines(reranked) -> str:
    """Deterministically compute deadlines from the user contract's binding date
    plus its named periods, so GPT-4o narrates dates we calculated rather than
    doing arithmetic itself (PRD §5.1, §11 mitigation)."""
    text = _user_contract_text(reranked)
    if not text:
        return ""
    bm = _BINDING_RE.search(text)
    binding = _parse_date(bm.group(1)) if bm else None
    if not binding:
        return ""

    lines = [f"Binding Agreement Date: {binding.isoformat()}"]
    for label, pattern in _KNOWN_PERIODS.items():
        m = pattern.search(text)
        if not m:
            continue
        days = int(m.group(1))
        deadline = deadline_from(binding, days)
        lines.append(f"{label} ({days} days) -> deadline {deadline.isoformat()} "
                     f"({days_until(deadline)} days from today)")
    if len(lines) == 1:  # binding date found but no recognized periods
        return ""
    return "PRECOMPUTED DEADLINES (authoritative — use these exact dates):\n" + "\n".join(lines)


def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


def generator(state: RAGState) -> RAGState:
    reranked = state["reranked_chunks"]
    context = _format_context(reranked)
    deadlines = precompute_deadlines(reranked)
    if deadlines:
        context = f"{deadlines}\n\n{context}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(today=dt.date.today().isoformat())},
        {"role": "user", "content": USER_TEMPLATE.format(query=state["query"], context=context)},
    ]

    resp = _client().chat.completions.create(
        model=settings.generation_model, messages=messages, temperature=0.0,
    )
    state["answer"] = resp.choices[0].message.content
    state["source_citations"] = _citations(reranked)
    state["escalated"] = False
    return state
