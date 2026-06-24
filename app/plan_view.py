import streamlit as st
from core.db import db_get_current_plan
from core.data_io import get_runner_id


def _parse_plan(plan_text: str):
    """Parse plan text into structured weeks."""
    weeks = []
    current = None
    for line in plan_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("week") or line.lower().startswith("phase"):
            if current:
                weeks.append(current)
            current = {"title": line, "workouts": []}
        elif current is not None and ":" in line:
            current["workouts"].append(line)
    if current:
        weeks.append(current)
    return weeks


def render():
    st.markdown(
        "<h2 style='font-size:1.6rem!important;font-weight:800;margin-bottom:0.2rem'>Training Plan</h2>"
        "<p style='color:rgba(255,255,255,0.4)!important;font-size:0.85rem;margin-bottom:1.2rem'>Your active protocol</p>",
        unsafe_allow_html=True,
    )

    # check session state first (plan was just generated this session)
    # if empty (e.g. after a refresh), load whatever was last saved in DB
    plan = st.session_state.get("plan", "")
    if not plan:
        runner_id = st.session_state.get("runner_id") or get_runner_id()
        if runner_id:
            stored = db_get_current_plan(runner_id)
            plan = stored.get("content", "")
            if plan:
                st.session_state.plan = plan  # cache it so we don't re-query every render

    if not plan:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:20px;padding:2rem;text-align:center;margin-bottom:1rem'>"
            "<div style='font-size:2.5rem;margin-bottom:0.8rem'>📋</div>"
            "<p style='font-weight:700;font-size:1.1rem;margin-bottom:0.4rem'>No plan yet</p>"
            "<p style='color:rgba(255,255,255,0.5)!important;font-size:0.85rem;line-height:1.6'>"
            "Go to Chat and generate your personalised training plan.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Go to Chat", use_container_width=True):
            st.session_state.page = "Chat"
            st.rerun()
        return

    weeks = _parse_plan(plan)

    for week in weeks:
        workouts_html = ""
        for w in week["workouts"]:
            parts = w.split(":", 1)
            day = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else w

            # Pick icon
            dl = desc.lower()
            if "interval" in dl or "tempo" in dl:
                icon = "⚡"
            elif "long" in dl:
                icon = "🏔️"
            else:
                icon = "🏃"

            workouts_html += (
                f"<div style='display:flex;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05)'>"
                f"<span style='font-size:1.2rem;margin-right:10px'>{icon}</span>"
                f"<span style='color:rgba(255,255,255,0.5);font-size:0.8rem;font-weight:700;width:40px;flex-shrink:0'>{day}</span>"
                f"<span style='font-size:0.9rem;font-weight:500'>{desc}</span>"
                f"</div>"
            )

        st.markdown(
            f"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);"
            f"border-radius:20px;padding:1.2rem;margin-bottom:0.8rem;border-left:3px solid #CCFF00'>"
            f"<p style='color:#CCFF00!important;font-size:0.8rem!important;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:1px;margin-bottom:0.5rem'>{week['title']}</p>"
            f"{workouts_html}"
            f"</div>",
            unsafe_allow_html=True,
        )