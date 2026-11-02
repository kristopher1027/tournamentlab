"""Interactive menu — the only module that does input()/print()."""
from __future__ import annotations

from pathlib import Path

from .errors import FixtureError, TournamentError, ValidationError
from .fixtures import generate_schedule, list_fixtures, record_result
from .standings import compute_standings, get_champion, is_complete
from .storage import load_state, save_state
from .teams import list_teams, new_state, register_team

MENU = """\
TournamentLab — Esports League Manager
  1) Register team
  2) List teams
  3) Generate schedule
  4) List fixtures
  5) Record result
  6) Show standings
  7) Show champion
  8) Save season
  9) Load season
  0) Quit
"""


def _ask_int(prompt: str) -> int:
    """Prompt until the user enters a nonnegative int (bool not possible via input)."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  ! Please enter a whole number.")
            continue
        if value < 0:
            print("  ! Score cannot be negative.")
            continue
        return value


def _print_table(rows: list[dict]) -> None:
    header = f"{'#':>2}  {'Team':<20} {'P':>2} {'W':>2} {'D':>2} {'L':>2} " \
             f"{'GF':>3} {'GA':>3} {'GD':>3} {'Pts':>3}"
    print(header)
    print("-" * len(header))
    for r in rows:
        gd = f"+{r['gd']}" if r["gd"] > 0 else str(r["gd"])
        print(f"{r['rank']:>2}  {r['name']:<20} {r['played']:>2} {r['wins']:>2} "
              f"{r['draws']:>2} {r['losses']:>2} {r['gf']:>3} {r['ga']:>3} "
              f"{gd:>3} {r['points']:>3}")


def _cmd_register(state: dict) -> None:
    name = input("Team name: ")
    team = register_team(state, name)
    print(f"  + Registered {team['name']} ({team['id']}).")


def _cmd_list_teams(state: dict) -> None:
    teams = list_teams(state)
    if not teams:
        print("  (no teams registered yet)")
        return
    for t in teams:
        print(f"  {t['id']}  {t['name']}")


def _cmd_generate(state: dict) -> None:
    fixtures = generate_schedule(state)
    print(f"  + Generated {len(fixtures)} fixtures.")


def _cmd_list_fixtures(state: dict) -> None:
    fixtures = list_fixtures(state)
    if not fixtures:
        print("  (no fixtures generated yet)")
        return
    for fx in fixtures:
        if fx["status"] == "played":
            score = f"{fx['home_score']}-{fx['away_score']}"
        else:
            score = "—"
        print(f"  {fx['id']}  {fx['home_id']} vs {fx['away_id']}  "
              f"[{fx['status']}] {score}")


def _cmd_record(state: dict) -> None:
    fixture_id = input("Fixture ID: ").strip()
    home = _ask_int("Home score: ")
    away = _ask_int("Away score: ")
    fx = record_result(state, fixture_id, home, away)
    print(f"  + Recorded {fx['id']}: {fx['home_score']}-{fx['away_score']}")


def _cmd_standings(state: dict) -> None:
    rows = compute_standings(state["teams"], state["fixtures"])
    _print_table(rows)
    if is_complete(state["fixtures"]):
        champ = get_champion(state["teams"], state["fixtures"])
        print(f"\nStatus: complete — Champion: {champ['name']}")
    else:
        remaining = sum(1 for fx in state["fixtures"] if fx["status"] != "played")
        print(f"\nStatus: in progress — {remaining} fixture(s) remaining.")


def _cmd_champion(state: dict) -> None:
    champ = get_champion(state["teams"], state["fixtures"])
    if champ is None:
        print("  Season is in progress — no champion yet.")
    else:
        print(f"  Champion: {champ['name']}")


def _cmd_save(state: dict) -> None:
    path = input("Save to path (e.g. season.json): ").strip()
    save_state(state, path)
    print(f"  + Saved to {path}.")


def _cmd_load(state: dict) -> None:
    path = input("Load from path: ").strip()
    loaded = load_state(path)  # raises on bad data, never mutates live state
    state.clear()
    state.update(loaded)
    print(f"  + Loaded season from {path}.")


_HANDLERS = {
    "1": _cmd_register,
    "2": _cmd_list_teams,
    "3": _cmd_generate,
    "4": _cmd_list_fixtures,
    "5": _cmd_record,
    "6": _cmd_standings,
    "7": _cmd_champion,
    "8": _cmd_save,
    "9": _cmd_load,
}


def run(state: dict | None = None) -> None:
    if state is None:
        state = new_state()
    while True:
        print()
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == "0":
            print("Bye.")
            return
        handler = _HANDLERS.get(choice)
        if handler is None:
            print("  ! Unknown option.")
            continue
        try:
            handler(state)
        except (ValidationError, FixtureError) as exc:
            print(f"  ! {exc}")
        except TournamentError as exc:  # catch-all for any other domain error
            print(f"  ! {exc}")