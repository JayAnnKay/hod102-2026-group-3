import streamlit as st
from core.data_io import load_runner, save_runner


def render():
    st.title("User Profile")

    if "runner" not in st.session_state:
        st.session_state.runner = load_runner()

    runner = st.session_state.runner

    st.table(
        {
            "Field": ["First name", "City", "Gender", "Goals", "Constraints & injuries"],
            "Value": [
                runner.get("first_name", ""),
                runner.get("city", ""),
                runner.get("gender", ""),
                runner.get("goals", ""),
                runner.get("constraints", ""),
            ],
        }
    )

    with st.expander("Modify"):
        with st.form("profile_form"):
            goals = st.text_input("Goals", value=runner.get("goals", ""))
            constraints = st.text_input(
                "Constraints & injuries", value=runner.get("constraints", "")
            )
            if st.form_submit_button("Save"):
                st.session_state.runner["goals"] = goals
                st.session_state.runner["constraints"] = constraints
                save_runner(st.session_state.runner)
                st.success("Saved!")
