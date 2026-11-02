"""End-to-end controlled demo — reproducible, prints each step."""
from pathlib import Path
import tempfile

from tournament.fixtures import generate_schedule, record_result
from tournament.standings import compute_standings, get_champion, is_complete
from tournament.storage import load_state, save_state
from tournament.teams import new_state, register_team


def _print_table(rows):
    print(f"{'#':>2}  {'Team':<10} {'P':>2} {'W':>2} {'D':>2} {'L':>2} "
          f"{'GF':>3} {'GA':>3} {'GD':>3} {'Pts':>3}")
    for r in rows:
        gd = f"+{r['gd']}" if r["gd"] > 0 else str(r["gd"])
        print(f"{r['rank']:>2}  {r['name']:<10} {r['played']:>2} {r['wins']:>2} "
              f"{r['draws']:>2} {r['losses']:>2} {r['gf']:>3} {r['ga']:>3} "
              f"{gd:>3} {r['points']:>3}")


def main():
    state = new_state()
    for name in ("Thunder", "Comets", "Phoenix", "Rockets"):
        register_team(state, name)
    print("Teams:", [t["name"] for t in state["teams"]])

    fixtures = generate_schedule(state)
    print(f"Fixtures ({len(fixtures)}):")
    for fx in fixtures:
        print(f"  {fx['id']}  {fx['home_id']} vs {fx['away_id']}")

    # One win, one draw
    record_result(state, "M001", 3, 1)  # Thunder vs Comets
    record_result(state, "M006", 0, 0)  # Phoenix vs Rockets  (M006 is last pair)
    print("\nAfter two results:")
    _print_table(compute_standings(state["teams"], state["fixtures"]))

    # Invalid score must not change anything
    try:
        record_result(state, "M002", -1, 0)
    except Exception as exc:
        print(f"\nRejected invalid score: {exc}")
    print("State unchanged:", state["fixtures"][1]["status"] == "pending")

    # Save + reload
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "season.json"
        save_state(state, path)
        loaded = load_state(path)
    assert compute_standings(state["teams"], state["fixtures"]) == \
           compute_standings(loaded["teams"], loaded["fixtures"])
    print("Reload preserves standings: OK")

    # Finish season with fixed scores
    for fid in ("M002", "M003", "M004", "M005"):
        record_result(state, fid, 1, 0)
    print("\nFinal table:")
    _print_table(compute_standings(state["teams"], state["fixtures"]))
    print("\nSeason complete:", is_complete(state["fixtures"]))
    champ = get_champion(state["teams"], state["fixtures"])
    print(f"Champion: {champ['name']}")


if __name__ == "__main__":
    main()