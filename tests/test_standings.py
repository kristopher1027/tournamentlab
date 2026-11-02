import unittest

from tournament.fixtures import generate_schedule, record_result
from tournament.standings import compute_standings, get_champion, is_complete
from tournament.teams import new_state, register_team


def _state_with(*names: str) -> dict:
    state = new_state()
    for name in names:
        register_team(state, name)
    return state


def _rows_by_name(rows):
    return {r["name"]: r for r in rows}


class StandingsTests(unittest.TestCase):
    def setUp(self):
        self.state = _state_with("Red", "Blue", "Green", "Yellow")
        generate_schedule(self.state)
        # schedule order: M001 Red-Blue, M002 Red-Green, M003 Red-Yellow,
        #                 M004 Blue-Green, M005 Blue-Yellow, M006 Green-Yellow

    def test_win_draw_loss_points(self):
        record_result(self.state, "M001", 2, 0)   # Red win
        record_result(self.state, "M004", 1, 1)   # Blue-Green draw
        rows = _rows_by_name(compute_standings(self.state["teams"], self.state["fixtures"]))
        self.assertEqual(rows["Red"]["points"], 3)
        self.assertEqual(rows["Red"]["wins"], 1)
        self.assertEqual(rows["Blue"]["points"], 1)
        self.assertEqual(rows["Blue"]["draws"], 1)
        self.assertEqual(rows["Green"]["points"], 1)
        self.assertEqual(rows["Green"]["draws"], 1)

    def test_gf_ga_gd_correct(self):
        record_result(self.state, "M001", 3, 1)  # Red 3-1 Blue
        rows = _rows_by_name(compute_standings(self.state["teams"], self.state["fixtures"]))
        self.assertEqual(rows["Red"]["gf"], 3)
        self.assertEqual(rows["Red"]["ga"], 1)
        self.assertEqual(rows["Red"]["gd"], 2)
        self.assertEqual(rows["Blue"]["gf"], 1)
        self.assertEqual(rows["Blue"]["ga"], 3)
        self.assertEqual(rows["Blue"]["gd"], -2)

    def test_pending_fixtures_ignored(self):
        rows = compute_standings(self.state["teams"], self.state["fixtures"])
        for r in rows:
            self.assertEqual(r["played"], 0)
            self.assertEqual(r["points"], 0)



    def test_sort_key_is_points_gd_gf_name(self):
        """Unit test of the sort key itself — no league fixtures involved.

        Rows are hand-built so we can pin EXACTLY how ties are broken:
          - points desc  (row P1 vs everything else)
          - GD desc      (row Q1 vs Q2: same pts, different GD)
          - GF desc      (row R1 vs R2: same pts+GD, different GF)
          - name asc     (row S1 vs S2: same pts+GD+GF, name decides)
        """
        from tournament.standings import _sort_key

        rows = [
            # wins on points alone
            {"name": "P1", "points": 9, "gd": -5, "gf": 1},
            # tie with Q2 on points, wins on GD
            {"name": "Q1", "points": 6, "gd":  3, "gf": 1},
            {"name": "Q2", "points": 6, "gd": -1, "gf": 9},
            # tie with R2 on pts+GD, wins on GF
            {"name": "R1", "points": 3, "gd":  2, "gf": 5},
            {"name": "R2", "points": 3, "gd":  2, "gf": 1},
            # tie with S2 on pts+GD+GF, wins on name (casefolded)
            {"name": "Alpha", "points": 0, "gd": 0, "gf": 0},
            {"name": "Zulu",  "points": 0, "gd": 0, "gf": 0},
        ]
        ordered = [r["name"] for r in sorted(rows, key=_sort_key)]
        self.assertEqual(
            ordered,
            ["P1", "Q1", "Q2", "R1", "R2", "Alpha", "Zulu"],
        )

    def test_tiebreak_name_end_to_end(self):
        """Full pipeline: identical points/GD/GF, only name differs.

        Two teams each win 2-0 against different opponents. Both finish on
        3 points, +2 GD, 2 GF. Only the name can separate them.
        'alpha' < 'zulu' casefolded, so Alpha must rank above Zulu.
        """
        teams = [
            {"id": "TM001", "name": "Zulu"},
            {"id": "TM002", "name": "Alpha"},
            {"id": "TM003", "name": "Bravo"},
            {"id": "TM004", "name": "Charlie"},
        ]
        fixtures = [
            # Zulu beats Bravo 2-0  → Zulu 3 pts, +2 GD, 2 GF
            {"id": "M001", "home_id": "TM001", "away_id": "TM003",
             "status": "played", "home_score": 2, "away_score": 0},
            # Alpha beats Charlie 2-0 → Alpha 3 pts, +2 GD, 2 GF
            {"id": "M002", "home_id": "TM002", "away_id": "TM004",
             "status": "played", "home_score": 2, "away_score": 0},
        ]
        rows = compute_standings(teams, fixtures)

        # Zulu and Alpha are identical on every numeric key; name decides.
        by_name = {r["name"]: r for r in rows}
        self.assertEqual(by_name["Zulu"]["points"], 3)
        self.assertEqual(by_name["Alpha"]["points"], 3)
        self.assertEqual(by_name["Zulu"]["gd"], 2)
        self.assertEqual(by_name["Alpha"]["gd"], 2)
        self.assertEqual(by_name["Zulu"]["gf"], 2)
        self.assertEqual(by_name["Alpha"]["gf"], 2)

        # Alpha must rank above Zulu because "alpha" < "zulu".
        self.assertEqual(rows[0]["name"], "Alpha")
        self.assertEqual(rows[1]["name"], "Zulu")

    def test_tiebreak_equal_points_gd_gf_uses_name(self):
        teams = [
            {"id": "TM001", "name": "zzz"},
            {"id": "TM002", "name": "aaa"},
            {"id": "TM003", "name": "mmm"},
            {"id": "TM004", "name": "nnn"},
        ]
        fixtures = [
            {"id": "M001", "home_id": "TM001", "away_id": "TM004",
             "status": "played", "home_score": 2, "away_score": 0},  # zzz 3pts +2
            {"id": "M002", "home_id": "TM002", "away_id": "TM003",
             "status": "played", "home_score": 2, "away_score": 0},  # aaa 3pts +2
        ]
        rows = compute_standings(teams, fixtures)
        # zzz vs aaa: same pts (3), same GD (+2), same GF (2) -> name decides
        self.assertEqual(rows[0]["name"], "aaa")
        self.assertEqual(rows[1]["name"], "zzz")

    def test_standings_recompute_from_matches(self):
        record_result(self.state, "M001", 2, 0)
        before = _rows_by_name(compute_standings(self.state["teams"], self.state["fixtures"]))
        self.assertEqual(before["Red"]["points"], 3)
        # Can't re-record M001, so record another match and confirm table grows
        record_result(self.state, "M004", 1, 1)
        after = _rows_by_name(compute_standings(self.state["teams"], self.state["fixtures"]))
        self.assertEqual(after["Blue"]["points"], 1)
        self.assertEqual(after["Green"]["points"], 1)

    def test_points_invariant(self):
        record_result(self.state, "M001", 2, 0)  # non-draw
        record_result(self.state, "M004", 1, 1)  # draw
        rows = compute_standings(self.state["teams"], self.state["fixtures"])
        total = sum(r["points"] for r in rows)
        non_draws = sum(1 for fx in self.state["fixtures"]
                        if fx["status"] == "played" and fx["home_score"] != fx["away_score"])
        draws = sum(1 for fx in self.state["fixtures"]
                    if fx["status"] == "played" and fx["home_score"] == fx["away_score"])
        self.assertEqual(total, 3 * non_draws + 2 * draws)

    def test_gf_equals_ga_in_total(self):
        record_result(self.state, "M001", 3, 2)
        record_result(self.state, "M004", 1, 0)
        rows = compute_standings(self.state["teams"], self.state["fixtures"])
        self.assertEqual(sum(r["gf"] for r in rows), sum(r["ga"] for r in rows))

    def test_champion_none_until_all_played(self):
        record_result(self.state, "M001", 2, 0)
        self.assertFalse(is_complete(self.state["fixtures"]))
        self.assertIsNone(get_champion(self.state["teams"], self.state["fixtures"]))

    def test_champion_after_last_match(self):
        for fid in ("M001", "M002", "M003", "M004", "M005", "M006"):
            record_result(self.state, fid, 1, 0)
        self.assertTrue(is_complete(self.state["fixtures"]))
        champ = get_champion(self.state["teams"], self.state["fixtures"])
        self.assertIsNotNone(champ)
        self.assertEqual(champ["rank"], 1)


if __name__ == "__main__":
    unittest.main()