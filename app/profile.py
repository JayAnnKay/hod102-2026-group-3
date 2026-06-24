"""Screen 3 - User profile (app/profile.py).

The profile is STORED state, not a per-launch questionnaire:
  open -> load saved profile -> show flat -> Modify -> validated form -> save.
The chat (Day 3) writes to the SAME json via core.data_io; this form is the
manual editor + the Day-1 way to set the profile while chat is hard-coded.

Wire into main.py by calling `profile.render()` when the Profile tab is active.
Standalone test: `streamlit run app/profile.py`
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `core` importable whether run via main.py or standalone.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from core import data_io
from core.profile_model import (
    CONSTRAINT_KINDS,
    DAYS,
    GENDERS,
    SEVERITIES,
    RunnerProfile,
    default_profile,
    to_display_rows,
)


def _constraints_to_df(profile: RunnerProfile) -> pd.DataFrame:
    rows = [
        {"kind": c.kind, "area": c.area or "", "note": c.note,
         "severity": c.severity or "", "active": c.active}
        for c in profile.constraints
    ]
    if not rows:
        rows = [{"kind": "other", "area": "", "note": "", "severity": "", "active": True}]
    return pd.DataFrame(rows)


def _df_to_constraints(df: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        note = str(r.get("note", "")).strip()
        area = str(r.get("area", "")).strip()
        if not note and not area:
            continue  # drop empty rows
        sev = str(r.get("severity", "")).strip()
        out.append(
            {
                "kind": r.get("kind", "other"),
                "area": area or None,
                "note": note,
                "severity": sev or None,
                "active": bool(r.get("active", True)),
            }
        )
    return out


def render() -> None:
    st.header("User profile")
    st.caption("What the app knows about the runner.")

    if "profile" not in st.session_state:
        raw = data_io.load_profile()  # dict from core; {} on first run
        st.session_state.profile = (
            RunnerProfile.model_validate(raw) if raw else default_profile()
        )
    profile: RunnerProfile = st.session_state.profile

    # ---------------- READ MODE (flat display) ----------------
    if not st.session_state.get("editing_profile"):
        for label, value in to_display_rows(profile):
            c1, c2 = st.columns([1, 2])
            c1.markdown(f"**{label}**")
            c2.write(value)
        st.divider()
        if st.button("Modify"):
            st.session_state.editing_profile = True
            st.rerun()
        return

    # ---------------- EDIT MODE (typed, validated form) ----------------
    with st.form("profile_form"):
        st.subheader("Identity")
        first_name = st.text_input("First name", profile.identity.first_name)
        city = st.text_input("City", profile.identity.city or "")
        gender = st.selectbox(
            "Gender",
            [""] + GENDERS,
            index=([""] + GENDERS).index(profile.identity.gender or ""),
        )

        st.subheader("Goal")
        race_type = st.text_input("Race / goal type", profile.goal.race_type)
        target_distance = st.number_input(
            "Target distance (km, 0 = unset)", min_value=0.0, max_value=500.0,
            value=float(profile.goal.target_distance_km or 0), step=0.5,
        )
        target_time = st.text_input(
            "Target time (MM:SS or HH:MM:SS)", profile.goal.target_time or ""
        )
        no_date = st.checkbox("No fixed race date", value=profile.goal.race_date is None)
        race_date = st.date_input("Race date", value=profile.goal.race_date or None)
        horizon = st.number_input(
            "Horizon (weeks, 0 = unset)", min_value=0, max_value=104,
            value=profile.goal.horizon_weeks or 0,
        )

        st.subheader("Availability")
        spw = st.number_input(
            "Sessions per week", min_value=1, max_value=14,
            value=profile.availability.sessions_per_week,
        )
        pref_days = st.multiselect(
            "Preferred days", DAYS, default=profile.availability.preferred_days
        )
        max_min = st.number_input(
            "Max session minutes (0 = unset)", min_value=0, max_value=600,
            value=profile.availability.max_session_min or 0,
        )

        st.subheader("Constraints & injuries")
        cons_df = st.data_editor(
            _constraints_to_df(profile),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "kind": st.column_config.SelectboxColumn("Kind", options=CONSTRAINT_KINDS),
                "area": st.column_config.TextColumn("Area"),
                "note": st.column_config.TextColumn("Note"),
                "severity": st.column_config.SelectboxColumn("Severity", options=[""] + SEVERITIES),
                "active": st.column_config.CheckboxColumn("Active"),
            },
            key="cons_editor",
        )

        submitted = st.form_submit_button("Save", type="primary")

    # Cancel lives outside the form (forms only allow form_submit_button).
    if st.button("Cancel"):
        st.session_state.editing_profile = False
        st.rerun()

    if submitted:
        try:
            new = RunnerProfile.model_validate(
                {
                    "identity": {
                        "first_name": first_name,
                        "city": city or None,
                        "gender": gender or None,
                    },
                    "goal": {
                        "race_type": race_type,
                        "target_distance_km": target_distance or None,
                        "target_time": target_time or None,
                        "race_date": None if no_date else race_date,
                        "horizon_weeks": horizon or None,
                    },
                    "availability": {
                        "sessions_per_week": int(spw),
                        "preferred_days": pref_days,
                        "max_session_min": int(max_min) or None,
                    },
                    "constraints": _df_to_constraints(cons_df),
                    "notes": profile.notes,
                }
            )
        except ValidationError as e:
            st.error("Couldn't save - fix these:")
            for err in e.errors():
                loc = ".".join(str(p) for p in err["loc"])
                st.write(f"- `{loc}`: {err['msg']}")
        else:
            data_io.save_profile(new.model_dump(mode="json"))
            st.session_state.profile = new
            st.session_state.editing_profile = False
            st.success("Profile saved.")
            st.rerun()


if __name__ == "__main__":
    render()