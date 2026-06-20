"""Streamlit UI for the Build-in-Public Content Agent (Week 3).

Run with:  streamlit run copilot/app/content_agent_app.py
"""
from __future__ import annotations

import uuid

import streamlit as st
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from copilot.agent.build import build_content_graph
from copilot.agent.state import ContentAgentState, Draft

st.set_page_config(page_title="Build-in-Public Content Agent", page_icon="✍️", layout="wide")
st.title("✍️ Build-in-Public Content Agent")
st.caption("Turn a week's course materials + project into publish-ready LinkedIn & blog posts.")

# ── Session bootstrap ────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.phase = "input"      # input → running → review → done
    st.session_state.checkpointer = MemorySaver()
    st.session_state.app = None
    st.session_state.pending_state: dict = {}
    st.session_state.published_url: str | None = None
    st.session_state.error_log: list[str] = []


def _get_app():
    if st.session_state.app is None:
        st.session_state.app = build_content_graph(st.session_state.checkpointer)
    return st.session_state.app


def _config() -> dict:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


# ── Phase 1: Inputs ──────────────────────────────────────────────────────────
if st.session_state.phase == "input":
    with st.form("inputs"):
        st.subheader("Week inputs")
        col1, col2 = st.columns(2)
        with col1:
            week = st.number_input("Week number", min_value=1, max_value=52, value=3, step=1)
            github_repo = st.text_input("GitHub project repo (owner/repo)", placeholder="yourname/my-week3-project")
        with col2:
            materials_files = st.file_uploader(
                "Course materials (PDF / Markdown)", type=["pdf", "md", "txt"],
                accept_multiple_files=True,
            )
            notes_files = st.file_uploader(
                "My notes (PDF / Markdown)", type=["pdf", "md", "txt"],
                accept_multiple_files=True,
            )

        submitted = st.form_submit_button("Run content agent →", type="primary")

    if submitted:
        # Save uploaded files to /tmp
        def _save_uploads(uploads) -> list[str]:
            paths = []
            for f in (uploads or []):
                dest = f"/tmp/content_agent_{f.name}"
                with open(dest, "wb") as out:
                    out.write(f.read())
                paths.append(dest)
            return paths

        initial_state: ContentAgentState = {
            "week": int(week),
            "materials_paths": _save_uploads(materials_files),
            "notes_paths": _save_uploads(notes_files),
            "github_repo": github_repo.strip(),
            "critic_revision_count": 0,
            "error_log": [],
        }

        st.session_state.phase = "running"
        st.session_state.initial_state = initial_state
        st.rerun()

# ── Phase: Running ───────────────────────────────────────────────────────────
elif st.session_state.phase == "running":
    with st.spinner("Agent running: ingesting → planning → retrieving → drafting → critiquing…"):
        try:
            app = _get_app()
            app.invoke(st.session_state.initial_state, config=_config())
            graph_state = app.get_state(_config())

            if graph_state.next:
                # Graph is interrupted at human_gate — surface drafts for review
                st.session_state.pending_state = graph_state.values
                st.session_state.phase = "review"
            else:
                # Completed without interrupt (edge case)
                st.session_state.published_url = graph_state.values.get("published_url")
                st.session_state.error_log = graph_state.values.get("error_log", [])
                st.session_state.phase = "done"
        except Exception as exc:
            st.error(f"Agent error: {exc}")
            st.session_state.phase = "input"
    st.rerun()

# ── Phase: Human review gate ─────────────────────────────────────────────────
elif st.session_state.phase == "review":
    pending = st.session_state.pending_state
    drafts: list[Draft] = pending.get("drafts", [])
    themes = pending.get("themes", [])
    revision_count = pending.get("critic_revision_count", 0)
    errors = pending.get("error_log", [])

    st.subheader("Planned themes")
    for i, t in enumerate(themes, 1):
        with st.expander(f"Theme {i}: {t.get('concept', '')}"):
            st.write(f"**My angle:** {t.get('note_angle', '')}")
            st.write(f"**Build evidence:** {t.get('build_evidence', '')}")

    st.subheader("Draft posts (review before publishing)")
    if revision_count > 0:
        st.info(f"Critic ran {revision_count} revision round(s) before surfacing these drafts.")

    edited_contents: dict[str, str] = {}
    for draft in drafts:
        platform = draft.get("platform", "")
        score = draft.get("critic_score", 0.0)
        feedback = draft.get("critic_feedback", "")
        score_color = "green" if score >= 3.5 else "orange" if score >= 2.5 else "red"

        with st.expander(f"{'LinkedIn' if platform == 'linkedin' else 'Substack / Blog'} draft", expanded=True):
            st.markdown(f"**Critic score:** :{score_color}[{score:.1f} / 5]")
            if feedback and feedback.lower() != "approved":
                st.caption(f"Critic note: {feedback}")
            edited_contents[platform] = st.text_area(
                "Edit draft (optional):", value=draft.get("content", ""),
                height=300 if platform == "linkedin" else 500,
                key=f"draft_{platform}",
            )

    if errors:
        with st.expander("Agent warnings"):
            for e in errors:
                st.warning(e)

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve & publish", type="primary"):
            approved_drafts = [
                {**d, "content": edited_contents.get(d["platform"], d["content"])}
                for d in drafts
            ]
            st.session_state.phase = "publishing"
            st.session_state.resume_payload = {
                "decision": "approve",
                "edited_drafts": approved_drafts,
            }
            st.rerun()

    with col2:
        if st.button("🔁 Regenerate drafts"):
            st.session_state.phase = "publishing"
            st.session_state.resume_payload = {"decision": "regenerate", "edited_drafts": None}
            st.rerun()

    with col3:
        if st.button("❌ Reject / start over"):
            # Reset session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ── Phase: Publishing (resume after interrupt) ────────────────────────────────
elif st.session_state.phase == "publishing":
    payload = st.session_state.get("resume_payload", {"decision": "reject"})

    if payload["decision"] == "regenerate":
        spinner_msg = "Regenerating drafts…"
    else:
        spinner_msg = "Publishing approved post to GitHub Pages…"

    with st.spinner(spinner_msg):
        try:
            app = _get_app()
            app.invoke(Command(resume=payload), config=_config())
            graph_state = app.get_state(_config())

            if graph_state.next:
                # Interrupted again (regeneration loop came back to human_gate)
                st.session_state.pending_state = graph_state.values
                st.session_state.phase = "review"
            else:
                st.session_state.published_url = graph_state.values.get("published_url")
                st.session_state.error_log = graph_state.values.get("error_log", [])
                st.session_state.phase = "done"
        except Exception as exc:
            st.error(f"Resume error: {exc}")
            st.session_state.phase = "review"
    st.rerun()

# ── Phase: Done ───────────────────────────────────────────────────────────────
elif st.session_state.phase == "done":
    st.success("Done!")
    url = st.session_state.published_url
    if url:
        st.markdown(f"**Published:** [{url}]({url})")
        st.info("LinkedIn draft is in the approved drafts above — copy and post manually.")
    else:
        st.warning("No URL returned. Check GitHub Pages configuration or agent warnings.")

    for e in st.session_state.error_log:
        st.warning(e)

    if st.button("Run another week"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
