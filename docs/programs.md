# Programs and grading

Each required program reads an input board file, a output board file, and a depth:

```bash
python programs/MiniMaxOpening.py board1.txt board2.txt 2
```

The handout writes `python MiniMaxOpening.py`. That is the same file. This repo keeps it in `programs/`. The submission ZIP places a copy at the archive root, which is the handout's command.

It writes the chosen 23-character position to the output file and prints:

```
Board Position: ...
Positions evaluated by static estimation: ...
MINIMAX estimate: ...
```

Alpha-beta uses those same three lines. For the same position and depth, minimax and alpha-beta return the same estimate and the same move when they share a tie-break. The difference is the number of positions the estimator sees. The examples need at least two positions where alpha-beta evaluates fewer positions.

| Program | Search | Side | Phase | Estimator |
| --- | --- | --- | --- | --- |
| `MiniMaxOpening.py` | minimax | White | opening | baseline |
| `MiniMaxGame.py` | minimax | White | midgame/endgame | baseline |
| `ABOpening.py` | alpha-beta | White | opening | baseline |
| `ABGame.py` | alpha-beta | White | midgame/endgame | baseline |
| `MiniMaxOpeningBlack.py` | minimax | Black | opening | baseline |
| `MiniMaxGameBlack.py` | minimax | Black | midgame/endgame | baseline |
| `MiniMaxOpeningImproved.py` | minimax | White | opening | improved |
| `MiniMaxGameImproved.py` | minimax | White | midgame/endgame | improved |
| `TournamentAgent.py` | team choice | either | either | team choice |

Black programs may use the color-swap method in the Morris handout. This repo does: swap the input, run the White search, swap the chosen board back. The printed estimate is the swapped search value, so a higher number favors Black.

`TournamentAgent.py` is optional in the ZIP only if the team folds everything into the other programs. This repo keeps it as its own file. It has two modes:

```bash
python programs/TournamentAgent.py
python programs/TournamentAgent.py <input> <output> <depth> <white|black> <opening|midgame> --history <game.json>
```

With no board arguments it opens the interactive match console used for official games. With board arguments it makes one timed move. See [tournament.md](tournament.md).

## Parts

| Part | Weight | Work |
| --- | --- | --- |
| I. Minimax | 25% | `MiniMaxOpening.py`, `MiniMaxGame.py` |
| II. Alpha-beta | 20% | `ABOpening.py`, `ABGame.py` |
| III. Playing Black | 10% | `MiniMaxOpeningBlack.py`, `MiniMaxGameBlack.py` |
| IV. Improved static estimation | 20% | the two `Improved` programs and `MyStaticEstimation.txt` |
| V. Tournament agent and participation | 25% | legal moves, both colors, both phases, time limit, completed matches |
| Total | 100% |  |

Tournament wins and losses are not the grade. Part V is graded on legal moves, playing both colors, finishing assigned games, following the time limit and protocol, and team participation. All three teammates normally receive the same grade. A participation problem should be raised with the instructor early.

`Examples.txt` has to include at least two positions where alpha-beta evaluates fewer positions than minimax. Ours also repeats the two Part IV boards with full program output.

`MyStaticEstimation.txt` has to cover the features, why they were chosen, how they are combined, and why the result is stronger than the handout estimator, plus at least two boards where the improved estimator chooses a different move, with a short reason for preferring it.

Both files are written in `deliverables/`. The Submission section below maps each requirement to the section that answers it.

## Submission

One ZIP per team. Build it with:

```bash
python3 tools/build_submission.py
```

It writes `dist/Morris-AI-submission.zip` with the nine programs at the archive root, the `morris/` package beside them, `Examples.txt`, and `MyStaticEstimation.txt`. It then extracts the archive in a clean folder and runs all nine programs there. The programs need `morris/` next to them.

Where each written requirement is answered:

| Handout requirement | Answered in |
| --- | --- |
| Part II: at least two cases where alpha-beta evaluates fewer positions than minimax | `Examples.txt`, Part II |
| Part IV: features used by the improved estimator | `MyStaticEstimation.txt`, section 1 |
| Part IV: why those features were selected | `MyStaticEstimation.txt`, section 2 |
| Part IV: how they are combined | `MyStaticEstimation.txt`, section 3 |
| Part IV: why it is better than the original estimator | `MyStaticEstimation.txt`, section 4 |
| Part IV: two boards where the improved estimator picks a different move, and why | `MyStaticEstimation.txt`, section 5, and `Examples.txt`, Part IV |

`Examples.txt` is generated from real runs of the submitted programs. Regenerate it after any change to search or the estimators:

```bash
python3 tools/verify_project.py --examples-only
```

That command fails if `MyStaticEstimation.txt` quotes a move the programs no longer choose. Section 5 of that file is written by hand, so update it when that happens. Without `--examples-only`, the script also regenerates `Validation.txt` and `validation.json` (timings and local games). Those two files are evidence for the team and are not submitted.

## Development notes from the project handout

The team designs, implements, tests, and debugs the programs. Tools are allowed under course and university policy. The submitted code still has to implement the class algorithms, and the team has to be able to explain it.

Teammates may discuss the algorithms, write prompts together, test, debug, design the estimator, and run the tournament agent. Discussion of general ideas with other teams is fine. Source code, complete prompts, implementation-specific solutions, and the improved estimator stay inside the team.
