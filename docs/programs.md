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

`TournamentAgent.py` is optional in the ZIP only if the team folds everything into the other programs. This repo keeps it as its own file. Suggested call:

```bash
python programs/TournamentAgent.py <input> <output> <depth> <white|black> <opening|midgame>
```

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

`Examples.txt` has to include:

- at least two positions where alpha-beta evaluates fewer nodes than minimax,
- at least two positions where the improved estimator chooses a different move than the baseline, with a short reason for preferring the new move.

`MyStaticEstimation.txt` has to cover the features, why they were chosen, how they are combined, and why the result is stronger than the handout estimator.

## Development notes from the project handout

The team designs, implements, tests, and debugs the programs. Tools are allowed under course and university policy. The submitted code still has to implement the class algorithms, and the team has to be able to explain it.

Teammates may discuss the algorithms, write prompts together, test, debug, design the estimator, and run the tournament agent. Discussion of general ideas with other teams is fine. Source code, complete prompts, implementation-specific solutions, and the improved estimator stay inside the team.
