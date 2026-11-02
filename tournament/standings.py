"""League table computation, tie-breaks, and champion.

This module is pure: it imports nothing from the rest of the package and
performs no I/O. ``compute_standings`` is a function of (teams, fixtures).
"""
from __future__ import annotations


def _empty_row(team: dict) -> dict:
    return {
        "team_id": team["id"],
        "name": team["name"],
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "points": 0,
        "rank": 0,
    }


def _sort_key(row: dict):
    # Sort: points desc, GD desc, GF desc, name asc (casefolded).
    return (-row["points"], -row["gd"], -row["gf"], row["name"].casefold())


def compute_standings(teams: list, fixtures: list) -> list:
    """Return the ranked league table derived from played fixtures only."""
    rows = {t["id"]: _empty_row(t) for t in teams}

    for fx in fixtures:
        if fx.get("status") != "played":
            continue
        home = rows.get(fx["home_id"])
        away = rows.get(fx["away_id"])
        if home is None or away is None:
            continue
        hg = fx["home_score"]
        ag = fx["away_score"]

        home["played"] += 1
        away["played"] += 1
        home["gf"] += hg
        home["ga"] += ag
        away["gf"] += ag
        away["ga"] += hg

        if hg > ag:
            home["wins"] += 1
            away["losses"] += 1
        elif hg < ag:
            away["wins"] += 1
            home["losses"] += 1
        else:
            home["draws"] += 1
            away["draws"] += 1

    for row in rows.values():
        row["gd"] = row["gf"] - row["ga"]
        row["points"] = 3 * row["wins"] + 1 * row["draws"]

    ranked = sorted(rows.values(), key=_sort_key)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def is_complete(fixtures: list) -> bool:
    """True iff every fixture has been played."""
    return all(fx.get("status") == "played" for fx in fixtures)


def get_champion(teams: list, fixtures: list):
    """Return the top-ranked team iff the season is complete, else None."""
    if not fixtures or not is_complete(fixtures):
        return None
    table = compute_standings(teams, fixtures)
    if not table:
        return None
    return table[0]
