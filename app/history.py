import streamlit as st
import pandas as pd
from core.data_io import load_runner


def render():
    st.title("Training History")

    runner = load_runner()
    sessions = runner.get("sessions", [])

    if not sessions:
        st.info("No training sessions logged yet.")
        return

    df = pd.DataFrame(sessions)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    total_km = df["km"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total sessions", len(df))
    col2.metric("Total distance", f"{total_km:.1f} km")
    col3.metric("Avg per session", f"{total_km / len(df):.1f} km")

    st.subheader("Weekly distance (km)")
    weekly = df.set_index("date")["km"].resample("W").sum()
    st.bar_chart(weekly)

    st.subheader("All sessions")
    display = df.rename(columns={
        "date": "Date",
        "km": "Distance (km)",
        "pace": "Pace (/km)",
        "type": "Type"
    })
    display["Type"] = display["Type"].str.capitalize()
    st.dataframe(display, use_container_width=True, hide_index=True)
