"""
core/tools.py
All tools the LangGraph agent can call.

Every tool prints:
  1. Tool entry with its arguments
  2. The result it's returning

This is your debugging trace - when something looks wrong, scroll the
terminal output and you'll see exactly which tool was called and what
it returned.
"""

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from core.db import (
    db_get_runner_profile, db_get_goals, db_get_active_injuries,
    db_get_recent_sessions, db_get_current_plan, db_compute_progress,
    db_save_plan, db_add_injury, db_resolve_injury,
    db_log_session, db_update_goal_date,
)


# ── READ tools ─────────────────────────────────────────────────────────────

@tool
def get_runner_profile(runner_id: Annotated[int, InjectedState("runner_id")]) -> dict:
    """Get the runner's profile: first_name, city, sessions_per_week,
    preferred_days, max_session_min, notes. Call this first on every new
    message if you don't have profile context yet."""
    print(f"  [tool] get_runner_profile(runner_id={runner_id})")
    result = db_get_runner_profile(runner_id)
    print(f"  [tool] -> returned: {result}")
    return result


@tool
def get_goals(runner_id: Annotated[int, InjectedState("runner_id")]) -> dict:
    """Get the runner's current active race goal: race_type, target_distance_km,
    target_time, race_date, horizon_weeks. Call when race date or pace targets
    matter."""
    print(f"  [tool] get_goals(runner_id={runner_id})")
    result = db_get_goals(runner_id)
    print(f"  [tool] -> returned: {result}")
    return result


@tool
def get_active_injuries(runner_id: Annotated[int, InjectedState("runner_id")]) -> list:
    """Get all active (unresolved) injuries for the runner.
    Call at the start of any plan-related or injury-related message."""
    print(f"  [tool] get_active_injuries(runner_id={runner_id})")
    result = db_get_active_injuries(runner_id)
    print(f"  [tool] -> returned: {len(result)} active injuries")
    return result


@tool
def get_recent_sessions(runner_id: Annotated[int, InjectedState("runner_id")],
                        since: str = None, n: int = 10) -> list:
    """Get the runner's training sessions.
    If since (YYYY-MM-DD) is provided, returns sessions since that date.
    Otherwise returns the last n sessions.
    Each session includes date, km, pace, type."""
    print(f"  [tool] get_recent_sessions(runner_id={runner_id}, since={since}, n={n})")
    result = db_get_recent_sessions(runner_id, since=since, n=n)
    print(f"  [tool] -> returned: {len(result)} sessions")
    return result


@tool
def get_current_plan(runner_id: Annotated[int, InjectedState("runner_id")]) -> dict:
    """Get the runner's current active training plan with all weeks and sessions.
    Call before save_plan so you can patch rather than regenerate blindly."""
    print(f"  [tool] get_current_plan(runner_id={runner_id})")
    result = db_get_current_plan(runner_id)
    print(f"  [tool] -> returned: plan with {len(result.get('weeks', []))} weeks")
    return result


@tool
def analyze_progress(runner_id: Annotated[int, InjectedState("runner_id")],
                     question: str = None) -> dict:
    """Compute a structured progress report against the runner's goal.
    Returns verdict (on_track | at_risk | off_track), volume_adherence_pct,
    sessions_last_4_weeks, longest_run_km, weeks_remaining, active_injuries.
    Call when the runner asks if they're on track, ahead, or behind."""
    print(f"  [tool] analyze_progress(runner_id={runner_id}, question={question})")
    result = db_compute_progress(runner_id, question)
    print(f"  [tool] -> verdict: {result.get('verdict')}")
    return result


# ── WRITE tools ────────────────────────────────────────────────────────────

@tool
def save_plan(runner_id: Annotated[int, InjectedState("runner_id")],
              content: str, structured: dict, total_weeks: int) -> str:
    """Save a newly generated training plan to the database.
    Inserts as the new active plan (most recent is always active).
    content: human-readable plan summary.
    structured: dict with a 'weeks' list.
    total_weeks: total weeks in the plan."""
    print(f"  [tool] save_plan(runner_id={runner_id}, total_weeks={total_weeks})")
    result = db_save_plan(runner_id, content, structured, total_weeks)
    print(f"  [tool] -> {result}")
    return result


@tool
def add_injury(runner_id: Annotated[int, InjectedState("runner_id")],
               area: str, severity: str, note: str = "") -> str:
    """Log a new injury for the runner.
    area: body part e.g. 'knee', 'left ankle', 'hamstring'.
    severity: niggle | moderate | severe.
    Call when runner reports pain, soreness, or a physical issue."""
    print(f"  [tool] add_injury(runner_id={runner_id}, area={area}, severity={severity})")
    result = db_add_injury(runner_id, area, severity, note)
    print(f"  [tool] -> {result}")
    return result


@tool
def resolve_injury(injury_id: int) -> str:
    """Mark an injury as resolved. Call when runner explicitly says they have
    recovered (e.g. 'knee is fine now', 'all good').
    Sets active=false and resolved_at=now."""
    print(f"  [tool] resolve_injury(injury_id={injury_id})")
    result = db_resolve_injury(injury_id)
    print(f"  [tool] -> {result}")
    return result


@tool
def log_session(runner_id: Annotated[int, InjectedState("runner_id")],
                date: str, km: float, pace: str, type: str) -> str:
    """Log a completed training session from conversation.
    date: YYYY-MM-DD. pace: MM:SS format e.g. '5:30'.
    type: easy | intervals | long | recovery.
    Call when runner says they completed a run."""
    print(f"  [tool] log_session(runner_id={runner_id}, date={date}, "
          f"km={km}, type={type})")
    result = db_log_session(runner_id, date, km, pace, type)
    print(f"  [tool] -> {result}")
    return result


@tool
def update_goal_date(runner_id: Annotated[int, InjectedState("runner_id")],
                     new_date: str) -> str:
    """Update the runner's active race date. new_date format: YYYY-MM-DD.
    Call when runner says their race date has moved."""
    print(f"  [tool] update_goal_date(runner_id={runner_id}, new_date={new_date})")
    result = db_update_goal_date(runner_id, new_date)
    print(f"  [tool] -> {result}")
    return result


# ── Tool registry — imported by coach.py ──────────────────────────────────

ALL_TOOLS = [
    # Reads
    get_runner_profile,
    get_goals,
    get_active_injuries,
    get_recent_sessions,
    get_current_plan,
    analyze_progress,
    # Writes
    save_plan,
    add_injury,
    resolve_injury,
    log_session,
    update_goal_date,
]