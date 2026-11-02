import unittest

from tournament.errors import ValidationError
from tournament.teams import new_state, register_team, list_teams


class RegisterTeamTests(unittest.TestCase):
    def setUp(self):
        self.state = new_state()

    def test_register_returns_team_with_deterministic_id(self):
        team = register_team(self.state, "Red Comets")
        self.assertEqual(team["id"], "TM001")
        self.assertEqual(team["name"], "Red Comets")
        self.assertEqual(len(list_teams(self.state)), 1)

    def test_ids_increment(self):
        register_team(self.state, "Red Comets")
        register_team(self.state, "Blue Bolts")
        self.assertEqual([t["id"] for t in list_teams(self.state)], ["TM001", "TM002"])

    def test_reject_duplicate_casefolded_name(self):
        register_team(self.state, "Red Comets")
        with self.assertRaises(ValidationError):
            register_team(self.state, "  red comets  ")
        self.assertEqual(len(list_teams(self.state)), 1)

    def test_reject_blank_name(self):
        with self.assertRaises(ValidationError):
            register_team(self.state, "   ")
        with self.assertRaises(ValidationError):
            register_team(self.state, "x")
        self.assertEqual(len(list_teams(self.state)), 0)

    def test_reject_too_long_name(self):
        with self.assertRaises(ValidationError):
            register_team(self.state, "x" * 31)
        self.assertEqual(len(list_teams(self.state)), 0)

    def test_trimmed_display_name_is_stored(self):
        team = register_team(self.state, "   Phoenix   ")
        self.assertEqual(team["name"], "Phoenix")

    def test_name_must_be_string(self):
        with self.assertRaises(ValidationError):
            register_team(self.state, None)
        with self.assertRaises(ValidationError):
            register_team(self.state, 42)

    def test_cannot_exceed_eight_teams(self):
        for i in range(8):
            register_team(self.state, f"Team {i}")
        with self.assertRaises(ValidationError):
            register_team(self.state, "Ninth Team")
        self.assertEqual(len(list_teams(self.state)), 8)

    def test_cannot_register_after_schedule_generated(self):
        for name in ("Aaa", "Bbb", "Ccc", "Ddd"):
            register_team(self.state, name)
        self.state["season_generated"] = True
        with self.assertRaises(ValidationError):
            register_team(self.state, "Eee")

    def test_list_teams_returns_copy(self):
        register_team(self.state, "Red Comets")
        snapshot = list_teams(self.state)
        snapshot.clear()
        self.assertEqual(len(list_teams(self.state)), 1)


if __name__ == "__main__":
    unittest.main()