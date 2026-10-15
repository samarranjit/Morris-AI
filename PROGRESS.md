# Saved implementation checkpoint

All implementation stages are complete. What remains is in CHECKLIST.md under
"Human tournament/submission tasks".

## Completed
- PDF-specific capture fallback, board diagram correction, expanded move tests.
- Minimax and alpha-beta with deterministic ties and actual estimator counts.
- Both colors, all phases, all eight assignment command-line programs.
- Improved evaluator with explicit weights and no baseline-formula changes.
- Submission answers: Examples.txt (Part II and Part IV, with real program
  output) and MyStaticEstimation.txt (the four Part IV questions plus two boards).
- Timed tournament agent with placement tracking, history validation, and draws.
- Interactive match console inside morris/tournament.py, started by running
  TournamentAgent.py with no board arguments. It replaced tournament_console/play.py
  and was checked against it with identical typed input.
- Six complete local games, saved histories, and timing measurements.
- Submission ZIP; all nine entry scripts passed from a fresh extraction.

## Latest verification
- 57 automated tests passed.
- Examples.txt regenerated from the submitted programs; every printed line matched.
- Baseline estimator is byte-for-byte identical to the original.
- Four equal-depth evaluator comparison games: improved won 3, drew 1.

## Resume commands
Run from the project root:

    python3 -m unittest discover -s tests -v
    python3 tools/verify_project.py --examples-only
    python3 tools/build_submission.py

The second command regenerates Examples.txt (drop --examples-only to also
regenerate Validation.txt and validation.json, which takes longer).
The third rebuilds dist/Morris-AI-submission.zip and verifies a clean extraction.

Read README.md for usage and EXPLANATION.md for the implementation walkthrough.

## Decisions to retain
We follow the last GenerateRemove line on Variant PDF page 4: if no opposing
piece outside a mill can be removed, keep the moved board without capture. The
ambiguous PDF wording is not an instructor-confirmed clarification. Do not
silently switch to standard Morris rules. An instructor ruling should trigger a
rule/test change and regeneration of the evidence together.

The user reports an extension to the printed deadlines; the new dates are not
known here. No official matches, external posts, result submissions, or Canvas
upload have been performed. These are still team responsibilities.
