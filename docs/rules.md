# Rules

Morris Game, Variant is a two-player board game. White and Black each have nine pieces. White moves first. The board has 23 intersections. The winner is the side that reduces the opponent to two pieces, or leaves the opponent with no legal move.

A draw is declared if the same board with the same player to move occurs three times.

## Phases

1. Opening. Players alternate placing one piece on any empty intersection. Each player places nine pieces. The first 18 placements are the opening, White placing on the odd moves of that sequence.
2. Midgame. A player moves one piece along a line to an adjacent empty intersection.
3. Endgame. A player who has only three pieces may hop to any empty intersection.

A mill formed during the opening removes a piece, so the number of pieces on the board can be lower than the number of placements so far. The phase follows the placement count, not the number of pieces still on the board.

## Mills

Three of one color on a straight line, including the four corner diagonals, close a mill. The mover then removes one opponent piece that is not in a mill. An isolated piece is a piece that is not part of a mill.

When every opponent piece is in a mill, any opponent piece may be removed. The handout's `GenerateRemove` ends with that case. The code in `morris/moves.py` removes one black piece in either case.

## Generators

The handout gives White generators. Black uses three steps: swap `W` and `B`, generate White moves, swap the results.

| Function | When |
| --- | --- |
| `GenerateAdd` | Opening. Put `W` on each empty square. |
| `GenerateMove` | Midgame. Slide `W` to an empty neighbor. |
| `GenerateHopping` | White has exactly three pieces. Move `W` to any empty square. |
| `GenerateRemove` | The placement or move just closed a mill. |
| `GenerateMovesOpening` | `GenerateAdd`. |
| `GenerateMovesMidgameEndgame` | Hopping at exactly three White pieces, otherwise `GenerateMove`. |

`neighbors` and `closeMill` are encoded directly from the diagram. The full lists are in [board.md](board.md) and `morris/board.py`.

## Baseline static estimation

Opening, for a position `b`:

```
numWhitePieces - numBlackPieces
```

Midgame and endgame:

```
numBlackMoves = number of positions from a Black midgame/endgame move

if numBlackPieces <= 2:  10000
else if numWhitePieces <= 2:  -10000
else if numBlackMoves == 0:  10000
else:  1000 * (numWhitePieces - numBlackPieces) - numBlackMoves
```

`numBlackMoves` counts generated positions, including the separate positions that come from different captures. These functions are in `morris/estimation.py`. The improved estimator is a separate pair of functions and does not replace these.
