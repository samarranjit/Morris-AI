"""Baseline static estimators from the Morris handout.

Opening: White pieces minus Black pieces.

Midgame and endgame, from White's point of view:
  10000  if Black has 2 or fewer pieces
  -10000 if White has 2 or fewer pieces
  10000  if Black has no legal midgame/endgame move
  otherwise 1000 * (White pieces - Black pieces) - Black's move count

The piece checks are in that order, so a position where both sides have
2 or fewer pieces scores 10000.
"""

from __future__ import annotations

from morris.board import BLACK, WHITE
from morris.moves import generate_moves_midgame_endgame_black

WIN = 10_000
LOSS = -10_000


def static_estimate_opening(board: str) -> int:
    return board.count(WHITE) - board.count(BLACK)


def static_estimate_midgame_endgame(board: str) -> int:
    white_pieces = board.count(WHITE)
    black_pieces = board.count(BLACK)
    if black_pieces <= 2:
        return WIN
    if white_pieces <= 2:
        return LOSS
    black_moves = generate_moves_midgame_endgame_black(board)
    if len(black_moves) == 0:
        return WIN
    return 1000 * (white_pieces - black_pieces) - len(black_moves)
