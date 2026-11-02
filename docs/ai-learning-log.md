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