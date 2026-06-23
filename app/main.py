import streamlit as st
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RunCoach",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS — every selector battle-tested against Streamlit internals
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

/* ── Kill Streamlit chrome ── */
#MainMenu {display:none!important}
footer {display:none!important}
header {display:none!important}
[data-testid="collapsedControl"] {display:none!important}
[data-testid="stSidebar"] {display:none!important}

/* ── Dark base ── */
.stApp {
    background: #050505 !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: #050505 !important;
}

/* ── Mobile width constraint ── */
.block-container {
    max-width: 430px !important;
    margin: 0 auto !important;
    padding: 1rem 1.2rem 3rem 1.2rem !important;
    background: #050505 !important;
}

/* ── All text white by default ── */
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp span, .stApp label, .stApp li,
.stMarkdown, .stMarkdown p {
    font-family: 'Outfit', sans-serif !important;
    color: #ffffff !important;
}

/* ── RADIO PILL TABS ── */
/* Hide the label */
.stRadio > label {display:none!important}
/* The group container */
.stRadio > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 6px !important;
    background: rgba(255,255,255,0.06) !important;
    padding: 5px !important;
    border-radius: 50px !important;
    margin-bottom: 1.2rem !important;
}
/* Each radio option */
.stRadio > div[role="radiogroup"] label {
    flex: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}
/* Hide the radio circle dot */
.stRadio > div[role="radiogroup"] label > div:first-child {
    display: none !important;
}
/* The clickable label text area */
.stRadio > div[role="radiogroup"] label > div:last-child {
    text-align: center !important;
    padding: 10px 4px !important;
    border-radius: 50px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: rgba(255,255,255,0.45) !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
}
.stRadio > div[role="radiogroup"] label > div:last-child p {
    color: rgba(255,255,255,0.45) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    margin: 0 !important;
}
/* Active tab */
.stRadio > div[role="radiogroup"] label:has(input:checked) > div:last-child {
    background: #CCFF00 !important;
    color: #050505 !important;
    box-shadow: 0 2px 12px rgba(204,255,0,0.25) !important;
}
.stRadio > div[role="radiogroup"] label:has(input:checked) > div:last-child p {
    color: #050505 !important;
    font-weight: 700 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: #CCFF00 !important;
    color: #050505 !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 14px 24px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
.stButton > button p {
    color: #050505 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    margin: 0 !important;
}
.stButton > button:hover {
    background: #d4ff33 !important;
    box-shadow: 0 6px 20px rgba(204,255,0,0.3) !important;
}
.stButton > button:active {
    transform: scale(0.98) !important;
}

/* ── TEXT INPUTS ── */
div[data-baseweb="input"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}
div[data-baseweb="input"] input {
    color: #ffffff !important;
    background: transparent !important;
    caret-color: #CCFF00 !important;
    font-family: 'Outfit', sans-serif !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #CCFF00 !important;
    box-shadow: 0 0 0 1px #CCFF00 !important;
}
.stTextInput [data-testid="InputInstructions"] {
    display: none !important;
}
/* Number inputs */
div[data-baseweb="input"] input[type="number"] {
    color: #ffffff !important;
    background: transparent !important;
}

/* ── SELECT / DROPDOWN ── */
div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
}
div[data-baseweb="select"] span {
    color: #ffffff !important;
}

/* ── MULTISELECT ── */
.stMultiSelect > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: #CCFF00 !important;
    color: #050505 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ── CHAT ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 0.8rem !important;
}
[data-testid="stChatMessage"] .stMarkdown {
    background: rgba(255,255,255,0.06);
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
/* Hide avatars */
[data-testid="stChatMessage"] [data-testid="stChatAvatar"] {
    display: none !important;
}
/* Chat input */
[data-testid="stChatInputContainer"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stChatInputContainer"] textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 50px !important;
    color: #ffffff !important;
    caret-color: #CCFF00 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 16px !important;
    padding: 12px !important;
}
[data-testid="stMetricLabel"] p {
    color: rgba(255,255,255,0.5) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
[data-testid="stMetricValue"] {
    color: #CCFF00 !important;
    font-weight: 800 !important;
}

/* ── CHARTS ── */
[data-testid="stVegaLiteChart"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    padding: 8px !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* ── FORM ── */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}
[data-testid="stForm"] button[type="submit"] {
    background: #CCFF00 !important;
    color: #050505 !important;
    border-radius: 50px !important;
}
[data-testid="stForm"] button[type="submit"] p {
    color: #050505 !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 16px !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
}

/* ── DIVIDER ── */
hr {border-color: rgba(255,255,255,0.08) !important}

/* ── CHECKBOX ── */
.stCheckbox label span {color: #ffffff !important}

/* ── DATE INPUT ── */
[data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.06) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}

/* ── DATA EDITOR ── */
[data-testid="stDataEditor"] {
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* ── CAPTION ── */
.stCaption, .stCaption p {
    color: rgba(255,255,255,0.4) !important;
}

/* ── SUBHEADER ── */
.stSubheader, h2 {
    font-weight: 700 !important;
    font-size: 1.1rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar {width:4px}
::-webkit-scrollbar-track {background:#050505}
::-webkit-scrollbar-thumb {background:rgba(255,255,255,0.15);border-radius:4px}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_password():
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center'>"
        "<div style='font-size:3.5rem;margin-bottom:0.5rem'>⚡</div>"
        "<h1 style='font-size:2.8rem!important;font-weight:900;letter-spacing:-2px;margin:0'>RunCoach</h1>"
        "<p style='color:#CCFF00!important;font-weight:600;letter-spacing:3px;text-transform:uppercase;font-size:0.75rem;margin-top:4px'>Pro Edition</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    pw = st.text_input(
        "Password",
        type="password",
        label_visibility="collapsed",
        placeholder="Enter access code",
    )
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("Unlock", use_container_width=True):
        secret = os.environ.get("APP_PASSWORD", "")
        if hmac.compare_digest(pw.strip(), secret):
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Wrong code.")


if not st.session_state.get("authed"):
    check_password()
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION DEFAULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "page" not in st.session_state:
    st.session_state.page = "Chat"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan" not in st.session_state:
    st.session_state.plan = ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NAVIGATION — native horizontal radio, CSS-styled as pills
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABS = ["Chat", "Plan", "Profile", "History"]

selected = st.radio(
    "nav",
    TABS,
    index=TABS.index(st.session_state.page),
    horizontal=True,
    label_visibility="collapsed",
)

if selected != st.session_state.page:
    st.session_state.page = selected
    st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.page == "Chat":
    from app.chat import render
    render()
elif st.session_state.page == "Plan":
    from app.plan_view import render
    render()
elif st.session_state.page == "Profile":
    from app.profile import render
    render()
elif st.session_state.page == "History":
    from app.history import render
    render()