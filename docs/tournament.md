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

Use `--history game.json` from the first turn to validate opponent boards and track placements/repetition. Use a new file per game. See README.md for commands and timing margins.
