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

## Tournament: interactive console (use this for official games)

Run the tournament agent with no board arguments:

```bash
python3 programs/TournamentAgent.py
```

On macOS you can instead double-click `programs/Start-Tournament.command`.

Choose `new`, then `white` or `black`. Press Enter for a 180-second search
budget and depth ceiling 12. Use 2 seconds for a quick practice session.

- White: the agent calculates immediately and prints your first Teams message.
- Black: the console waits for White's board before calculating your response.
- Paste a 23-character opponent board and press Enter. The two-line Teams post
  (`Move N - Color` followed by its board) is also accepted.
- An illegal board is rejected without advancing the game. Paste again.
- After a valid board, the agent searches and prints two lines to copy to Teams.
  Post them yourself; the console never posts online.

The console tracks phase changes, hopping, move numbers, and threefold
repetition. It stops when the game ends. The saved state assumes you post the
displayed move, so do not post a different board.

Commands while waiting for the opponent:

- `show`: display the current board and the last recorded move.
- `time 60`: give future searches 60 seconds instead of the current budget.
- `quit`: stop. Progress is already saved.

The opponent's Teams timestamp starts the four-minute window, and waiting to
paste their move uses part of it. Lower the budget with `time N` when needed.

Every new game gets its own session JSON in `out/tournament-console/`, and the
path is printed in Terminal. To resume, run the console and choose `resume`, or:

```bash
python3 programs/TournamentAgent.py --resume out/tournament-console/<session>.json
```

A move your team already calculated is shown again, not recalculated. If the
opponent's move was saved but the search was interrupted, search restarts from
that board. Ctrl+C or closing Terminal does not erase accepted moves.
A session JSON is not the same file as a `--history` array below; keep using
whichever one a game started with.

## Tournament: one move per command

The same program also runs a single move from a board file. Keep one history
file per game. First move as White:

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

## Written answers for the submission

The handout asks for two text files with the code. Both are in `deliverables/`
and both go into the ZIP.

| Handout requirement | Answered in |
| --- | --- |
| Part II: at least two cases where alpha-beta evaluates fewer positions than minimax | `Examples.txt`, Part II (cases 1 and 2) |
| Part IV: features used by the improved estimator | `MyStaticEstimation.txt`, section 1 |
| Part IV: why those features were selected | `MyStaticEstimation.txt`, section 2 |
| Part IV: how they are combined | `MyStaticEstimation.txt`, section 3 |
| Part IV: why it is better than the original estimator | `MyStaticEstimation.txt`, section 4 |
| Part IV: two boards where the improved estimator picks a different move, and why | `MyStaticEstimation.txt`, section 5, and `Examples.txt`, Part IV |

Each example in `Examples.txt` shows the command and the three lines the
submitted program printed. Regenerate it after any change to the search or the
estimators:

```bash
python3 tools/verify_project.py --examples-only
```

That command also stops with an error if `MyStaticEstimation.txt` quotes a
move the programs no longer choose. Section 5 of that file is written by hand,
so update it if this happens.

## Evidence and submission

```bash
python3 tools/verify_project.py
python3 tools/build_submission.py
```

- `deliverables/Examples.txt`: the Part II and Part IV examples (submitted).
- `deliverables/MyStaticEstimation.txt`: the Part IV written answers (submitted).
- `deliverables/Validation.txt`: measured timing and local game results (not submitted).
- `deliverables/validation.json`: machine-readable results and complete games (not submitted).
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

## Other documents

- [EXPLANATION.md](EXPLANATION.md): how the move generator, minimax, alpha-beta,
  estimators, and tournament agent work. Read it before explaining the code.
- [CHECKLIST.md](CHECKLIST.md): what is done and what the team still has to do.
- [docs/rules.md](docs/rules.md), [docs/board.md](docs/board.md): the game rules
  and the 23 board locations.
- [docs/programs.md](docs/programs.md): the required programs, output format,
  and grading weights.
- [docs/tournament.md](docs/tournament.md): match protocol and result reporting.
