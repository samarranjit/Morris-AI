# Tournament

Each team is assigned at least three official opponents. Some teams get one extra opponent when the class size is uneven. The instructor publishes the matchup list. Only those matchups are official. Practice games are useful and are not reported.

The user reports a deadline extension. Confirm the new dates with the instructor; the dates below are the original PDF dates.

## Original schedule

- Agree on a time for every official match by 2026-10-08. If the teams cannot agree, contact the instructor, who may assign a time.
- Play every official game by 2026-10-15.

## How a match is played

The two teams open a Microsoft Teams group chat with everyone from both teams. That chat is the official record.

Each team picks one person to post that team's moves for a given game. Other members may help run the program. One poster avoids two different boards being submitted.

White posts first. Each post contains:

1. the move number,
2. the side that moved,
3. the 23-character board.

```
Move 7 - White
xxxWxxxxBxxWWxxxxBxxxxx
```

Moves 1 through 18 are the opening: nine placements each. After that, play is midgame and endgame.

## Time, illegal moves, results

After a legal board is posted, the opponent has 4 minutes, measured by the Teams timestamp. A late post may be claimed as a loss. The opponent may instead agree to restart. They do not have to.

An illegal board may be claimed as a loss. It may be corrected only before the 4 minutes end and before the opponent has answered. After the opponent answers, the move stands. Disputes go to the instructor with the saved chat.

A game is won under the Morris rules (opponent reduced to two pieces, or no legal move), by timeout, or by an uncorrected illegal move.

A draw is the same position with the same side to move, three times. Both teams point at that position in the chat.

Scoring per game: win 1, draw 0.5, loss 0. Standings use points divided by games played.

Each official pairing is two games.

- Game 1: Team A is White, Team B is Black.
- Game 2: Team B is White, Team A is Black.

## Reporting

After both games, one of the two teams adds one line to the shared results document on Canvas. Use the assigned ids (`T01`, `T02`, ...), with no spaces:

```
MATCH|TeamA|TeamB|Game1|Game2|YYYY-MM-DD
```

Result codes: `A` Team A won, `B` Team B won, `D` draw.

```
MATCH|T01|T07|A|B|2026-10-15
```

Team T01 won game 1 (T01 as White). Team T07 won game 2 (T07 as White).

```
MATCH|T03|T09|A|D|2026-10-17
```

Team T03 won game 1. Game 2 was a draw.

The Teams chat remains the record if a reported line is disputed.

## What the agent has to do during a match

- Produce a legal successor of the posted board.
- Play White or Black.
- Use opening moves for the first 18 placements, then midgame and endgame rules. Hopping starts when that side has three pieces.
- Search with minimax or alpha-beta.
- Return a board inside the 4-minute window. Depth is the team's choice.

## Running the agent: interactive console (use this for official games)

Run the tournament agent with no board arguments:

```bash
python3 programs/TournamentAgent.py
```

On macOS you can instead double-click `programs/Start-Tournament.command`.

Choose `new`, then `white` or `black`. Press Enter for a 180-second search budget and depth ceiling 12. Use 2 seconds for a quick practice session.

- White: the agent calculates immediately and prints your first Teams message.
- Black: the console waits for White's board before calculating your response.
- Paste a 23-character opponent board and press Enter. The two-line Teams post (`Move N - Color` followed by its board) is also accepted.
- An illegal board is rejected without advancing the game. Paste again.
- After a valid board, the agent searches and prints two lines to copy to Teams. Post them yourself; the console never posts online.

The console tracks phase changes, hopping, move numbers, and threefold repetition. It stops when the game ends. The saved state assumes you post the displayed move, so do not post a different board.

Commands while waiting for the opponent:

- `show`: display the current board and the last recorded move.
- `time 60`: give future searches 60 seconds instead of the current budget.
- `quit`: stop. Progress is already saved.

The opponent's Teams timestamp starts the four-minute window, and waiting to paste their move uses part of it. Lower the budget with `time N` when needed.

Depth 12 is a ceiling, not a promise to finish twelve plies. The agent searches depth 1, 2, 3, ... and keeps the last result that finished within the time budget. The default budget is 180 seconds. There is no maximum, but above 210 seconds the agent prints a warning: the 4 minutes start at the opponent's post, so pasting their move and posting yours both come out of the same window.

The search uses every CPU core by default. Use `--workers N` to choose how many processes; `--workers 1` searches in one process and picks the same move. If worker processes cannot start, the console says so and uses one process.

Every new game gets its own session JSON in `out/tournament-console/`, and the path is printed in Terminal. To resume, run the console and choose `resume`, or:

```bash
python3 programs/TournamentAgent.py --resume out/tournament-console/<session>.json
```

A move your team already calculated is shown again, not recalculated. If the opponent's move was saved but the search was interrupted, search restarts from that board. Ctrl+C or closing Terminal does not erase accepted moves.

## Running the agent: one move per command

The same program also makes a single move from a board file. Keep one history file per game. A session JSON from the console is not the same file as a `--history` array; keep using whichever one a game started with.

First move as White:

```bash
python3 programs/TournamentAgent.py examples/empty_board.txt out/move.txt 12 white opening --seconds 180 --history out/game1.json
```

Save the opponent's next board as `out/opponent.txt`, then run:

```bash
python3 programs/TournamentAgent.py out/opponent.txt out/move.txt 12 white opening --seconds 180 --history out/game1.json
```

For Black's first turn, save White's first posted board in the input file and use a new history filename with `black opening`. The runner infers the initial empty board and checks White's first placement. After the first 18 placements, use `midgame`. The search timer starts when the program runs, so reduce `--seconds` when part of the four minutes is already used.

Without history, give the placement count during the opening:

```bash
python3 programs/TournamentAgent.py examples/empty_board.txt out/move.txt 6 white opening --placements 0 --seconds 10
```

Without history, the program cannot validate the opponent's prior move or recognize earlier repetitions; track those manually. It never infers the opening phase from piece counts.

Only post an output after a successful exit (code 0). Diagnostics such as completed depth go to stderr. A failed command may leave an old output file in place; never mistake it for a new decision.

## Parallel search measurements

Measured on a 14-core Mac with `python3 tools/benchmark.py --seconds 20`. Depth finished inside 20 seconds. One worker is plain alpha-beta. Fourteen workers add move ordering, a transposition table, and reply splitting. At the same depth both choose the same move; a higher depth can choose a different one.

| Board | 1 worker | 14 workers |
| --- | --- | --- |
| Opening, empty board | depth 6 | depth 8 |
| Midgame, handout position 2 | depth 8 | depth 10 |
| Midgame, random position | depth 7 | depth 8 |

In the opening there are many first moves, so those are shared across cores. In the midgame there are few, so the opponent's replies are shared instead. Run the benchmark on the match machine before official games. On Linux the worker count follows the cores the job is allowed to use, which can be fewer than the machine has.
