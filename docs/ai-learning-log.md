## Cycle 1 — Trusting AI test data without hand-verifying

- **Topic I didn't know:** how to design a test that exercises
  multi-key tie-breaks without accidentally having no ties at all.
- **Exact prompt I used:** "Give me unittest code for a 4-team
  league that exercises points→GD→GF→name tie-breaks."
- **AI's explanation, my words:** AI shipped a fixture set with
  scores, but computed the expected table incorrectly twice.
- **Tiny independent experiment:** I hand-computed the table from
  the fixtures on paper before running the test.
- **Actual result:** The hand-computed table matched the code's
  output; the AI's `expected` list was wrong.
- **Misconception corrected:** The failing test was not the code's
  fault. Crafted fixtures must be designed so ties actually occur —
  and the sort-key logic is easier to test in isolation than
  end-to-end.
- **Related commit / test:** split into `test_sort_key_is_*` (unit)
  and `test_tiebreak_name_end_to_end` (integration).

## Cycle 2 — Validating complete round-robin schedules

- **Topic I didn't know:** how to verify that a generated round-robin season contains every required matchup.
- **Exact prompt I used:** "Help me validate that a generated round-robin schedule contains all required fixtures and reject incomplete schedules."
- **AI's explanation, my words:** AI explained that a round-robin schedule for `n` teams must contain `n(n-1)/2` unique fixtures.
- **Tiny independent experiment:** I tested a generated schedule with four teams, then removed a fixture and checked whether storage validation rejected it.
- **Actual result:** The complete schedule passed validation, while the incomplete schedule was rejected.
- **Misconception corrected:** Checking that fixtures reference valid teams is not enough. A schedule can contain only valid teams and still be incomplete.
- **Related commit / test:** `33fed92` — `fix(storage): reject incomplete tournament schedules`; `test_reject_incomplete_round_robin_schedule` and `test_reject_generated_season_without_fixtures`.

## Cycle 3 — Python imports when running scripts from subdirectories

- **Topic I didn't know:** why a Python script can fail to import a project package when executed directly from a subdirectory.
- **Exact prompt I used:** "Help me fix ModuleNotFoundError: No module named 'tournament' when running scripts/demo_season.py."
- **AI's explanation, my words:** AI explained that Python's module search path depends on how a script is launched, so the project root might not be available when running a script inside `scripts/`.
- **Tiny independent experiment:** I ran `python3 scripts/demo_season.py` from the project root and checked whether the script could import the `tournament` package.
- **Actual result:** Adding the project root to `sys.path` allowed the demo script to run successfully.
- **Misconception corrected:** Having a package in the repository does not automatically guarantee that every directly executed script can import it.
- **Related file:** `scripts/demo_season.py`.
