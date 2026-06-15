"""Streamlit web chat (PRD §3).

Chat + PDF upload. Renders citations, upload status, and escalation messaging.
Run with:  streamlit run copilot/app/streamlit_app.py
"""
from __future__ import annotations

import uuid

import streamlit as st

from copilot.graph.build import run_graph
from copilot.ingest.ingest_user_contract import ingest_user_contract

st.set_page_config(page_title="Real Estate Contract Copilot", page_icon="🏠")
st.title("🏠 Real Estate Transaction & Contract Copilot")

# --- Session bootstrap ---
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state.history = []
    st.session_state.contract_ready = False

# --- Sidebar: profile + contract upload ---
with st.sidebar:
    st.header("Your transaction")
    state = st.selectbox("Property state", ["GA", "FL", "TX", "CA"], index=0)
    county = st.text_input("County", "Fulton")
    user_geo = {"state": state, "county": county}

    uploaded = st.file_uploader("Upload executed purchase agreement (PDF)", type=["pdf"])
    if uploaded and not st.session_state.contract_ready:
        with st.spinner("Parsing your contract…"):
            tmp = f"/tmp/{uploaded.name}"
            with open(tmp, "wb") as f:
                f.write(uploaded.read())
            result = ingest_user_contract(tmp, st.session_state.session_id, user_geo)
        st.session_state.contract_ready = result["chunks_indexed"] > 0
        st.success(f"Indexed {result['chunks_indexed']} chunks from your contract.")
        if result["failed"]:
            st.warning(f"{len(result['failed'])} chunks failed metadata validation.")

# --- Chat history ---
for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("citations"):
            st.caption("Sources: " + " · ".join(turn["citations"]))

def _needs_contract(text: str) -> bool:
    """Heuristic: does the question depend on the user's own executed contract?
    Used to block contract-specific answers until upload ingestion completes
    (spec §7.2, review fix #5)."""
    t = text.lower()
    cues = ["my contract", "my closing", "my due diligence", "my deadline",
            "my lender", "my earnest", "my agreement", "based on my", "in my contract"]
    return any(c in t for c in cues)


# --- Input ---
if prompt := st.chat_input("Ask about your deadlines, contingencies, or rights…"):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if _needs_contract(prompt) and not st.session_state.contract_ready:
            resp = {
                "answer": ("This question depends on your executed purchase "
                           "agreement. Please upload it in the sidebar so I can "
                           "give you accurate, contract-specific dates."),
                "escalated": False, "escalation_reason": None,
                "citations": [], "top_score": 0.0, "latency_ms": 0,
            }
            st.markdown(resp["answer"])
        else:
            with st.spinner("Thinking…"):
                resp = run_graph(prompt, user_geo, st.session_state.session_id)
            st.markdown(resp["answer"])
            if resp["escalated"]:
                st.info(f"Escalated to your agent ({resp['escalation_reason']}).")
            elif resp["citations"]:
                st.caption("Sources: " + " · ".join(resp["citations"]))
            st.caption(f"latency: {resp['latency_ms']} ms · top_score: {resp['top_score']:.2f}")

    st.session_state.history.append({
        "role": "assistant", "content": resp["answer"], "citations": resp["citations"],
    })
