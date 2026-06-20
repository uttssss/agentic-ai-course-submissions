"""Streamlit UI for the Build-in-Public Content Agent (Week 3).

Run with:  make run-agent
"""
from __future__ import annotations

import re
import traceback
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
    st.session_state.phase = "input"
    st.session_state.checkpointer = MemorySaver()
    st.session_state.app = None
    st.session_state.pending_state: dict = {}
    st.session_state.published_url: str | None = None
    st.session_state.error_log: list[str] = []
    st.session_state.last_error: str = ""


def _get_app():
    if st.session_state.app is None:
        st.session_state.app = build_content_graph(st.session_state.checkpointer)
    return st.session_state.app


def _config() -> dict:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def _parse_repo(value: str) -> str:
    """Accept 'owner/repo' or any GitHub URL and return just 'owner/repo'."""
    value = value.strip()
    # Match https://github.com/owner/repo (ignore trailing path)
    m = re.search(r"github\.com/([^/]+/[^/\s]+)", value)
    if m:
        return m.group(1).rstrip("/")
    return value


# ── Phase: Input ─────────────────────────────────────────────────────────────
if st.session_state.phase == "input":
    if st.session_state.last_error:
        st.error(st.session_state.last_error)
        st.session_state.last_error = ""

    with st.form("inputs"):
        st.subheader("Week inputs")
        col1, col2 = st.columns(2)
        with col1:
            week = st.number_input("Week number", min_value=1, max_value=52, value=3, step=1)
            github_repo = st.text_input(
                "GitHub project repo (owner/repo or full URL)",
                placeholder="yourname/my-week3-project",
            )
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
            "github_repo": _parse_repo(github_repo),
            "critic_revision_count": 0,
            "error_log": [],
        }

        st.session_state.phase = "running"
        st.session_state.initial_state = initial_state
        st.rerun()

# ── Phase: Running ────────────────────────────────────────────────────────────
elif st.session_state.phase == "running":
    st.info("Agent running: ingesting → planning → retrieving → drafting → critiquing…  \nThis takes 2–5 minutes. Do not close this tab.")
    with st.spinner("Working…"):
        try:
            app = _get_app()
            app.invoke(st.session_state.initial_state, config=_config())
            graph_state = app.get_state(_config())

            if graph_state.next:
                st.session_state.pending_state = graph_state.values
                st.session_state.phase = "review"
            else:
                st.session_state.published_url = graph_state.values.get("published_url")
                st.session_state.error_log = graph_state.values.get("error_log", [])
                st.session_state.phase = "done"
        except Exception as exc:
            st.session_state.last_error = (
                f"Agent error: {exc}\n\n```\n{traceback.format_exc()}\n```"
            )
            st.session_state.phase = "input"
            # Reset graph so next run starts fresh
            st.session_state.app = None
            st.session_state.thread_id = uuid.uuid4().hex
    st.rerun()

# ── Phase: Human review gate ──────────────────────────────────────────────────
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

    if not drafts:
        st.warning("No drafts were generated. Check agent warnings below.")

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
            if feedback and feedback.lower() not in ("approved", ""):
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
            st.session_state.resume_payload = {"decision": "approve", "edited_drafts": approved_drafts}
            st.rerun()

    with col2:
        if st.button("🔁 Regenerate drafts"):
            st.session_state.phase = "publishing"
            st.session_state.resume_payload = {"decision": "regenerate", "edited_drafts": None}
            st.rerun()

    with col3:
        if st.button("❌ Reject / start over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ── Phase: Publishing ─────────────────────────────────────────────────────────
elif st.session_state.phase == "publishing":
    payload = st.session_state.get("resume_payload", {"decision": "reject"})
    spinner_msg = "Regenerating drafts…" if payload["decision"] == "regenerate" else "Publishing to GitHub Pages…"

    with st.spinner(spinner_msg):
        try:
            app = _get_app()
            app.invoke(Command(resume=payload), config=_config())
            graph_state = app.get_state(_config())

            if graph_state.next:
                st.session_state.pending_state = graph_state.values
                st.session_state.phase = "review"
            else:
                st.session_state.published_url = graph_state.values.get("published_url")
                st.session_state.error_log = graph_state.values.get("error_log", [])
                st.session_state.phase = "done"
        except Exception as exc:
            st.session_state.last_error = f"Publish error: {exc}\n\n```\n{traceback.format_exc()}\n```"
            st.session_state.phase = "review"
    st.rerun()

# ── Phase: Done ───────────────────────────────────────────────────────────────
elif st.session_state.phase == "done":
    st.success("Done!")
    url = st.session_state.published_url
    if url:
        st.markdown(f"**Published:** [{url}]({url})")
        st.info("LinkedIn draft: copy from the drafts above and post manually.")
    else:
        st.warning("No URL returned — check agent warnings below.")

    for e in st.session_state.error_log:
        st.warning(e)

    if st.button("Run another week"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
