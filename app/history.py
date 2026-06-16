import streamlit as st
import pandas as pd
from core.data_io import load_runner


def render():
    st.title("Training History")

    runner = load_runner()
    sessions = runner.get("sessions", [])

    if not sessions:
        st.info("No training sessions found.")
        return

    df = pd.DataFrame(sessions)
    df.columns = ["Date", "Distance (km)", "Pace (/km)", "Type"]
    df["Type"] = df["Type"].str.capitalize()

    st.dataframe(df, use_container_width=True, hide_index=True)
