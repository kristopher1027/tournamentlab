"""Fixture generation and result recording.

Pure-ish functions: they mutate the passed-in state but perform no I/O.
"""
from __future__ import annotations

from .errors import FixtureError, ValidationError

MIN_TEAMS = 4


def _next_fixture_id(fixtures: list[dict]) -> str:
    """Deterministic, zero-padded IDs: M001, M002, ..."""
    return f"M{len(fixtures) + 1:03d}"


def generate_schedule(state: dict) -> list[dict]:
    """Generate a single round-robin schedule for the registered teams.

    Rules:
      - at least MIN_TEAMS (4) teams must be registered
      - the schedule may be generated only once per season
      - every unordered pair of distinct teams appears exactly once
      - fixture IDs are deterministic (M001, M002, ...)
      - home/away order is deterministic: earlier-registered team is home

    Returns the list of created fixtures.
    """
    if not isinstance(state, dict) or "teams" not in state:
        raise ValidationError("Invalid league state.")

    teams = state["teams"]
    if len(teams) < MIN_TEAMS:
        raise ValidationError(
            f"At least {MIN_TEAMS} teams are required to generate a schedule."
        )

    if state.get("season_generated") or state.get("fixtures"):
        raise ValidationError("The schedule has already been generated for this season.")

    new_fixtures: list[dict] = []
    n = len(teams)
    for i in range(n):
        for j in range(i + 1, n):
            new_fixtures.append(
                {
                    "id": _next_fixture_id(new_fixtures),
                    "home_id": teams[i]["id"],
                    "away_id": teams[j]["id"],
                    "status": "pending",
                    "home_score": None,
                    "away_score": None,
                }
            )

    state["fixtures"].extend(new_fixtures)
    state["season_generated"] = True
    return new_fixtures


def list_fixtures(state: dict) -> list[dict]:
    """Return a shallow copy of the fixtures list (safe to display/iterate)."""
    return list(state.get("fixtures", []))


def _validate_score(value, label: str) -> int:
    """Strict nonnegative integer check.

    Note: ``type(value) is int`` deliberately rejects ``bool`` because
    ``isinstance(True, int)`` is True in Python.
    """
    if type(value) is not int:
        raise ValidationError(f"{label} must be an integer.")
    if value < 0:
        raise ValidationError(f"{label} cannot be negative.")
    return value


def record_result(
    state: dict, fixture_id: str, home_score, away_score
) -> dict:
    """Record the result of a pending fixture.

    Rules:
      - the fixture must exist
      - the fixture must be pending (no duplicate submissions)
      - both scores must be nonnegative integers (bool rejected)
      - updates are atomic: on any failure, no field is mutated
    """
    if not isinstance(state, dict) or "fixtures" not in state:
        raise ValidationError("Invalid league state.")

    fixture = None
    for fx in state["fixtures"]:
        if fx["id"] == fixture_id:
            fixture = fx
            break
    if fixture is None:
        raise FixtureError(f"Unknown fixture ID: {fixture_id!r}.")

    if fixture["status"] != "pending":
        raise FixtureError(
            f"Fixture {fixture_id} has already been played; cannot record again."
        )

    # Validate BOTH scores before touching the fixture.
    hs = _validate_score(home_score, "Home score")
    as_ = _validate_score(away_score, "Away score")

    # Atomic commit: both fields plus status in one logical step.
    fixture["home_score"] = hs
    fixture["away_score"] = as_
    fixture["status"] = "played"
    return fixture