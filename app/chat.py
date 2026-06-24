import streamlit as st

from core.coach import get_reply
from core.coach import generate_plan
from core.data_io import load_profile


def render():
    st.markdown(
        "<h2 style='font-size:1.6rem!important;font-weight:800;margin-bottom:0.2rem'>Coach AI</h2>"
        "<p style='color:rgba(255,255,255,0.4)!important;font-size:0.85rem;margin-bottom:1.2rem'>Your personal running coach</p>",
        unsafe_allow_html=True,
    )

    # Welcome card when empty
    if not st.session_state.messages:
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:20px;padding:2rem;text-align:center;margin-bottom:1rem'>"
            "<div style='font-size:2.5rem;margin-bottom:0.8rem'>⚡</div>"
            "<p style='font-weight:700;font-size:1.1rem;margin-bottom:0.4rem'>Ready to train</p>"
            "<p style='color:rgba(255,255,255,0.5)!important;font-size:0.85rem;line-height:1.6'>"
            "Tell me about your running goals, experience level, and how many days per week you can train.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Chat history
    for msg in st.session_state.messages:

        role = msg.get("role", "assistant")

        avatar = "👤" if role == "user" else "🤖"

        with st.chat_message(role, avatar=avatar):
            st.write(msg["content"])

    # Input
    user_input = st.chat_input("Message your coach...")

    if user_input:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        reply = get_reply(user_input)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        st.rerun()

    # CTA
    if st.session_state.messages:
        st.markdown(
            "<div style='height:0.5rem'></div>",
            unsafe_allow_html=True,
        )

        if st.button(
            "Generate Training Plan",
            use_container_width=True,
        ):

            if not st.session_state.get("plan"):

                runner = load_profile()

                st.session_state.plan = generate_plan(
                    runner
                )

            st.session_state.page = "Plan"

            st.rerun()
