# Morris AI Tournament

CS4346 team project. The agent plays the Morris Game, Variant with minimax and alpha-beta, then a static estimator the team designs. Official games are played in Microsoft Teams by posting 23-character board strings.

The instructor handouts are `docs/Project.pdf` and `docs/Morris-Variant.pdf`. The markdown files under `docs/` are working notes taken from those PDFs. Where a note and a PDF disagree, the PDF is the assignment.

The working list is [CHECKLIST.md](CHECKLIST.md). Do those steps in order. Each one builds on the previous step.

## Deadlines

| Item | Date |
| --- | --- |
| Team size | 3 students |
| Schedule official matches | 2026-10-08 |
| Submit the project ZIP | 2026-10-08 |
| Finish official games | 2026-10-15 |

## Layout

`programs/` holds the nine required entry points. `morris/` holds the game code. Run commands from the repository root.

The handout shows `python MiniMaxOpening.py`. In this repo the same file is `programs/MiniMaxOpening.py`. For the ZIP, copy those nine files to the archive root. Each script finds `morris/` either beside itself or one directory up, so both layouts run.

```
programs/MiniMaxOpening.py         White, minimax, opening, baseline estimator
programs/MiniMaxGame.py            White, minimax, midgame/endgame, baseline
programs/ABOpening.py              White, alpha-beta, opening, baseline
programs/ABGame.py                 White, alpha-beta, midgame/endgame, baseline
programs/MiniMaxOpeningBlack.py    Black, minimax, opening, baseline
programs/MiniMaxGameBlack.py       Black, minimax, midgame/endgame, baseline
programs/MiniMaxOpeningImproved.py White, minimax, opening, improved estimator
programs/MiniMaxGameImproved.py    White, minimax, midgame/endgame, improved
programs/TournamentAgent.py        either color, either phase, for match play

morris/board.py                    23 locations, neighbors, mills
morris/moves.py                    move generators
morris/estimation.py               handout static estimators
morris/improved.py                 Part IV estimators
morris/search.py                   minimax and alpha-beta
morris/io.py                       board files
morris/cli.py                      argument parsing and the three output lines

examples/                          boards, including the two handout positions
deliverables/                      Examples.txt and MyStaticEstimation.txt
docs/                              handouts and notes
tests/test_handout.py              checks against the handout
CHECKLIST.md                       stepwise task list
```

## What is already in place

The handout specifies the board, the White move generators, the color-swap method for Black, and the baseline static estimators. Those are implemented and covered by `tests/test_handout.py`.

What is left is tracked in [CHECKLIST.md](CHECKLIST.md): minimax, alpha-beta, a check of the Black programs, the improved estimator and its write-up, the tournament agent, the matches, and the ZIP.

## Commands

From the repository root. The handout writes `python`. On this machine the interpreter is `python3`.

```bash
python3 -m unittest discover -s tests
python3 programs/MiniMaxOpening.py examples/empty_board.txt out/board.txt 2
python3 programs/TournamentAgent.py examples/empty_board.txt out/board.txt 3 white opening
```

A program prints three lines and writes the chosen board to the output file:

```
Board Position: xxxxxxxxxxxxxxxxxxxxxxx
Positions evaluated by static estimation: 0
MINIMAX estimate: 0
```

`Positions evaluated by static estimation` counts calls to the estimator. Alpha-beta prints the same label. The number on the third line is the minimax value.

## Submission ZIP

One ZIP per team. Put these files in it:

1. `MiniMaxOpening.py`
2. `MiniMaxGame.py`
3. `ABOpening.py`
4. `ABGame.py`
5. `MiniMaxOpeningBlack.py`
6. `MiniMaxGameBlack.py`
7. `MiniMaxOpeningImproved.py`
8. `MiniMaxGameImproved.py`
9. `Examples.txt`
10. `MyStaticEstimation.txt`
11. `TournamentAgent.py`, since this repo keeps a separate tournament program

Copy the nine scripts out of `programs/` into the ZIP root, and copy `Examples.txt` and `MyStaticEstimation.txt` out of `deliverables/`. The ZIP also needs the `morris/` directory next to those scripts. Confirm that layout against the Canvas submission notes before uploading.

## Reading order

1. [CHECKLIST.md](CHECKLIST.md) for the next step to do.
2. [docs/rules.md](docs/rules.md) for phases, mills, and generators.
3. [docs/board.md](docs/board.md) for the 23 indexes.
4. [docs/programs.md](docs/programs.md) for parts, output, and grading.
5. [docs/tournament.md](docs/tournament.md) for match protocol.
