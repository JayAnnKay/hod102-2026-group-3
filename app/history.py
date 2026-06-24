import streamlit as st
import pandas as pd
from core.data_io import load_runner


def pace_to_seconds(pace_str):
    try:
        parts = str(pace_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return 0


def seconds_to_pace(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0:
        return "0:00"
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def render():
    st.markdown(
        "<h2 style='font-size:1.6rem!important;font-weight:800;margin-bottom:0.2rem'>Analytics</h2>"
        "<p style='color:rgba(255,255,255,0.4)!important;font-size:0.85rem;margin-bottom:1.2rem'>Performance logs</p>",
        unsafe_allow_html=True,
    )

    runner = load_runner()
    sessions = runner.get("sessions", [])

    if not sessions:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);"
            "border-radius:20px;padding:2rem;text-align:center'>"
            "<div style='font-size:2.5rem;margin-bottom:0.8rem'>👟</div>"
            "<p style='font-weight:700;font-size:1.1rem;margin-bottom:0.4rem'>No data yet</p>"
            "<p style='color:rgba(255,255,255,0.5)!important;font-size:0.85rem'>Log your first session to unlock analytics.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # DataFrame
    df = pd.DataFrame(sessions)
    column_mapping = {"date": "Date", "km": "Distance (km)", "pace": "Pace (/km)", "type": "Type"}
    df = df[list(column_mapping.keys())].rename(columns=column_mapping)
    df["Type"] = df["Type"].str.capitalize()
    df["Date"] = pd.to_datetime(df["Date"])

    # Filter
    run_types = df["Type"].unique()
    selected_types = st.multiselect("Filter by run type", options=run_types, default=run_types)
    filtered_df = df[df["Type"].isin(selected_types)]

    # Stats
    if not filtered_df.empty:
        avg_seconds = filtered_df["Pace (/km)"].apply(pace_to_seconds).mean()
        avg_pace_str = seconds_to_pace(avg_seconds)
    else:
        avg_pace_str = "0:00"

    total_runs = len(filtered_df)
    total_dist = filtered_df["Distance (km)"].sum()

    st.markdown(
        f"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);"
        f"border-radius:20px;padding:1.2rem;margin-bottom:1rem'>"
        f"<div style='display:flex;justify-content:space-around;text-align:center'>"
        f"<div>"
        f"<div style='color:rgba(255,255,255,0.45);font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>Runs</div>"
        f"<div style='color:#CCFF00;font-weight:800;font-size:1.6rem'>{total_runs}</div>"
        f"</div>"
        f"<div style='border-left:1px solid rgba(255,255,255,0.08);padding-left:1.5rem'>"
        f"<div style='color:rgba(255,255,255,0.45);font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>Distance</div>"
        f"<div style='color:#00F0FF;font-weight:800;font-size:1.6rem'>{total_dist:.1f} <span style='font-size:0.75rem;font-weight:600'>km</span></div>"
        f"</div>"
        f"<div style='border-left:1px solid rgba(255,255,255,0.08);padding-left:1.5rem'>"
        f"<div style='color:rgba(255,255,255,0.45);font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>Avg Pace</div>"
        f"<div style='font-weight:800;font-size:1.6rem'>{avg_pace_str}</div>"
        f"</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # Charts
    st.markdown("<p style='font-weight:700;font-size:0.95rem;margin:1rem 0 0.5rem 0'>Weekly Volume</p>", unsafe_allow_html=True)
    weekly = filtered_df.set_index("Date")["Distance (km)"].resample("W").sum()
    st.bar_chart(weekly)

    st.markdown("<p style='font-weight:700;font-size:0.95rem;margin:1rem 0 0.5rem 0'>Distance Over Time</p>", unsafe_allow_html=True)
    st.line_chart(filtered_df, x="Date", y="Distance (km)", use_container_width=True)

    st.markdown("<p style='font-weight:700;font-size:0.95rem;margin:1rem 0 0.5rem 0'>All Sessions</p>", unsafe_allow_html=True)
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
