"""Team registration and listing.

Pure-ish functions: they mutate the passed-in state but perform no I/O.
"""
from __future__ import annotations

from .errors import (
    MAX_NAME, MAX_TEAMS, MIN_NAME, MIN_TEAMS, ValidationError,
)



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

def rename_team(state: dict, team_id: str, new_name: str) -> dict:
    """Rename an existing team.

    Fixtures reference the stable team ID, not the display name, so no
    fixture needs updating — this is why IDs and names are separate.

    Rules mirror register_team:
      - new_name trimmed; 2..30 chars
      - casefolded uniqueness (excluding the team being renamed)
      - team must exist
    """
    if not isinstance(state, dict) or "teams" not in state:
        raise ValidationError("Invalid league state.")

    team = None
    for t in state["teams"]:
        if t["id"] == team_id:
            team = t
            break
    if team is None:
        raise ValidationError(f"Unknown team id: {team_id!r}.")

    trimmed = _validate_name(new_name)
    folded = trimmed.casefold()
    for other in state["teams"]:
        if other["id"] == team_id:
            continue
        if other["name"].casefold() == folded:
            raise ValidationError(
                f"Team name '{trimmed}' is already in use by {other['id']}."
            )

    team["name"] = trimmed
    return team
