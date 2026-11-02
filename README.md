# TournamentLab

A Python CLI esports league manager: register 4–8 teams, generate a
round-robin schedule, record results, and compute a ranked league table.

## Run

    python main.py

## Test

    python -m unittest discover -v

## Rules

- 4–8 teams, names trimmed 2–30 chars, case-insensitive uniqueness
- Single round-robin (each pair once) → N(N−1)/2 fixtures
- Points: win 3, draw 1, loss 0
- Tie-break: points ↓, goal difference ↓, goals for ↓, name ↑
- Champion shown only when every fixture is played
- JSON save/load with strict schema + invariant validation on load

## Files

- `main.py` — entry point
- `tournament/teams.py` — registration & listing
- `tournament/fixtures.py` — schedule + record results
- `tournament/standings.py` — table, tie-break, champion (pure)
- `tournament/storage.py` — JSON save/load + validation
- `tournament/cli.py` — interactive menu
- `tests/` — 26+ unittest cases
- `scripts/demo_season.py` — reproducible end-to-end demo
- `docs/` — design decisions and AI learning log

## Example session

(see `python scripts/demo_season.py` output)