# Saved implementation checkpoint

All seven requested implementation stages are complete and saved. The original
project folder has been updated as well as the deliverable copy. No Git commit
was created; use git diff to review the changes. Existing Git history is intact.

## Completed
- PDF-specific capture fallback, board diagram correction, expanded move tests.
- Minimax and alpha-beta with deterministic ties and actual estimator counts.
- Both colors, all phases, all eight assignment command-line programs.
- Improved evaluator with explicit weights and no baseline-formula changes.
- Required written answers and four reproducible comparison examples.
- Timed tournament runner with placement tracking, history validation, and draws.
- Six complete local games, saved histories, and timing measurements.
- Submission ZIP; all nine entry scripts passed from a fresh extraction.

## Latest verification
- 46 automated tests passed in the original project folder.
- Baseline estimator is byte-for-byte identical to the original.
- A real 0.05-second tournament search completed depth 3, interrupted the next
  iteration, and returned a legal move in approximately 0.05003 seconds.
- Four equal-depth evaluator comparison games: improved won 3, drew 1.
- Two additional timed-runner games completed with legal histories.

## Resume commands
Run from the project root:

    python3 -m unittest discover -s tests -v
    python3 tools/verify_project.py
    python3 tools/build_submission.py

The second command regenerates Examples.txt, Validation.txt, and validation.json.
The third rebuilds dist/Morris-AI-submission.zip and verifies a clean extraction.

Read README.md for usage and EXPLANATION.md for the implementation walkthrough.
Read CHECKLIST.md for remaining human tournament and submission tasks.

## Decisions to retain
The user instructed us to follow the best reading of the rules. We follow the
last GenerateRemove line on Variant PDF page 4: if no opposing piece outside a
mill can be removed, keep the moved board without capture. The ambiguous PDF
wording is not an instructor-confirmed clarification. Do not silently switch to
standard Morris rules. An instructor ruling should trigger a rule/test change
and regeneration of the evidence together.

The user reports an extension to the printed deadlines; the new dates are not
known here. No official matches, external posts, result submissions, or Canvas
upload have been performed. These are still team responsibilities.
