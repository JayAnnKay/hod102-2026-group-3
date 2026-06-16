import streamlit as st

st.set_page_config(page_title="Running Coach", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "Chat"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan" not in st.session_state:
    st.session_state.plan = ""

with st.sidebar:
    st.title("Running Coach")
    st.session_state.page = st.radio(
        "Navigate",
        ["Chat", "Current Plan", "User Profile", "Training History"],
        index=["Chat", "Current Plan", "User Profile", "Training History"].index(
            st.session_state.page
        ),
    )

if st.session_state.page == "Chat":
    from app.chat import render
    render()
elif st.session_state.page == "Current Plan":
    from app.plan_view import render
    render()
elif st.session_state.page == "User Profile":
    from app.profile import render
    render()
elif st.session_state.page == "Training History":
    from app.history import render
    render()
