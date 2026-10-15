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

## 8. A stronger tournament agent

Ground rules for this whole section:
- Only the tournament path changes (`morris/tournament.py`, `programs/TournamentAgent.py`, and new tournament-only modules). The Part I-IV programs keep their exact output, moves, and evaluation counts.
- The search stays minimax with alpha-beta. Every item below speeds up or sharpens alpha-beta; none replaces it.
- After each step, run `python -m unittest discover -s tests` and `python3 tools/verify_project.py --examples-only`.
- Keep an item only if the measurements in 8.1 show it helps.
- Nothing guarantees winning every game. The goal is to search deeper, evaluate better, and never lose to a crash, a timeout, or an illegal move.

### 8.1 Measurement harness (do this first)
- [ ] Build a fixed benchmark set: about 10 opening, 10 midgame, and 10 hopping boards, including both handout positions.
- [ ] Write `tools/benchmark.py`: for each board, report the depth completed, positions per second, and the move chosen at 30 s and 180 s.
- [ ] Write `tools/self_play.py`: play agent version A against version B over many games, swapping colors, with a shorter time limit (for example 10 s). Report wins, losses, and draws.
- [ ] Save the current agent's numbers as the baseline to beat.

### 8.2 Faster single-core search
- [ ] Profile with `cProfile` on the benchmark boards and list the slowest functions.
- [ ] Speed up the hot paths without changing results: precomputed neighbor and mill tables, fewer string copies, and mill checks that look only at lines through the moved square.
- [x] Order moves, inside `programs/TournamentAgent.py`: captures first, then killer moves, history moves, and the saved best move. Blocking an opponent mill is not separate yet.
- [x] Try the previous depth's best move first, at the root from the last iteration and inside the tree from the transposition table.
- [x] Killer moves and the history heuristic.
- [x] Transposition table keyed on board, side, placements, and the repetition history. A stored value is used only at the same depth, so the result matches plain alpha-beta; the saved move is tried first at any depth. Capped at one million entries per worker.
- [ ] Use the four-fold symmetry of the board (left-right mirror, top-bottom mirror) to share table entries, if the mills and neighbors are symmetric. Verify this with a test before relying on it.
- [ ] Aspiration windows: start each depth with a narrow window around the last score, and re-search with the full window if the result falls outside it.
- [x] Test: at fixed depths, the faster search returns the same board and value as plain alpha-beta, including depth 5 where replies are split.

### 8.3 Using every core
Python threads cannot run the search in parallel, so this uses separate processes.
- [x] Root splitting, entirely inside `programs/TournamentAgent.py` (the `morris/` package is unchanged): root moves go to a `ProcessPoolExecutor` with one worker per core (`os.cpu_count()`). Each worker runs alpha-beta, with the same rules as `morris/search.py`, on its move.
- [x] Search the most promising move first, alone, then the rest in parallel, ordered by the previous depth's scores.
- [x] Share the best root score between workers (`multiprocessing.Array`), so later moves are searched with a tighter alpha. Earlier moves use alpha one lower, so ties still go to the first generated move.
- [x] Each worker keeps its own transposition table, killers, and history, and workers are reused across depths and moves.
- [x] Time budget across processes: each worker checks the same deadline, and the parent keeps the last fully finished depth.
- [x] `if __name__ == "__main__"` guards and the `spawn` start method, so it works on macOS and Windows.
- [x] Split the opponent's replies across cores when a position has about twelve or fewer root moves, and always split the first root move once the depth reaches 5.
- [x] Tests in `tests/test_parallel.py`: same board and value as sequential alpha-beta on random opening and midgame positions, depths 2-5, the phase change, and repetition counts; deadline; tiny budget.
- [x] `--workers N` in both TournamentAgent modes, defaulting to the core count. Falls back to one process if workers cannot start or die.
- [x] Benchmark (`tools/benchmark.py --seconds 20`, 14 cores): opening depth 6 to 8, handout midgame depth 8 to 10, random midgame depth 7 to 8. Results in `docs/tournament.md`.

### 8.4 Smarter time use
- [ ] Spend the budget by situation: more on complex midgame boards and when the score drops between depths, less on forced moves.
- [ ] If only one legal move exists, play it at once.
- [ ] Do not start a new depth that probably cannot finish; estimate its time from the growth between earlier depths.
- [ ] Keep a fixed safety margin (for example 20 s) for pasting and posting within the 4-minute limit.

### 8.5 A stronger evaluator
- [ ] Add candidate features: open mills (two pieces and an empty square), double mills, pieces that can close a mill next move, and an endgame term for the 3-piece hopping phase.
- [ ] Tune the weights by self-play (8.1): change one weight at a time and keep a change only if it wins more games over at least 50 games with colors swapped.
- [ ] Keep the evaluator symmetric (swapping colors negates the score), and keep game results at plus or minus 10000.
- [ ] Prefer faster wins and slower losses: adjust win and loss scores by depth so the agent finishes won games instead of shuffling.
- [ ] Keep `deliverables/MyStaticEstimation.txt` matching the evaluator that is submitted, or keep the tuned tournament evaluator separate.

### 8.6 Opening preparation (check with the instructor first)
- [ ] Ask the instructor whether a precomputed opening table or endgame table is allowed, since it is not minimax or alpha-beta at play time.
- [ ] If allowed: run long overnight searches on all opening positions up to a few placements, using the full machine, and store the best moves.
- [ ] If allowed: solve small endgames (for example 3 against 3 hopping) offline and store won, lost, and drawn results.

### 8.7 Robustness (never lose to a bug)
- [ ] Always keep a legal fallback move ready from depth 1 before searching deeper.
- [ ] Validate every opponent board and every agent board as a legal successor before saving or posting. This is already done; keep the tests.
- [ ] Save the session after every move so a crash, closed laptop, or reboot can resume with `--resume`.
- [ ] Handle `Ctrl+C` and worker crashes by returning the best finished move, never a traceback.
- [ ] Threefold repetition and draw handling: avoid repeating when ahead, seek a repetition when behind.
- [ ] Test long games, full 18 placements, all-in-mill captures, both colors, and hopping on both sides.

### 8.8 Match-day setup
- [ ] Plug in the laptop, close other apps, and turn off sleep. On macOS run the agent with `caffeinate -i python3 programs/TournamentAgent.py`.
- [ ] Run `tools/benchmark.py` on the match machine once, to confirm the depth reached and that every core is busy (Activity Monitor).
- [ ] Do a full practice game in the console from start to finish, including `--resume` after quitting.
- [ ] Keep a second machine or teammate ready with the same commit and the saved session file.

### 8.9 Wrap-up
- [ ] Record the before-and-after depth, speed, and self-play results in `docs/tournament.md`.
- [ ] Make sure every team member can explain the move ordering, transposition table, parallel search, and evaluator changes.
- [ ] Rebuild the ZIP with `tools/build_submission.py` and rerun its smoke checks.
