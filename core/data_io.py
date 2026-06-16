import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "runner.json"


def load_runner() -> dict:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_runner(data: dict) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
