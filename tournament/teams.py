"""Team registration and listing.

Pure-ish functions: they mutate the passed-in state but perform no I/O.
"""
from __future__ import annotations

from .errors import ValidationError

MIN_NAME = 2
MAX_NAME = 30
MIN_TEAMS = 4
MAX_TEAMS = 8


def new_state() -> dict:
    """Return a fresh empty league state."""
    return {
        "schema_version": 1,
        "teams": [],
        "fixtures": [],
        "season_generated": False,
    }


def _normalize(name: str) -> str:
    return name.strip().casefold()


def _validate_name(name) -> str:
    if not isinstance(name, str):
        raise ValidationError("Team name must be a string.")
    trimmed = name.strip()
    if len(trimmed) < MIN_NAME:
        raise ValidationError(
            f"Team name must be at least {MIN_NAME} characters after trimming."
        )
    if len(trimmed) > MAX_NAME:
        raise ValidationError(
            f"Team name must be at most {MAX_NAME} characters after trimming."
        )
    return trimmed


def _next_team_id(teams: list[dict]) -> str:
    """Deterministic, zero-padded, gap-free IDs: TM001, TM002, ..."""
    return f"TM{len(teams) + 1:03d}"


def register_team(state: dict, name: str) -> dict:
    """Register a new team. Returns the created team dict.

    Rules:
      - name is trimmed; 2..30 chars
      - casefolded names must be unique
      - cannot register once the schedule is generated
      - cannot exceed MAX_TEAMS
    """
    if not isinstance(state, dict) or "teams" not in state:
        raise ValidationError("Invalid league state.")

    if state.get("season_generated"):
        raise ValidationError("Cannot register teams after the schedule is generated.")

    if len(state["teams"]) >= MAX_TEAMS:
        raise ValidationError(f"A league holds at most {MAX_TEAMS} teams.")

    trimmed = _validate_name(name)
    folded = trimmed.casefold()

    for team in state["teams"]:
        if team["name"].casefold() == folded:
            raise ValidationError(f"Team name '{trimmed}' is already registered.")

    team = {
        "id": _next_team_id(state["teams"]),
        "name": trimmed,
    }
    state["teams"].append(team)
    return team


def list_teams(state: dict) -> list[dict]:
    """Return a shallow copy of the teams list (safe to display/iterate)."""
    return list(state.get("teams", []))