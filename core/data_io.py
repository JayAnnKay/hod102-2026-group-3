"""Data access.

load_runner / save_runner: the team's original file helpers (untouched).
load_profile / save_profile: now backed by Postgres across three tables
  runners (identity + availability) , goals (1 per runner) , constraints (N).
Both still speak plain dicts, so app/profile.py is unchanged.
Single-runner assumption for Day 2: we use the one runner in the table.
"""
import json
from pathlib import Path

from core.db import get_connection

DATA_PATH = Path(__file__).parent.parent / "data" / "runner.json"

_DAY_ABBREV = {
    "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
    "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun",
    "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
    "fri": "Fri", "sat": "Sat", "sun": "Sun",
}

def _normalize_days(days: list) -> list:
    if not days:
        return []
    return [_DAY_ABBREV.get(d.lower(), d) for d in days]


def load_runner() -> dict:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_runner(data: dict) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


# --------------------------------------------------------------------------- #
# Profile  (runners + goals + constraints)
# --------------------------------------------------------------------------- #
def _build_profile_dict(runner_row, goal_row, constraint_rows) -> dict:
    """Assemble the three tables' rows into the profile dict the model expects."""
    rid, first_name, city, gender, spw, pref_days, max_min, notes = runner_row
    goal = {}
    if goal_row:
        race_type, dist, target_time, race_date, horizon = goal_row
        goal = {
            "race_type": race_type or "",
            "target_distance_km": float(dist) if dist is not None else None,
            "target_time": target_time,
            "race_date": race_date.isoformat() if race_date else None,
            "horizon_weeks": horizon,
        }
    return {
        "identity": {"first_name": first_name, "city": city, "gender": gender},
        "goal": goal,
        "availability": {
            "sessions_per_week": spw if spw is not None else 3,
            "preferred_days": _normalize_days(list(pref_days) if pref_days else []),
            "max_session_min": max_min,
        },
        "constraints": [
            {
                "kind": k if k in ("injury", "preference", "other") else "injury",
                "area": a, "note": n, "severity": s, "active": act,
            }
            for (k, a, n, s, act) in constraint_rows
        ],
        "notes": notes or "",
    }


def _current_runner_id(cur) -> int | None:
    cur.execute("select id from runners order by id limit 1;")
    row = cur.fetchone()
    return row[0] if row else None


def get_runner_id() -> int | None:
    """Return the first runner's id from the DB. Returns None if no runner exists."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        return _current_runner_id(cur)
    finally:
        conn.close()


def load_profile() -> dict:
    """Read the single runner's profile from the DB, or {} if no runner yet."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        rid = _current_runner_id(cur)
        if rid is None:
            return {}
        cur.execute(
            "select id, first_name, city, gender, sessions_per_week, "
            "preferred_days, max_session_min, notes from runners where id = %s;",
            (rid,),
        )
        runner_row = cur.fetchone()
        cur.execute(
            "select race_type, target_distance_km, target_time, race_date, "
            "horizon_weeks from goals where runner_id = %s;",
            (rid,),
        )
        goal_row = cur.fetchone()
        cur.execute(
            "select kind, area, note, severity, active from injury "
            "where runner_id = %s order by injury_id;",
            (rid,),
        )
        constraint_rows = cur.fetchall()
        return _build_profile_dict(runner_row, goal_row, constraint_rows)
    finally:
        conn.close()


def save_profile(data: dict) -> None:
    """Write the profile dict back across the three tables, in one transaction."""
    ident = data.get("identity", {})
    goal = data.get("goal", {})
    avail = data.get("availability", {})
    constraints = data.get("constraints", [])

    conn = get_connection()
    try:
        cur = conn.cursor()
        rid = _current_runner_id(cur)
        if rid is None:
            cur.execute(
                "insert into runners (first_name) values (%s) returning id;",
                (ident.get("first_name", ""),),
            )
            rid = cur.fetchone()[0]

        cur.execute(
            "update runners set first_name=%s, city=%s, gender=%s, "
            "sessions_per_week=%s, preferred_days=%s, max_session_min=%s, notes=%s "
            "where id=%s;",
            (
                ident.get("first_name", ""),
                ident.get("city"),
                ident.get("gender"),
                avail.get("sessions_per_week"),
                avail.get("preferred_days") or [],
                avail.get("max_session_min"),
                data.get("notes", ""),
                rid,
            ),
        )

        goal_params = (
            goal.get("race_type", ""),
            goal.get("target_distance_km"),
            goal.get("target_time"),
            goal.get("race_date"),
            goal.get("horizon_weeks"),
        )
        cur.execute("select goal_id from goals where runner_id = %s;", (rid,))
        if cur.fetchone():
            cur.execute(
                "update goals set race_type=%s, target_distance_km=%s, target_time=%s, "
                "race_date=%s, horizon_weeks=%s where runner_id=%s;",
                goal_params + (rid,),
            )
        else:
            cur.execute(
                "insert into goals (race_type, target_distance_km, target_time, "
                "race_date, horizon_weeks, runner_id) values (%s,%s,%s,%s,%s,%s);",
                goal_params + (rid,),
            )

        # constraints: replace the whole set for this runner (table is named "injury")
        cur.execute("delete from injury where runner_id = %s;", (rid,))
        for c in constraints:
            cur.execute(
                "insert into injury (runner_id, kind, area, note, severity, active) "
                "values (%s,%s,%s,%s,%s,%s);",
                (rid, c.get("kind", "other"), c.get("area"), c.get("note", ""),
                 c.get("severity"), c.get("active", True)),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()