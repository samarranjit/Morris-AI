# Checklist

Do the steps in order. Later steps call the code from earlier ones. Check a box when that item runs, not when it is only sketched.

The entry scripts, argument parsing, and printed output are already wired. Almost all new code goes in `morris/search.py` and then `morris/improved.py`.

| When | What |
| --- | --- |
| 2026-10-08 | Schedule every official match. Submit the project ZIP. |
| 2026-10-15 | Finish every official game. |

Scheduling does not wait on the agent. Contact assigned opponents today even while search is still being written.

## 0. Foundation, already in the repo

- [x] Board, neighbors, and mills in `morris/board.py`. See [docs/board.md](docs/board.md).
- [x] White generators and Black-by-color-swap in `morris/moves.py`. See [docs/rules.md](docs/rules.md).
- [x] Handout static estimators in `morris/estimation.py`. Leave these functions as they are. Part IV adds a second pair in `morris/improved.py`.
- [x] Command-line programs. Each one calls `morris.cli.run`, which calls `minimax` or `alphabeta`.
- [x] `python3 -m unittest discover -s tests` passes.

Before writing search, run the empty-board command once so the stub message is familiar:

```bash
python3 programs/MiniMaxOpening.py examples/empty_board.txt out/board.txt 1
```

It exits with `Part I: implement minimax in morris/search.py`. After Step 1 that same command prints a board and writes `out/board.txt`.

## 1. Minimax for the opening

Part I, shared with Step 2. File: `morris/search.py`, function `minimax`. Program: `MiniMaxOpening.py`.

`minimax(board, depth, phase="opening", estimate=static_estimate_opening)` returns `(best_board, positions_evaluated, value)`.

- [ ] **1.1 White moves, then Black moves.** At a maximizing node, White moves with `generate_moves_opening`. At a minimizing node, Black moves with `generate_moves_opening_black`. White is always the maximizer in this function. Black programs swap colors before they call it.
- [ ] **1.2 Depth counts plies.** Depth 0 calls `estimate` and returns that number. Depth 1 generates White's moves and evaluates each child at depth 0. Depth 2 generates White's moves, then Black's replies, then evaluates the resulting boards. Each call to `estimate` adds 1 to `positions_evaluated`.
- [ ] **1.3 The root returns a board.** Deeper calls only need a value. The board in the return triple is the child of the root with the best value.
- [ ] **1.4 Ties keep the earliest move.** The generators already list moves from location 0 upward. At a max node, replace the best value only when the new value is strictly greater. At a min node, replace it only when the new value is strictly smaller. Alpha-beta in Step 3 must use this same rule, or the two programs can pick different moves.
- [ ] **1.5 Opening has no separate terminal test.** The opening score is White pieces minus Black pieces. A mill is already reflected, because the generator removed a piece before the position is scored.
- [ ] **1.6 Check depth 0.** On `examples/handout_position_1.txt` the estimate is `0` (five White, five Black) and the evaluation count is `1`. The returned board can be the input board, because no move is chosen.
- [ ] **1.7 Check depth 1 on an empty board.** `xxxxxxxxxxxxxxxxxxxxxxx` has 23 legal placements. The evaluation count is 23. Every child scores `1`. The kept move is the first generated one, a White piece on `a0`: `W` followed by 22 `x` characters. The estimate is `1`.
- [ ] **1.8 Run the program.**

```bash
mkdir -p out
python3 programs/MiniMaxOpening.py examples/empty_board.txt out/opening.txt 1
```

Stdout has these three lines, and `out/opening.txt` contains the same board:

```
Board Position: Wxxxxxxxxxxxxxxxxxxxxxx
Positions evaluated by static estimation: 23
MINIMAX estimate: 1
```

- [ ] **1.9 Depth 2 on a small board.** Start from a position with only a few empty squares so the tree stays readable. Hand-count White's moves, Black's replies, and the leaf scores. The printed estimate matches that count, and the printed board is one of White's legal opening moves.

`MiniMaxGame.py` still fails until Step 2. That is expected.

## 2. Minimax for the midgame and endgame

Same function, `phase="midgame"`. Program: `MiniMaxGame.py`. This finishes Part I (25%).

- [ ] **2.1 Switch generators by phase.** Midgame White moves come from `generate_moves_midgame_endgame`. Midgame Black moves come from `generate_moves_midgame_endgame_black`. Hopping is already inside those functions: a side with exactly three pieces hops.
- [ ] **2.2 Pass the midgame estimator.** `MiniMaxGame.py` already passes `static_estimate_midgame_endgame`. Use the `estimate` argument. Do not call the opening estimator from a midgame search.
- [ ] **2.3 Stop at a finished game before generating moves.** If Black has 2 or fewer pieces, the value is `10000`. If White has 2 or fewer, the value is `-10000`. If the side to move has no legal move, the value is `10000` when Black is stuck and `-10000` when White is stuck. Call `estimate` for these positions so they count toward `positions_evaluated`. The baseline function already returns those piece-count scores and returns `10000` when Black has no move.
- [ ] **2.4 Depth 0 matches the formula.** Pick a midgame board where both sides have at least three pieces. The printed estimate equals `1000 * (white - black) - black_moves`, and the evaluation count is `1`.
- [ ] **2.5 A capture is one move.** If the best move closes a mill, the output board has the new White placement or slide and one Black piece removed. Compare it with `generate_moves_midgame_endgame` so the string is a real successor.
- [ ] **2.6 Run both Part I programs** on an opening file and a midgame file at depth 1 and depth 2. Each run writes a 23-character file and prints the three lines.

## 3. Alpha-beta

Part II (20%). Function `alphabeta` in `morris/search.py`. Programs: `ABOpening.py`, `ABGame.py`.

Build this on Step 1 and Step 2. Same recursion, same generators, same estimator, same tie-break. Add an alpha-beta window.

- [ ] **3.1 Root window.** The root starts at alpha = negative infinity, beta = positive infinity.
- [ ] **3.2 Prune.** A max node raises alpha. A min node lowers beta. Stop expanding a node when alpha is greater than or equal to beta.
- [ ] **3.3 Same answer as minimax.** For several boards, both phases, and depths 1, 2, and 3, the board string and `MINIMAX estimate` match the minimax program. The evaluation count for alpha-beta is smaller on at least some of those boards. A depth-1 opening on an empty board may not prune, because every child scores `1`. Use a deeper search or a board where one early move is clearly better.
- [ ] **3.4 Save two cases for the write-up.** Record input board, depth, shared move, shared estimate, minimax evaluation count, and alpha-beta evaluation count. These go into `deliverables/Examples.txt` in Step 5.

```bash
python3 programs/MiniMaxOpening.py examples/handout_position_1.txt out/mm.txt 3
python3 programs/ABOpening.py examples/handout_position_1.txt out/ab.txt 3
```

`out/mm.txt` and `out/ab.txt` match. The alpha-beta count is the one that should drop.

## 4. Black

Part III (10%). The programs already swap colors around the White search in `morris/cli.py`. This step checks that swap once White search works.

- [ ] **4.1 Opening.** `MiniMaxOpeningBlack.py` on an empty board at depth 1 places a Black piece. The first generated square is `a0`, so the board is `B` plus 22 `x` characters. The estimate is the swapped White search value: placing one Black piece scores `1` for Black.
- [ ] **4.2 Swap is its own inverse.** Take a White move produced by `MiniMaxOpening.py`. Swap colors with `morris.board.swap_colors`, run `MiniMaxOpeningBlack.py` at the same depth, and swap the output back. You get the same move White chose.
- [ ] **4.3 Midgame.** `MiniMaxGameBlack.py` on a midgame board returns a board that `generate_moves_midgame_endgame_black` also produces.
- [ ] **4.4 Both colors, both phases.** Run all four minimax programs: opening White, opening Black, game White, game Black. Each writes a legal board.

## 5. Alpha-beta examples

Start `deliverables/Examples.txt` with the two cases saved in Step 3.4. The improved-move cases are added in Step 6.

- [ ] **5.1 Case 1** is filled in: board, depth, move, estimate, both evaluation counts. Alpha-beta's count is smaller.
- [ ] **5.2 Case 2** is a different board or depth, with the same fields, and alpha-beta again evaluates fewer positions.
- [ ] **5.3 Re-run both programs** and confirm the numbers in the file still match the output.

## 6. Improved static estimation

Part IV (20%). Depends on Steps 1 and 2 so you can compare moves. Alpha-beta is not required for this part. The improved programs call `minimax` with the new functions.

Edit `morris/improved.py` only. Keep `morris/estimation.py` unchanged.

- [ ] **6.1 Choose features and write down why** before coding. The handout's optional list is piece difference, number of moves, mobility, completed mills, possible next mills, blocked opponent pieces, and useful squares. Use the ones you can justify. The baseline opening score is only the piece difference, so a useful opening feature sees something that difference misses, such as a move that closes a mill or one that gives the opponent a mill.
- [ ] **6.2 Implement** `static_estimate_opening_improved` and `static_estimate_midgame_endgame_improved`. A higher number favors White. Include the same terminal results the baseline uses in the midgame: `10000` when Black has 2 or fewer pieces or no move, `-10000` when White has 2 or fewer.
- [ ] **6.3 Keep it fast.** The tournament allows 4 minutes, and this function runs at every leaf. Prefer counts over the board string to a second full search.
- [ ] **6.4 Find two disagreements.** Run `MiniMaxOpening.py` and `MiniMaxOpeningImproved.py` at the same depth, then the two game programs. Save two boards where the output boards differ.
- [ ] **6.5 For each disagreement,** say which move the baseline picked, which move the new function picked, and why the new move is better in the game.
- [ ] **6.6 Write `deliverables/MyStaticEstimation.txt`.** Cover four things: the features, why those features, how they are combined, and why the result is stronger than the handout estimator.
- [ ] **6.7 Add those two boards** to `deliverables/Examples.txt` under the improved-estimator section.

## 7. Tournament agent

Part V (25%). The grade is legal moves, both colors, both phases, the time limit, finished matches, and participation. Wins and losses are not the grade.

`programs/TournamentAgent.py` already calls alpha-beta and the improved estimator. Change that wiring in `main` if the team chooses minimax or the baseline estimator instead.

- [ ] **7.1 Pick the search and the depth** you can finish inside 4 minutes. Time a depth-2 and a depth-3 midgame move on a crowded board:

```bash
python3 programs/TournamentAgent.py examples/handout_position_2.txt out/move.txt 3 white midgame
```

- [ ] **7.2 Play a full practice game** against a teammate or a second copy of the agent. Track the move number. Moves 1 through 18 use `opening`. After both players have placed nine pieces, use `midgame`. Pass `white` or `black` for the side about to move.
- [ ] **7.3 Check every posted string** is 23 characters and is a legal successor of the previous one. `format_board` in `morris/board.py` prints a diagram when a string is hard to read.
- [ ] **7.4 Opening captures.** If a placement closes a mill, the posted board must also show the removed piece. The placement count still advances. Nine placements per player end the opening even if captures lowered the number of pieces on the board.
- [ ] **7.5 Endgame.** When the side to move has exactly three pieces, the move may hop to any empty square. When a side has two pieces, the game is over.
- [ ] **7.6 Draw rule.** If the same board with the same side to move appears three times, the game is a draw. Keep a list of `(board, side)` while you play.

## 8. Official matches

Details are in [docs/tournament.md](docs/tournament.md).

- [ ] **8.1 Schedule** each assigned opponent by 2026-10-08. If you cannot agree on a time, email the instructor.
- [ ] **8.2 Teams chat** with both full teams. One person per team posts the official boards.
- [ ] **8.3 Game 1.** The team listed first is White and posts move 1.
- [ ] **8.4 Game 2.** Colors swap. The other team is White.
- [ ] **8.5 Each reply** is posted within 4 minutes of the opponent's legal board. A late or illegal board can be claimed as a loss. A correction counts only before those 4 minutes end and before the opponent has answered.
- [ ] **8.6 Finish** both games by 2026-10-15.
- [ ] **8.7 Report one line** in the Canvas results document, using team ids and no spaces:

```
MATCH|T01|T07|A|B|2026-10-15
```

`A` means the first team won that game, `B` means the second team won, `D` means a draw. Game 1 is the first team as White. Game 2 is the second team as White. Practice games are not entered.

## 9. ZIP

- [ ] **9.1 Re-run the tests** and one command for each of the eight programs.
- [ ] **9.2 Read `deliverables/Examples.txt` and `deliverables/MyStaticEstimation.txt`** against the output you just produced.
- [ ] **9.3 Build one ZIP** containing:

```
MiniMaxOpening.py
MiniMaxGame.py
ABOpening.py
ABGame.py
MiniMaxOpeningBlack.py
MiniMaxGameBlack.py
MiniMaxOpeningImproved.py
MiniMaxGameImproved.py
TournamentAgent.py
morris/
Examples.txt
MyStaticEstimation.txt
```

Copy the nine scripts out of `programs/` into the ZIP root, and copy the two text files out of `deliverables/`. The programs import `morris`, so the package has to sit next to those scripts. Check Canvas for any extra instruction about folders before uploading.

- [ ] **9.4 From a clean unzip,** run `python3 MiniMaxOpening.py` on a sample board and confirm the three output lines. The file is at the ZIP root, which is the handout's command.
