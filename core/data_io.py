import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "runner.json"


def load_runner() -> dict:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_runner(data: dict) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- added for the user profile (Screen 3) ---
PROFILE_PATH = Path(__file__).parent.parent / "data" / "profile.json"


def load_profile() -> dict:
    """Return the saved profile as a dict, or {} on first run."""
    if not PROFILE_PATH.exists():
        return {}
    with open(PROFILE_PATH, "r") as f:
        return json.load(f)


def save_profile(data: dict) -> None:
    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f, indent=2)