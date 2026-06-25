import streamlit as st
import pandas as pd
from core.db import db_get_current_plan
from core.data_io import get_runner_id


_SESSION_TYPE_ICON = {
    "intervals": "⚡", "tempo": "⚡", "speed": "⚡",
    "long": "🏔️",
    "recovery": "🔄", "rest": "🔄",
    "easy": "🏃",
}

def _guess_type(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ("interval", "tempo", "speed")):
        return "Intervals"
    if "long" in t:
        return "Long"
    if any(k in t for k in ("recovery", "rest")):
        return "Recovery"
    return "Easy"


def _plan_to_rows(content: str, structured: dict) -> list[dict]:
    """Convert plan content or structured JSON into flat session rows."""
    rows = []

    # Try structured JSON first (saved by agent as {"weeks": [...]})
    if structured and structured.get("weeks"):
        for w in structured["weeks"]:
            week_num = w.get("week", "")
            focus = w.get("focus", "")
            label = f"Week {week_num}" + (f" — {focus}" if focus else "")
            for s in w.get("sessions", []):
                desc = s.get("description", s.get("workout", ""))
                rows.append({
                    "Week": label,
                    "Day": s.get("day", ""),
                    "Type": s.get("type", _guess_type(desc)).capitalize(),
                    "Session": desc,
                })
        if rows:
            return rows

    # Fall back to parsing the plain-text content
    current_week = ""
    for line in (content or "").strip().split("\n"):
        line = line.strip().lstrip("-*• ")
        if not line:
            continue
        if line.lower().startswith("week") or line.lower().startswith("phase"):
            parts = line.split(":", 1)
            current_week = parts[0].strip()
            if len(parts) > 1 and parts[1].strip():
                current_week += f" — {parts[1].strip()}"
        elif current_week and ":" in line:
            parts = line.split(":", 1)
            day = parts[0].strip()
            session = parts[1].strip()
            rows.append({
                "Week": current_week,
                "Day": day,
                "Type": _guess_type(session),
                "Session": session,
            })

    return rows


def render():
    st.markdown(
        "<h2 style='font-size:1.6rem!important;font-weight:800;margin-bottom:0.2rem'>Training Plan</h2>"
        "<p style='color:rgba(255,255,255,0.4)!important;font-size:0.85rem;margin-bottom:1.2rem'>Your active protocol</p>",
        unsafe_allow_html=True,
    )

    runner_id = st.session_state.get("runner_id") or get_runner_id()
    plan = ""
    structured = {}
    if runner_id:
        stored = db_get_current_plan(runner_id)
        plan = stored.get("content", "")
        structured = stored.get("structured") or {}
        if plan:
            st.session_state.plan = plan

    if not plan:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);"
            "border-radius:20px;padding:2rem;text-align:center;margin-bottom:1rem'>"
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

    rows = _plan_to_rows(plan, structured)

    if not rows:
        # Couldn't parse structure — show raw text so plan is always readable
        st.markdown(plan)
        return

    df = pd.DataFrame(rows)

    # Summary stats
    weeks = df["Week"].unique()
    total_sessions = len(df)
    st.markdown(
        f"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);"
        f"border-radius:20px;padding:1.2rem;margin-bottom:1rem'>"
        f"<div style='display:flex;justify-content:space-around;text-align:center'>"
        f"<div><div style='color:rgba(255,255,255,0.45);font-size:0.7rem;text-transform:uppercase;"
        f"letter-spacing:1px;margin-bottom:4px'>Weeks</div>"
        f"<div style='color:#CCFF00;font-weight:800;font-size:1.6rem'>{len(weeks)}</div></div>"
        f"<div style='border-left:1px solid rgba(255,255,255,0.08);padding-left:1.5rem'>"
        f"<div style='color:rgba(255,255,255,0.45);font-size:0.7rem;text-transform:uppercase;"
        f"letter-spacing:1px;margin-bottom:4px'>Sessions</div>"
        f"<div style='color:#00F0FF;font-weight:800;font-size:1.6rem'>{total_sessions}</div></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # Week filter
    selected_weeks = st.multiselect(
        "Filter by week", options=list(weeks), default=list(weeks), key="plan_week_filter"
    )
    filtered = df[df["Week"].isin(selected_weeks)] if selected_weeks else df

    st.dataframe(filtered, use_container_width=True, hide_index=True)