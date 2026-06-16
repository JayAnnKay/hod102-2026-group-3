import streamlit as st


def render():
    st.title("Chat with your Coach")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Type a message...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append(
            {"role": "assistant", "content": "Got it! Tell me more about your goal."}
        )
        st.rerun()

    if st.button("Generate a training plan", use_container_width=True):
        st.session_state.plan = """Week 1 · Base
  Mon: 8 km easy
  Wed: 6 km intervals
  Sat: 14 km long

Week 2 · Build
  Mon: 9 km easy
  Wed: 7 km intervals
  Sat: 16 km long"""
        st.session_state.page = "Current Plan"
        st.rerun()
