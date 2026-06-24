"""
core/coach.py
The LangGraph agent — state, nodes, router, graph.

Streamlit calls run_coach() and gets back a string. Nothing else.

Reading the terminal trace:
  ============  one full turn separator
  [run_coach]   entry and exit of one user message
  [state]       what the State looks like right now
  [node]        which node is running and what it decided
  [route]       which node the router picked next
  [tool]        which tool the LLM called (from tools.py)
  [memory]      anything written or loaded from DB

When something looks wrong, scroll the trace top-to-bottom and you'll
see exactly where the agent's logic diverged from your expectation.
"""

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from core.tools import ALL_TOOLS

# When db.py is ready, uncomment these:
# from core.db import db_log_message, db_get_recent_messages

load_dotenv()


# ── 1. STATE ──────────────────────────────────────────────────────────────

class CoachState(TypedDict):
    """Shared whiteboard. Every node reads it and returns an update."""
    messages:    Annotated[list, add_messages]   # append-only conversation
    runner_id:   int                              # set once per session
    session_id:  str                              # uuid for cross-session memory
    loop_count:  int                              # how many times we've looped


def print_state(label: str, state: CoachState) -> None:
    """
    Pretty-print State at every node entry.
    This is the single most useful debugging tool you have.
    """
    msgs       = state.get("messages", [])
    last_msg   = msgs[-1] if msgs else None
    last_role  = (
        getattr(last_msg, "type", None)
        or getattr(last_msg, "role", None)
        or (last_msg.get("role") if isinstance(last_msg, dict) else "?")
    ) if last_msg else "—"
    tool_calls = getattr(last_msg, "tool_calls", None) if last_msg else None

    print(f"\n[state] ── {label} ──")
    print(f"        runner_id   : {state.get('runner_id')}")
    print(f"        session_id  : {state.get('session_id')}")
    print(f"        loop_count  : {state.get('loop_count', 0)}")
    print(f"        messages    : {len(msgs)} total")
    print(f"        last role   : {last_role}")
    if tool_calls:
        names = [
            tc.get("name") if isinstance(tc, dict) else tc.name
            for tc in tool_calls
        ]
        print(f"        tool_calls  : {names}")


# ── 2. MODEL ──────────────────────────────────────────────────────────────

_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
)
model_with_tools = _model.bind_tools(ALL_TOOLS)


# ── 3. SYSTEM PROMPT ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert running coach.
You always ground your advice in real data — never guess distances, paces,
sessions, or progress. Use tools to fetch facts and write changes.

Rules:
- Call get_runner_profile and get_goals early when context is missing.
- Call get_active_injuries on every injury or plan message.
- Call get_current_plan before save_plan so you can patch, not regenerate blindly.
- When runner reports pain/soreness → add_injury then update the plan.
- When runner says they recovered → resolve_injury.
- When race date changes → update_goal_date then update the plan.
- When runner says they completed a run → log_session.
- When runner asks if on track → analyze_progress.
- Never hallucinate km, pace, dates, or sessions. Use tool results only."""


# ── 4. NODES ──────────────────────────────────────────────────────────────

def understand(state: CoachState) -> dict:
    """
    LLM reads the conversation and decides what to do next.
    Either calls tools or produces a final reply.
    """
    print_state("ENTERING understand", state)
    print("[node]  understand: LLM thinking...")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = model_with_tools.invoke(messages)

    has_tool_calls = bool(getattr(response, "tool_calls", None))
    if has_tool_calls:
        tool_names = [
            tc.get("name") if isinstance(tc, dict) else tc.name
            for tc in response.tool_calls
        ]
        print(f"[node]  understand → LLM wants to call: {tool_names}")
    else:
        preview = (response.content or "")[:80].replace("\n", " ")
        print(f"[node]  understand → LLM produced plain reply: '{preview}...'")

    new_loop = state.get("loop_count", 0) + 1
    return {"messages": [response], "loop_count": new_loop}


def tools_entry_print(state: CoachState) -> dict:
    """
    Wrapper that prints before ToolNode runs.
    ToolNode itself doesn't expose a pre-hook, so we print here and pass
    through. The actual tool execution happens immediately after this node
    via the prebuilt ToolNode.
    """
    print_state("ENTERING tools", state)
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", []) or []
    print(f"[node]  tools: about to execute {len(tool_calls)} tool call(s)")
    return {}  # no state change — just prints


# The actual tool execution — prebuilt by LangGraph
_tool_runner = ToolNode(ALL_TOOLS)


def tools_node(state: CoachState) -> dict:
    """Combine entry print + actual tool execution."""
    tools_entry_print(state)
    result = _tool_runner.invoke(state)
    print(f"[node]  tools: completed, returning {len(result.get('messages', []))} "
          f"tool result(s) to State")
    return result


def respond(state: CoachState) -> dict:
    """
    Final reply — the LLM has all the data it needs, just answer the runner.
    """
    print_state("ENTERING respond", state)
    print("[node]  respond: generating final reply...")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = _model.invoke(messages)

    preview = (response.content or "")[:80].replace("\n", " ")
    print(f"[node]  respond → reply: '{preview}...'")
    return {"messages": [response]}


# ── 5. ROUTER ─────────────────────────────────────────────────────────────

def router(state: CoachState) -> str:
    """Read the last message. Tool calls → run them. Otherwise → respond."""
    last = state["messages"][-1]
    has_tool_calls = bool(getattr(last, "tool_calls", None))
    decision = "tools" if has_tool_calls else "respond"
    loop = state.get("loop_count", 0)
    print(f"[route] router decided: {decision} (loop #{loop})")
    return decision


# ── 6. GRAPH ──────────────────────────────────────────────────────────────

def _build_graph():
    print("[graph] building...")
    g = StateGraph(CoachState)

    g.add_node("understand", understand)
    g.add_node("tools",      tools_node)
    g.add_node("respond",    respond)

    g.add_edge(START,      "understand")   # always start here
    g.add_edge("tools",    "understand")   # loop: tool results back to LLM
    g.add_edge("respond",  END)            # reply written → done

    g.add_conditional_edges(
        "understand",
        router,
        {"tools": "tools", "respond": "respond"},
    )

    graph = g.compile()
    print("[graph] compiled\n")
    return graph


graph = _build_graph()


# ── 7. ENTRY POINT — called by Streamlit ──────────────────────────────────

def run_coach(runner_id: int, user_message: str,
              history: list = None, session_id: str = "default") -> str:
    """
    Single entry point. Returns the coach's reply as a plain string.

    Args:
        runner_id    : DB id of the runner (from Streamlit session_state)
        user_message : what the runner just typed
        history      : list of {"role", "content"} dicts from the UI
        session_id   : uuid grouping this conversation in the DB
    """
    history = history or []

    print("\n" + "=" * 60)
    print(f"[run_coach] new turn — runner_id={runner_id}, "
          f"session_id={session_id}")
    print(f"[run_coach] user message: '{user_message}'")
    print("=" * 60)

    # ── MEMORY: log the user message to DB ────────────────────────────────
    # Activate once db.py exists:
    # try:
    #     db_log_message(runner_id, "user", user_message, session_id=session_id)
    #     print(f"[memory] user message logged to DB")
    # except Exception as e:
    #     print(f"[memory] WARN: could not log user message: {e}")

    initial_state: CoachState = {
        "messages":   history + [{"role": "user", "content": user_message}],
        "runner_id":  runner_id,
        "session_id": session_id,
        "loop_count": 0,
    }

    try:
        result = graph.invoke(initial_state, config={"recursion_limit": 10})
    except Exception as e:
        # recursion_limit hit, or other graph error
        print(f"[run_coach] !! GRAPH ERROR: {type(e).__name__}: {e}")
        print(f"[run_coach] !! Likely cause: agent looped too many times — "
              f"check tool descriptions or router logic")
        return ("Sorry — I had trouble processing that. Could you try "
                "rephrasing it?")

    reply = result["messages"][-1].content
    final_loops = result.get("loop_count", 0)

    print(f"\n[run_coach] final reply: '{reply[:80]}...'")
    print(f"[run_coach] total loops in graph: {final_loops}")
    print("=" * 60 + "\n")

    # ── MEMORY: log the assistant reply to DB ─────────────────────────────
    # Activate once db.py exists:
    # try:
    #     db_log_message(runner_id, "assistant", reply, session_id=session_id)
    #     print(f"[memory] assistant reply logged to DB")
    # except Exception as e:
    #     print(f"[memory] WARN: could not log assistant reply: {e}")

    return reply


# ── 8. MEMORY HELPER — called by Streamlit on session start ───────────────

def load_session_history(runner_id: int, limit: int = 10) -> list:
    """
    Load the last `limit` messages from the DB so the runner picks up
    where they left off. Called by Streamlit on page load.

    Returns: list of {"role", "content"} dicts, oldest first.
    """
    print(f"[memory] load_session_history(runner_id={runner_id}, limit={limit})")
    # When db.py is ready, replace the placeholder:
    # try:
    #     past = db_get_recent_messages(runner_id, limit=limit)
    #     print(f"[memory] → loaded {len(past)} past messages from DB")
    #     return past
    # except Exception as e:
    #     print(f"[memory] WARN: could not load history: {e}")
    #     return []
    print(f"[memory] → placeholder: returning empty history (db.py not connected)")
    return []
