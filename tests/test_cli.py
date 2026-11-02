import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tournament.cli import run
from tournament.fixtures import generate_schedule
from tournament.teams import new_state, register_team


def _feed_inputs(answers):
    """Return a side_effect list for input() that pops from answers."""
    it = iter(answers)
    def _fake_input(_prompt=""):
        try:
            return next(it)
        except StopIteration:
            return "0"  # safety: quit if we run out
    return _fake_input


class CLITests(unittest.TestCase):
    def setUp(self):
        self.state = new_state()
        for name in ("Thunder", "Comets", "Phoenix", "Rockets"):
            register_team(self.state, name)
        generate_schedule(self.state)

    def _run(self, answers):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=_feed_inputs(answers)):
            with redirect_stdout(buf):
                run(self.state)
        return buf.getvalue()

    def test_empty_menu_choice_reprompts(self):
        out = self._run(["", "0"])
        self.assertIn("Unknown option", out)

    def test_invalid_menu_choice_reprompts(self):
        out = self._run(["99", "0"])
        self.assertIn("Unknown option", out)

    def test_bad_score_prints_error_and_continues(self):
        # menu 5 -> fixture M001, then "abc" (bad), then 1, 0
        out = self._run(["5", "M001", "abc", "1", "0", "0"])
        self.assertIn("whole number", out)
        self.assertIn("Recorded", out)

    def test_champion_only_when_complete(self):
        out = self._run(["7", "0"])  # champion with 0 games played
        self.assertIn("in progress", out.lower())


if __name__ == "__main__":
    unittest.main()