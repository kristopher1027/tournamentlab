import unittest

from tournament.errors import FixtureError, ValidationError
from tournament.fixtures import generate_schedule, list_fixtures, record_result
from tournament.teams import new_state, register_team


def _state_with(*names: str) -> dict:
    state = new_state()
    for name in names:
        register_team(state, name)
    return state


class GenerateScheduleTests(unittest.TestCase):
    def setUp(self):
        self.state = _state_with("Thunder", "Comets", "Phoenix", "Rockets")

    def test_reject_fewer_than_four_teams(self):
        state = _state_with("Alpha", "Bravo", "Charlie")
        with self.assertRaises(ValidationError):
            generate_schedule(state)
        self.assertEqual(state["fixtures"], [])
        self.assertFalse(state["season_generated"])
        with self.assertRaises(ValidationError):
            generate_schedule(new_state())

    def test_four_teams_produce_six_fixtures(self):
        fixtures = generate_schedule(self.state)
        self.assertEqual(len(fixtures), 6)
        self.assertEqual(len(self.state["fixtures"]), 6)

    def test_six_teams_produce_fifteen_fixtures(self):
        state = _state_with("Aaa", "Bbb", "Ccc", "Ddd", "Eee", "Fff")
        fixtures = generate_schedule(state)
        self.assertEqual(len(fixtures), 15)

    def test_no_self_match(self):
        generate_schedule(self.state)
        for fx in list_fixtures(self.state):
            self.assertNotEqual(fx["home_id"], fx["away_id"])

    def test_no_duplicate_unordered_pair(self):
        generate_schedule(self.state)
        seen = set()
        for fx in list_fixtures(self.state):
            pair = frozenset({fx["home_id"], fx["away_id"]})
            self.assertNotIn(pair, seen)
            seen.add(pair)
        self.assertEqual(len(seen), 6)

    def test_cannot_regenerate_schedule(self):
        generate_schedule(self.state)
        with self.assertRaises(ValidationError):
            generate_schedule(self.state)
        self.assertEqual(len(self.state["fixtures"]), 6)

    def test_fixture_ids_are_deterministic_and_zero_padded(self):
        fixtures = generate_schedule(self.state)
        ids = [fx["id"] for fx in fixtures]
        self.assertEqual(ids, ["M001", "M002", "M003", "M004", "M005", "M006"])

    def test_teams_play_n_minus_1_games(self):
        generate_schedule(self.state)
        counts = {t["id"]: 0 for t in self.state["teams"]}
        for fx in self.state["fixtures"]:
            counts[fx["home_id"]] += 1
            counts[fx["away_id"]] += 1
        self.assertTrue(all(c == 3 for c in counts.values()), counts)

    def test_new_fixtures_are_pending_with_null_scores(self):
        generate_schedule(self.state)
        for fx in list_fixtures(self.state):
            self.assertEqual(fx["status"], "pending")
            self.assertIsNone(fx["home_score"])
            self.assertIsNone(fx["away_score"])

    def test_list_fixtures_returns_copy(self):
        generate_schedule(self.state)
        snapshot = list_fixtures(self.state)
        snapshot.clear()
        self.assertEqual(len(list_fixtures(self.state)), 6)


class RecordResultTests(unittest.TestCase):
    def setUp(self):
        self.state = _state_with("Thunder", "Comets", "Phoenix", "Rockets")
        generate_schedule(self.state)

    def test_record_successful_result(self):
        fx = record_result(self.state, "M001", 2, 1)
        self.assertEqual(fx["status"], "played")
        self.assertEqual(fx["home_score"], 2)
        self.assertEqual(fx["away_score"], 1)

    def test_reject_negative_score(self):
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", -1, 0)

    def test_reject_float_score(self):
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", 1.5, 0)

    def test_reject_bool_score(self):
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", True, 0)
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", 0, False)

    def test_reject_string_score(self):
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", "2", 0)

    def test_reject_unknown_fixture(self):
        with self.assertRaises(FixtureError):
            record_result(self.state, "M999", 1, 0)

    def test_reject_duplicate_result(self):
        record_result(self.state, "M001", 2, 1)
        with self.assertRaises(FixtureError):
            record_result(self.state, "M001", 5, 5)
        fx = self.state["fixtures"][0]
        self.assertEqual(fx["home_score"], 2)
        self.assertEqual(fx["away_score"], 1)

    def test_rejected_score_does_not_mutate_fixture(self):
        before = dict(self.state["fixtures"][0])
        with self.assertRaises(ValidationError):
            record_result(self.state, "M001", -3, 2)
        after = self.state["fixtures"][0]
        self.assertEqual(before, after)

    def test_zero_zero_is_valid(self):
        fx = record_result(self.state, "M001", 0, 0)
        self.assertEqual(fx["status"], "played")
        self.assertEqual((fx["home_score"], fx["away_score"]), (0, 0))


if __name__ == "__main__":
    unittest.main()