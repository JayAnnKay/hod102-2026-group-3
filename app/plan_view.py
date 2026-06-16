import streamlit as st


def render():
    st.title("Current Plan")
    plan = st.session_state.get("plan", "")
    if plan:
        st.code(plan, language=None)
    else:
        st.info("No plan yet. Go to Chat and click 'Generate a training plan'.")
