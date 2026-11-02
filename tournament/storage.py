"""JSON persistence with strict schema/invariant validation on load."""
from __future__ import annotations

import json
from pathlib import Path

from .errors import (
    MAX_NAME, MAX_TEAMS, MIN_NAME, MIN_TEAMS, ValidationError,
)

SCHEMA_VERSION = 1


def save_state(state: dict, path) -> None:
    """Write the state to a JSON file."""
    p = Path(path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=False)


def load_state(path) -> dict:
    """Read and fully validate a saved season. Returns a NEW dict.

    Never mutates a live state — the caller decides whether to swap.
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"Save file not found: {p}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Malformed JSON in {p}: {exc}") from exc

    _validate_loaded(data)
    return data


def _is_int_not_bool(value) -> bool:
    return type(value) is int


def _validate_loaded(data) -> None:
    if not isinstance(data, dict):
        raise ValidationError("Saved data must be a JSON object.")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError(
            f"Unsupported schema_version: {data.get('schema_version')!r}."
        )
    if not isinstance(data.get("teams"), list):
        raise ValidationError("'teams' must be a list.")
    if not isinstance(data.get("fixtures"), list):
        raise ValidationError("'fixtures' must be a list.")
    if not isinstance(data.get("season_generated"), bool):
        raise ValidationError("'season_generated' must be a boolean.")

    # --- teams ---------------------------------------------------------
    team_ids = set()
    folded_names = set()
    for team in data["teams"]:
        if not isinstance(team, dict):
            raise ValidationError("Each team must be an object.")
        if set(team.keys()) != {"id", "name"}:
            raise ValidationError("Team objects must have exactly 'id' and 'name'.")
        tid = team["id"]
        name = team["name"]
        if not isinstance(tid, str) or not tid:
            raise ValidationError("Team id must be a non-empty string.")
        if tid in team_ids:
            raise ValidationError(f"Duplicate team id: {tid}.")
        team_ids.add(tid)
        if not isinstance(name, str):
            raise ValidationError(f"Team {tid} name must be a string.")
        trimmed = name.strip()
        if not (MIN_NAME <= len(trimmed) <= MAX_NAME):
            raise ValidationError(f"Team {tid} name length invalid.")
        folded = trimmed.casefold()
        if folded in folded_names:
            raise ValidationError(f"Duplicate team name (casefolded): {trimmed}.")
        folded_names.add(folded)

    n_teams = len(data["teams"])
    if n_teams > MAX_TEAMS:
        raise ValidationError(f"Too many teams: {n_teams} > {MAX_TEAMS}.")

    # --- fixtures ------------------------------------------------------
    fixture_ids = set()
    pairs = set()
    for fx in data["fixtures"]:
        if not isinstance(fx, dict):
            raise ValidationError("Each fixture must be an object.")
        required = {"id", "home_id", "away_id", "status",
                    "home_score", "away_score"}
        if set(fx.keys()) != required:
            raise ValidationError(
                f"Fixture keys must be exactly {sorted(required)}."
            )
        fid = fx["id"]
        if not isinstance(fid, str) or not fid:
            raise ValidationError("Fixture id must be a non-empty string.")
        if fid in fixture_ids:
            raise ValidationError(f"Duplicate fixture id: {fid}.")
        fixture_ids.add(fid)

        home_id = fx["home_id"]
        away_id = fx["away_id"]
        if home_id not in team_ids:
            raise ValidationError(f"Fixture {fid} references unknown home_id {home_id!r}.")
        if away_id not in team_ids:
            raise ValidationError(f"Fixture {fid} references unknown away_id {away_id!r}.")
        if home_id == away_id:
            raise ValidationError(f"Fixture {fid} has home_id == away_id.")

        pair = frozenset({home_id, away_id})
        if pair in pairs:
            raise ValidationError(f"Duplicate unordered pair in fixture {fid}.")
        pairs.add(pair)

        status = fx["status"]
        if status not in ("pending", "played"):
            raise ValidationError(f"Fixture {fid} has invalid status {status!r}.")

        hs, as_ = fx["home_score"], fx["away_score"]
        if status == "pending":
            if hs is not None or as_ is not None:
                raise ValidationError(
                    f"Pending fixture {fid} must have null scores."
                )
        else:  # played
            if not _is_int_not_bool(hs) or not _is_int_not_bool(as_):
                raise ValidationError(
                    f"Played fixture {fid} scores must be integers (not bool)."
                )
            if hs < 0 or as_ < 0:
                raise ValidationError(f"Played fixture {fid} scores must be >= 0.")

    # --- consistency ---------------------------------------------------
    if data["fixtures"] and not data["season_generated"]:
        raise ValidationError(
            "Fixtures present but season_generated is False."
        )
    if data["season_generated"] and data["fixtures"] and n_teams < MIN_TEAMS:
        raise ValidationError(
            "Scheduled season requires at least MIN_TEAMS teams."
        )
