"""Minimax and alpha-beta.

Parts I and II are implemented here. Both algorithms must share the
move generators and, on equal values, keep the earliest move in the
generator list. That is what makes them return the same move.

`positions_evaluated` counts calls to the static estimator, which is
the number the programs print.

Suggested shape of each search:

- White is the maximizing player. Black moves are generated with the
  color-swap helpers in morris.moves.
- At depth 0, call the estimator and count that call.
- In the midgame/endgame, a side reduced to 2 or fewer pieces has
  already lost. Check that before generating moves so a player with
  two pieces is not given another turn.
- Opening search uses generate_moves_opening. Midgame/endgame search
  uses generate_moves_midgame_endgame. Pass the improved estimators
  in for Part IV; do not copy the search.
"""

from __future__ import annotations

from collections.abc import Callable

Estimator = Callable[[str], int]


def minimax(
    board: str,
    depth: int,
    *,
    phase: str,
    estimate: Estimator,
) -> tuple[str, int, int]:
    """Return (best board for White, positions evaluated, minimax estimate)."""
    raise NotImplementedError("Part I: implement minimax in morris/search.py")


def alphabeta(
    board: str,
    depth: int,
    *,
    phase: str,
    estimate: Estimator,
) -> tuple[str, int, int]:
    """Return (best board for White, positions evaluated, minimax estimate)."""
    raise NotImplementedError("Part II: implement alpha-beta in morris/search.py")
