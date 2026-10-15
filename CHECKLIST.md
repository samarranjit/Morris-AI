# Completion checklist

## 1. Rules and generators
- [x] Inspect the PDF board diagrams and both sample positions.
- [x] Verify the 23 locations and 18 mill lines; fix the ASCII diagram.
- [x] Follow Variant p. 4's fallback: no eligible opponent outside a mill means no capture.
- [x] Test protected mills, no opponent, placements, slides, hops, and both colors.
- [ ] Instructor confirmation of the ambiguous all-pieces-in-mills fallback, if available.

## 2. Minimax
- [x] Alternate maximizing White and minimizing Black; preserve first tied move.
- [x] Return an immediate root successor and count actual estimator calls.
- [x] Handle depth zero, piece losses, and the side-to-move blockade.
- [x] Test exact counts and an independent exhaustive oracle across depths and phases.

## 3. Alpha-beta
- [x] Share the rules and evaluator with minimax; enable alpha >= beta cutoffs.
- [x] Verify identical decisions and values, with no more evaluations.
- [x] Record two real pruning examples in Examples.txt.

## 4. Black and interfaces
- [x] Verify Black color-swapping and legal output for both phases.
- [x] Check the three exact stdout lines and strict input validation.
- [x] Handle missing directories and file errors; avoid partially written boards.

## 5. Improved evaluator
- [x] Preserve the baseline file unchanged.
- [x] Implement documented opening and midgame/endgame formulas.
- [x] Check symmetry, hopping mobility, terminal bounds, and search equivalence.

## 6. Written answers for the submission
- [x] Examples.txt Part II: two pruning cases with commands and real program output.
- [x] Examples.txt Part IV: two improved-move disagreements with program output and reasons.
- [x] MyStaticEstimation.txt: the four required answers, plus the two boards in section 5.
- [x] docs/programs.md maps each handout requirement to the file section that answers it.
- [x] Beginner walkthrough in EXPLANATION.md.

## 7. Tournament and packaging
- [x] Iterative deepening, time budget, and legal fallback.
- [x] Placement-aware phase transition inside search.
- [x] Persistent validated game history and threefold repetition.
- [x] Six complete validated local games, timings, and saved logs.
- [x] Interactive match console in TournamentAgent.py (no board arguments).
- [x] Submission ZIP and clean-extraction smoke checks of every entry point.
