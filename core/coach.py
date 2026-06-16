HARDCODED_REPLY = "Got it! Tell me more about your goal."

HARDCODED_PLAN = """Week 1 · Base
  Mon: 8 km easy
  Wed: 6 km intervals
  Sat: 14 km long

Week 2 · Build
  Mon: 9 km easy
  Wed: 7 km intervals
  Sat: 16 km long"""


def get_reply(message: str) -> str:
    return HARDCODED_REPLY


def generate_plan(runner: dict) -> str:
    return HARDCODED_PLAN
