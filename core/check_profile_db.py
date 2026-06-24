"""Quick live test: run from repo root with  python core/check_profile_db.py
Confirms load_profile() reads Marie out of the DB and round-trips through the model.
"""
from core.data_io import load_profile
from core.profile_model import RunnerProfile

raw = load_profile()
print("raw dict from DB:", raw)
prof = RunnerProfile.model_validate(raw)
print("OK ->", prof.identity.first_name, "| goal:", prof.goal.race_type,
      prof.goal.target_distance_km, "km |", len(prof.constraints), "constraint(s)")