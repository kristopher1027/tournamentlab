import json
import tempfile
import unittest
from pathlib import Path

from tournament.errors import ValidationError
from tournament.fixtures import generate_schedule, record_result
from tournament.standings import compute_standings
from tournament.storage import load_state, save_state
from tournament.teams import new_state, register_team


def _playable_state() -> dict:
    state = new_state()
    for name in ("Thunder", "Comets", "Phoenix", "Rockets"):
        register_team(state, name)
    generate_schedule(state)
    return state


class StorageTests(unittest.TestCase):
    def test_roundtrip_preserves_ids_and_standings(self):
        state = _playable_state()
        record_result(state, "M001", 3, 1)
        record_result(state, "M002", 0, 0)
        before_rows = compute_standings(state["teams"], state["fixtures"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "season.json"
            save_state(state, path)
            loaded = load_state(path)
        self.assertEqual(
            [t["id"] for t in loaded["teams"]],
            [t["id"] for t in state["teams"]],
        )
        after_rows = compute_standings(loaded["teams"], loaded["fixtures"])
        self.assertEqual(before_rows, after_rows)

    def test_reject_fixture_referencing_unknown_team(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            save_state(state, path)
            data = json.loads(path.read_text())
            data["fixtures"][0]["home_id"] = "TM999"  # phantom
            path.write_text(json.dumps(data))
            with self.assertRaises(ValidationError):
                load_state(path)

    def test_reject_duplicate_team_ids(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.json"
            data = json.loads(json.dumps(state))
            data["teams"][1]["id"] = data["teams"][0]["id"]
            path.write_text(json.dumps(data))
            with self.assertRaises(ValidationError):
                load_state(path)

    def test_reject_duplicate_fixture_ids(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.json"
            data = json.loads(json.dumps(state))
            data["fixtures"][1]["id"] = data["fixtures"][0]["id"]
            path.write_text(json.dumps(data))
            with self.assertRaises(ValidationError):
                load_state(path)

    def test_reject_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not valid json")
            with self.assertRaises(ValidationError):
                load_state(path)

    def test_reject_missing_schema_version(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            data = json.loads(json.dumps(state))
            data.pop("schema_version")
            path.write_text(json.dumps(data))
            with self.assertRaises(ValidationError):
                load_state(path)

    def test_reject_bool_score(self):
        state = _playable_state()
        record_result(state, "M001", 1, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            data = json.loads(json.dumps(state))
            data["fixtures"][0]["home_score"] = True
            path.write_text(json.dumps(data))
            with self.assertRaises(ValidationError):
                load_state(path)
    def test_reject_incomplete_round_robin_schedule(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incomplete.json"
            data = json.loads(json.dumps(state))
            data["fixtures"].pop()
            path.write_text(json.dumps(data))

            with self.assertRaisesRegex(
                ValidationError, "Incomplete round-robin schedule"
            ):
                load_state(path)

    def test_reject_generated_season_without_fixtures(self):
        state = _playable_state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty_schedule.json"
            data = json.loads(json.dumps(state))
            data["fixtures"] = []
            path.write_text(json.dumps(data))

            with self.assertRaisesRegex(
                ValidationError, "Incomplete round-robin schedule"
            ):
                load_state(path)
if __name__ == "__main__":
    unittest.main()