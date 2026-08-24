# Data pipeline

Run `python3 scripts/data/evaluate_corridors.py`, then `python3 scripts/data/build_corridor.py`, `python3 scripts/data/build_terrain.py`, and `python3 scripts/data/validate_corridor.py`. Raw/cached downloads are ignored. The checked-in runtime package contains only the compact selected corridor. Regeneration contacts Overpass and geo.admin.ch and should respect their rate limits.

