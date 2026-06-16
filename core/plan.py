def get_current_plan(session_state) -> str:
    return session_state.get("plan", "")
