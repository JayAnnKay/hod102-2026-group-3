import streamlit as st
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Running Coach", layout="centered")

# ── PASSWORD GATE ──────────────────────────────────────────
def check_password():
    st.title("🔒 Running Coach | Login")
    pw = st.text_input("Enter password", type="password")
    if st.button("Login"):
        secret = os.environ.get("APP_PASSWORD", "")
        if hmac.compare_digest(pw.strip(), secret):
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Incorrect password.")

if not st.session_state.get("authed", False):
    check_password()
    st.stop()
# ──────────────────────────────────────────────────────────

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