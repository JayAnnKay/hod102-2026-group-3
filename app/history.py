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
    st.title("🏃 Training History")

    runner = load_runner()
    sessions = runner.get("sessions", [])

    if not sessions:
        st.info("No training sessions found. Time to lace up those shoes!")
        return

    df = pd.DataFrame(sessions)
    column_mapping = {"date": "Date", "km": "Distance (km)", "pace": "Pace (/km)", "type": "Type"}
    df = df[list(column_mapping.keys())].rename(columns=column_mapping)
    df["Type"] = df["Type"].str.capitalize()
    df["Date"] = pd.to_datetime(df["Date"])

    run_types = df["Type"].unique()
    selected_types = st.sidebar.multiselect("Filter by Run Type", options=run_types, default=run_types)
    filtered_df = df[df["Type"].isin(selected_types)]

    st.subheader("Quick Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Runs", len(filtered_df))
    col2.metric("Total Distance", f"{filtered_df['Distance (km)'].sum():.1f} km")

    if not filtered_df.empty:
        avg_seconds = filtered_df["Pace (/km)"].apply(pace_to_seconds).mean()
        avg_pace_str = seconds_to_pace(avg_seconds)
    else:
        avg_pace_str = "0:00"
    col3.metric("Avg Pace", f"{avg_pace_str} /km")

    st.subheader("Weekly distance (km)")
    weekly = filtered_df.set_index("Date")["Distance (km)"].resample("W").sum()
    st.bar_chart(weekly)

    st.subheader("Progress Chart")
    st.line_chart(filtered_df, x="Date", y="Distance (km)", use_container_width=True)

    st.subheader("All Sessions")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
