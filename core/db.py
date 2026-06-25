"""Single place that hands out a database connection and all DB operations.

DATABASE_URL lives in .env (git-ignored) and already includes
?sslmode=require. Everything that touches the DB imports get_connection
so the connection logic exists in exactly one place.
"""
import os
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    """Open a new connection to the Supabase Postgres database."""
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")


# ── runners ────────────────────────────────────────────────────────────────

def db_get_runner_profile(runner_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, first_name, city, gender, sessions_per_week, "
                "preferred_days, max_session_min, notes "
                "FROM runners WHERE id = %s",
                (runner_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {}
    finally:
        conn.close()


# ── goals ──────────────────────────────────────────────────────────────────

def db_get_goals(runner_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT goal_id, runner_id, race_type, target_distance_km, "
                "target_time, race_date, horizon_weeks, created_at "
                "FROM goals WHERE runner_id = %s",
                (runner_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else {}
    finally:
        conn.close()


def db_save_goal(runner_id: int, race_type: str = None, target_distance_km: float = None,
                 target_time: str = None, race_date: str = None, horizon_weeks: int = None) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT goal_id FROM goals WHERE runner_id = %s", (runner_id,))
            existing = cur.fetchone()
            if existing:
                # only overwrite fields the runner actually mentioned
                cur.execute(
                    "UPDATE goals SET "
                    "race_type = COALESCE(%s, race_type), "
                    "target_distance_km = COALESCE(%s, target_distance_km), "
                    "target_time = COALESCE(%s, target_time), "
                    "race_date = COALESCE(%s, race_date), "
                    "horizon_weeks = COALESCE(%s, horizon_weeks) "
                    "WHERE runner_id = %s",
                    (race_type, target_distance_km, target_time, race_date, horizon_weeks, runner_id),
                )
            else:
                cur.execute(
                    "INSERT INTO goals (runner_id, race_type, target_distance_km, "
                    "target_time, race_date, horizon_weeks) VALUES (%s, %s, %s, %s, %s, %s)",
                    (runner_id, race_type, target_distance_km, target_time, race_date, horizon_weeks),
                )
        conn.commit()
        return "goal saved"
    finally:
        conn.close()


def db_update_availability(runner_id: int, sessions_per_week: int = None,
                            preferred_days: list = None, max_session_min: int = None) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            fields, values = [], []
            if sessions_per_week is not None:
                fields.append("sessions_per_week = %s")
                values.append(sessions_per_week)
            if preferred_days is not None:
                fields.append("preferred_days = %s")
                values.append(preferred_days)
            if max_session_min is not None:
                fields.append("max_session_min = %s")
                values.append(max_session_min)
            if not fields:
                return "nothing to update"
            values.append(runner_id)
            cur.execute(f"UPDATE runners SET {', '.join(fields)} WHERE id = %s", values)
        conn.commit()
        return "availability updated"
    finally:
        conn.close()


def db_update_goal_date(runner_id: int, new_date: str) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE goals SET race_date = %s WHERE runner_id = %s",
                (new_date, runner_id),
            )
        conn.commit()
        return "goal date updated"
    finally:
        conn.close()


# ── injury ─────────────────────────────────────────────────────────────────

def db_get_active_injuries(runner_id: int) -> list:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT injury_id, kind, area, note, severity, logged_at "
                "FROM injury WHERE runner_id = %s AND active = true "
                "ORDER BY logged_at DESC",
                (runner_id,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def db_add_injury(runner_id: int, area: str, severity: str, note: str = "") -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO injury (runner_id, kind, severity, area, note, "
                "active, logged_at) VALUES (%s, 'injury', %s, %s, %s, true, NOW())",
                (runner_id, severity, area or None, note or None),
            )
        conn.commit()
        return "injury logged"
    finally:
        conn.close()


def db_resolve_injury(injury_id: int) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE injury SET active = false, resolved_at = NOW() "
                "WHERE injury_id = %s",
                (injury_id,),
            )
        conn.commit()
        return "injury resolved"
    finally:
        conn.close()


# ── training_sessions ──────────────────────────────────────────────────────

def db_get_recent_sessions(runner_id: int, since: str = None, n: int = 10) -> list:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if since:
                cur.execute(
                    "SELECT id, date, km, pace, type FROM training_sessions "
                    "WHERE runner_id = %s AND date >= %s ORDER BY date DESC",
                    (runner_id, since),
                )
            else:
                cur.execute(
                    "SELECT id, date, km, pace, type FROM training_sessions "
                    "WHERE runner_id = %s ORDER BY date DESC LIMIT %s",
                    (runner_id, n),
                )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def db_log_session(runner_id: int, date: str, km: float,
                   pace: str, type: str) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO training_sessions (runner_id, date, km, pace, type) "
                "VALUES (%s, %s, %s, %s, %s)",
                (runner_id, date, km, pace, type),
            )
        conn.commit()
        return "session logged"
    finally:
        conn.close()


# ── plans ──────────────────────────────────────────────────────────────────

def db_get_current_plan(runner_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, content, created_at, structured, total_weeks "
                "FROM plans WHERE runner_id = %s ORDER BY created_at DESC LIMIT 1",
                (runner_id,),
            )
            row = cur.fetchone()
            if not row:
                return {"runner_id": runner_id, "weeks": []}
            result = dict(row)
            result["weeks"] = (result.get("structured") or {}).get("weeks", [])
            return result
    finally:
        conn.close()


def db_save_plan(runner_id: int, content: str, structured: dict,
                 total_weeks: int) -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO plans (runner_id, content, structured, total_weeks, "
                "created_at) VALUES (%s, %s, %s, %s, NOW())",
                (runner_id, content, Json(structured), total_weeks),
            )
        conn.commit()
        return "plan saved"
    finally:
        conn.close()


# ── progress ───────────────────────────────────────────────────────────────

def db_compute_progress(runner_id: int, question: str = None) -> dict:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT race_date, target_distance_km FROM goals "
                "WHERE runner_id = %s",
                (runner_id,),
            )
            goal = cur.fetchone()
            if not goal:
                return {"verdict": "insufficient_data", "reason": "no goal set"}

            today = date.today()
            race_date = goal["race_date"]
            weeks_remaining = max(0, (race_date - today).days // 7) if race_date else None

            cur.execute(
                "SELECT sessions_per_week FROM runners WHERE id = %s",
                (runner_id,),
            )
            runner = cur.fetchone()
            target_spw = (runner or {}).get("sessions_per_week") or 3

            cur.execute(
                "SELECT date, km FROM training_sessions "
                "WHERE runner_id = %s "
                "AND date >= (CURRENT_DATE - INTERVAL '28 days') "
                "ORDER BY date DESC",
                (runner_id,),
            )
            sessions = cur.fetchall()
            actual_count = len(sessions)
            target_count = target_spw * 4
            volume_pct = round((actual_count / target_count) * 100) if target_count else 0
            longest_km = max((float(s["km"]) for s in sessions), default=0.0)

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM injury "
                "WHERE runner_id = %s AND active = true",
                (runner_id,),
            )
            injury_count = cur.fetchone()["cnt"]

        if volume_pct >= 80 and injury_count == 0:
            verdict = "on_track"
        elif volume_pct >= 50 or injury_count > 0:
            verdict = "at_risk"
        else:
            verdict = "off_track"

        return {
            "verdict": verdict,
            "volume_adherence_pct": volume_pct,
            "sessions_last_4_weeks": actual_count,
            "longest_run_km": longest_km,
            "weeks_remaining": weeks_remaining,
            "active_injuries": injury_count,
        }
    finally:
        conn.close()


# ── messages ───────────────────────────────────────────────────────────────

def db_log_message(runner_id: int, role: str, content: str,
                   session_id: str = None) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (runner_id, role, content, created_at) "
                "VALUES (%s, %s, %s, NOW())",
                (runner_id, role, content),
            )
        conn.commit()
    finally:
        conn.close()


def db_get_recent_messages(runner_id: int, limit: int = 10) -> list:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT role, content FROM messages "
                "WHERE runner_id = %s ORDER BY created_at DESC LIMIT %s",
                (runner_id, limit),
            )
            rows = cur.fetchall()
            return [{"role": r["role"], "content": r["content"]}
                    for r in reversed(rows)]
    finally:
        conn.close()