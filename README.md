# Morris AI: complete implementation

Python 3.10 or newer; standard library only. Run commands from this folder.
The original course PDFs remain in `docs/`. See `EXPLANATION.md` for a beginner
walkthrough, limitations, and the exact rule interpretation used.

```bash
python3 -m unittest discover -s tests -v
python3 programs/MiniMaxOpening.py examples/empty_board.txt out/move.txt 2
python3 programs/ABGame.py examples/handout_position_1.txt out/move.txt 3
```

The eight assignment programs accept input file, output file, and depth.
They print exactly three lines and write the selected 23-character board.
Black programs report values from Black's perspective. Depth zero evaluates
the input without choosing a move; use depth >= 1 when playing.

## Tournament: keep one history file per game

First move as White:

```bash
python3 programs/TournamentAgent.py examples/empty_board.txt out/move.txt 12 white opening --seconds 180 --history out/game1.json
```

Save the opponent's next board as `out/opponent.txt`, then run:

```bash
python3 programs/TournamentAgent.py out/opponent.txt out/move.txt 12 white opening --seconds 180 --history out/game1.json
```

For Black's first turn, save White's first posted board in the input file and
use a new history filename with `black opening`. The runner infers the initial
empty board and checks White's first placement. After the first 18 placements,
use `midgame`. The history is updated automatically for the opponent's input
and our selected move. Use a new history file for the next official game.

Depth 12 is a ceiling, not a promise to finish twelve plies. The runner searches
1, 2, 3, ... and uses the last fully completed result within the time budget.
The default budget is 180 seconds; the maximum accepted budget is 210 seconds.
The tournament allows four minutes INCLUDING copying, checking, and posting.
The search timer starts when the program runs, not when Teams received the
opponent's post. Reduce --seconds when you have already used part of the window.

Without history, provide the known placement count during opening:

```bash
python3 programs/TournamentAgent.py examples/empty_board.txt out/move.txt 6 white opening --placements 0 --seconds 10
```

Without history, the program cannot validate the opponent's prior move or
recognize historical threefold repetitions. Track those manually. It never
infers the opening phase from surviving piece counts. Do not use synthetic
handout diagrams as a new match-history starting point; use --placements for
standalone analysis of such positions.

Only post an output after a successful exit (code 0), and check the three-line
result. Diagnostics such as completed depth go to stderr. A failed command may
leave an OLD output file in place; never mistake it for a new decision.

## Evidence and submission

```bash
python3 tools/verify_project.py
python3 tools/build_submission.py
```

- `deliverables/Examples.txt`: two pruning examples and two improved choices.
- `deliverables/MyStaticEstimation.txt`: all four required written answers.
- `deliverables/Validation.txt`: measured timing and local game results.
- `deliverables/validation.json`: machine-readable results and complete games.
- `dist/Morris-AI-submission.zip`: nine entry scripts at ZIP root, `morris/`,
  the two required text files, and concise submission notes.

The build script extracts the archive in a fresh temporary directory and runs
all nine entry points there. Include the `morris/` package: the entry scripts
are intentionally small wrappers and depend on it.

## Course and rule notes

Search remains minimax/alpha-beta. There is no MCTS, neural network, external
engine, opening database, or learned policy. The baseline estimator is unchanged.

Capture fallback follows Variant PDF p. 4: if there is no opposing piece outside
a mill, retain the move without capture. This is an explicit interpretation of
ambiguous pseudocode, not an instructor-confirmed ruling. See EXPLANATION.md.

The user reports an extension to the printed deadlines. Confirm the new dates
in the course announcement. No matches have been scheduled, posted, or reported
by these tools. Tournament participation and official reporting remain team tasks.
