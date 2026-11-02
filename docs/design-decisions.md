# Design Decisions

1. **Fixtures list is the source of truth.** Standings are always recomputed
   via `compute_standings(teams, fixtures)`. No stored table → no drift.

2. **IDs are separate from display names.** `TM001` / `M001` are stable; names
   are display-only. Renaming would not break match references.

3. **`type(x) is int`, not `isinstance`.** `isinstance(True, int)` is True;
   `type(True) is int` is False. Bool goals are rejected everywhere.

4. **Tie-break order: pts ↓, GD ↓, GF ↓, name ↑ (casefolded).** Implemented
   as a single tuple sort key; tested with crafted equal-on-everything-except-name rows.

5. **Load validates into a temp object before swapping.** `json.load` proves
   JSON syntax; our validator proves business validity. Both must pass.

6. **Gap-free deterministic IDs.** Simple, predictable. Trade-off: no deletion
   support (out of scope for a single season).

7. **Engineer split.** A: teams, fixtures (schedule), storage. B: record_result,
   standings, CLI. Tests shared.