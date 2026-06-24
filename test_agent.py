"""
test_agent.py
Standalone test for the LangGraph agent. No Streamlit, no real DB needed.

Run this to watch the agent's full reasoning trace in your terminal:

    python test_agent.py

What to look for in the output:
  - Every [state] block shows what the agent knows at that moment
  - [node]  lines show which node is running
  - [route] lines show the router's decision
  - [tool]  lines show each tool call and its result
  - [memory] lines show DB read/write attempts

Once db.py is connected, you can compare turns within a session and
across sessions to verify memory works.
"""

from core.coach import run_coach, load_session_history


SCENARIOS = [
    # "Hi, who am I?",
    "I tweaked my knee on yesterday's long run.",
    # "Am I on track for my half marathon?",
]


def main():
    runner_id  = 42
    session_id = "test-session-001"

    # ── Memory check: load any past messages from DB ──────────────────────
    print("\n>>> LOADING PAST CONVERSATION HISTORY <<<")
    history = load_session_history(runner_id, limit=10)
    print(f">>> Loaded {len(history)} past messages\n")

    # ── Run each scenario, carrying history forward ──────────────────────
    for i, message in enumerate(SCENARIOS, 1):
        print(f"\n\n{'#' * 60}")
        print(f"# SCENARIO {i}: {message}")
        print(f"{'#' * 60}")

        reply = run_coach(
            runner_id    = runner_id,
            user_message = message,
            history      = history,
            session_id   = session_id,
        )

        # Append to history so the next turn sees the full conversation
        history.append({"role": "user",      "content": message})
        history.append({"role": "assistant", "content": reply})

        print(f"\nCOACH SAID: {reply}\n")

    print(f"\n>>> END OF TEST — history is now {len(history)} messages")


if __name__ == "__main__":
    main()
