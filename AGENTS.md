# AGENTS.md

Guide for coding agents working in this repository. Read this before changing code. The course handouts in `docs/Project.pdf` and `docs/Morris-Variant.pdf` are the assignment. `README.md` and the other files in `docs/` restate what those PDFs specify. [CHECKLIST.md](CHECKLIST.md) is the ordered task list. Do the unchecked step, then check the box.

## Course constraints

- The search is minimax and alpha-beta, as covered in class. The tournament compares those algorithms and the static estimators. Do not add a different game-playing algorithm.
- Teammates may share this repository. Other teams may not receive Python source, complete prompts, implementation-specific solutions, or the improved static estimator.
- The team is responsible for being able to explain the move generator, minimax, alpha-beta, and the estimator.

## Repository map

| Path | Role |
| --- | --- |
| `morris/board.py` | 23 locations, neighbors, mills, color swap, diagram printer |
| `morris/moves.py` | Handout generators: add, slide, hop, remove, and Black via color swap |
| `morris/estimation.py` | Baseline opening and midgame/endgame estimators. Leave these as specified. |
| `morris/improved.py` | Part IV estimators. This is where the new evaluation goes. |
| `morris/search.py` | Part I minimax and Part II alpha-beta. Both are implemented and tested. |
| `morris/cli.py` | Shared argument parsing and the three-line output. |
| `morris/tournament.py` | Timed iterative-deepening alpha-beta, match history, and the interactive match console. |
| `programs/TournamentAgent.py` | Also holds the tournament-only parallel search (root moves split across worker processes), so the agent can be shared as this one file plus `morris/`. Keep it there. Its alpha-beta must follow `morris/search.py` and return the same board and value (`tests/test_parallel.py`). |
| `tools/benchmark.py` | Depth reached and evaluations per second for different worker counts. |
| `tools/verify_project.py` | Regenerates `Examples.txt` from real program runs, plus timings and local games. |
| `tools/build_submission.py` | Builds and smoke-tests the submission ZIP. |
| `programs/*.py` | Required program names. Run them as `python programs/MiniMaxOpening.py`. Each one only calls `morris.cli.run`. Copy these files to the ZIP root at submission time. |
| `deliverables/` | `Examples.txt` and `MyStaticEstimation.txt` for the ZIP. |
| `examples/` | Board files, including the two positions drawn in the handout. |
| `tests/` | Handout facts, moves, search against an exhaustive oracle, CLI, improved estimator, tournament, console. |

## Board contract

- A position is a string of length 23. `W` white, `B` black, `x` empty.
- Index 0 is `a0` at the bottom-left. The names are in `morris.board.LOCATIONS`.
- There is no `d2` and no `d3`. `c2-e2` and `d0-d1` are adjacent, and they are not mills.
- Neighbor lists are sorted by index. Generators scan locations `0..22` and then those neighbor lists. On a tied estimate, search keeps the earliest board in that list so minimax and alpha-beta select the same move.
- `format_board(board)` prints a diagram for checking a position by hand.

The handout's `closeMill` case written as index 1 `(d3)` is `d0`. Its condition is the `a0-d0-g0` line, which matches the index table.

## Moves

White generators follow the handout pseudocode.

- Opening: `generate_add`. Place one white piece on an empty square.
- Midgame: `generate_move`. Slide along an edge to an empty neighbor.
- Endgame: `generate_hopping`, used when White has exactly three pieces.
- A move that closes a mill also removes one black piece that is not itself in a mill. When every black piece is in a mill, retain the move without capture, following the final GenerateRemove line (Variant p. 4). This is a documented interpretation of ambiguous pseudocode, not an instructor-confirmed ruling.

Black moves: swap colors, generate the White moves, swap the results. `MiniMaxOpeningBlack.py` and `MiniMaxGameBlack.py` use that same swap around the White search. After the swap, a larger minimax estimate favors Black.

Opening versus midgame is chosen by which program runs. Piece counts on the board do not identify the opening, because a mill can remove a piece before all nine placements are done. Each player places nine pieces. `programs/TournamentAgent.py` takes the phase as an argument.

## Search contract

Implement both algorithms in `morris/search.py`. Signature:

```python
search(board, depth, *, phase, estimate) -> (best_board, positions_evaluated, value)
```

- `phase` is `"opening"` or `"midgame"`.
- `estimate` is the baseline function or an improved function. Pass it in. Do not duplicate the search for Part IV.
- White maximizes.
- `positions_evaluated` is the number of calls to `estimate`.
- At depth 0, call `estimate`.
- In the midgame, check the handout's terminal cases before generating moves: Black has 2 or fewer pieces (value `10000`), White has 2 or fewer (value `-10000`). The baseline estimator also returns `10000` when Black has no legal move.
- Alpha-beta must return the same board and the same value as minimax for the same position, depth, estimator, and tie-break. It should evaluate fewer positions. `Examples.txt` needs at least two such cases.

The command line is:

```bash
python programs/MiniMaxOpening.py <input.txt> <output.txt> <depth>
```

Stdout, including for the alpha-beta programs:

```
Board Position: <23 characters>
Positions evaluated by static estimation: <integer>
MINIMAX estimate: <integer>
```

The output file contains the same 23-character board.

## Part IV

`morris/improved.py` holds the new estimators. `deliverables/MyStaticEstimation.txt` explains:

1. which features are used,
2. why those features,
3. how they are combined,
4. why this is stronger than the handout estimator.

Include at least two boards where the improved move differs from the baseline move, and why the new move is preferred. These are section 5 of `MyStaticEstimation.txt` and Part IV of `Examples.txt`. The feature list in the project handout (piece difference, mobility, mills, blocked pieces, useful squares) is optional. The write-up has to give a game-playing reason for the features that are used.

After changing search or an estimator, run `python3 tools/verify_project.py --examples-only`. It rewrites `Examples.txt` from real program output and fails if `MyStaticEstimation.txt` quotes a move the programs no longer choose.

## Part V

`programs/TournamentAgent.py` is the match program. With no board arguments it runs the interactive console in `morris/tournament.py`; with board arguments it makes one move:

```bash
python programs/TournamentAgent.py
python programs/TournamentAgent.py <input> <output> <depth> <white|black> <opening|midgame>
```

It uses iterative deepening around alpha-beta with the improved estimator. Use --history from the start of a game, or --placements for opening analysis. A move must be a legal successor, for either color, in the correct phase, and the team has 4 minutes after the opponent's post.

## Checks before handing work back

```bash
python -m unittest discover -s tests
```

Extend the tests when search is implemented. Keep the required program filenames. Keep the three output lines exact.
