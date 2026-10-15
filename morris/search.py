"""Readable minimax and alpha-beta over the same game tree.

The only difference is whether alpha-beta cutoffs are enabled. Keeping one
recursive implementation prevents the algorithms' rules from drifting apart.
White maximizes; Black minimizes. Ties keep the first generated move.
"""
from __future__ import annotations

from collections.abc import Callable
from math import inf
from time import monotonic

from morris.board import validate_board
from morris.moves import (
    generate_moves_opening, generate_moves_opening_black,
    generate_moves_midgame_endgame, generate_moves_midgame_endgame_black,
)

Estimator = Callable[[str], int]


class SearchTimeout(Exception):
    """A tournament search exceeded its internal time budget."""


def legal_moves(board: str, phase: str, white_turn: bool) -> list[str]:
    if phase == 'opening':
        if white_turn:
            return generate_moves_opening(board)
        return generate_moves_opening_black(board)
    if white_turn:
        return generate_moves_midgame_endgame(board)
    return generate_moves_midgame_endgame_black(board)


def minimax(board: str, depth: int, *, phase: str, estimate: Estimator) -> tuple[str, int, int]:
    """Return (immediate best successor, estimator calls, minimax value)."""
    return _search(board, depth, phase=phase, estimate=estimate, pruning=False)


def alphabeta(
    board: str, depth: int, *, phase: str, estimate: Estimator,
    deadline: float | None = None,
    placements: int | None = None,
    game_estimate: Estimator | None = None,
    repetitions: dict[tuple[str, bool], int] | None = None,
) -> tuple[str, int, int]:
    """Alpha-beta; optional match context is used only by the tournament.

    A deadline is an absolute time from time.monotonic(). Placements counts
    pieces already placed, not pieces surviving. Repetition keys use this
    search's color perspective: True means White is to move.
    """
    return _search(
        board, depth, phase=phase, estimate=estimate, pruning=True,
        deadline=deadline, placements=placements, game_estimate=game_estimate,
        repetitions=repetitions,
    )


def _search(
    board, depth, *, phase, estimate, pruning,
    deadline=None, placements=None, game_estimate=None, repetitions=None,
):
    board = validate_board(board)
    if depth < 0:
        raise ValueError('depth must be nonnegative')
    if phase not in ('opening', 'midgame'):
        raise ValueError('phase must be opening or midgame')
    if placements is not None:
        if not 0 <= placements <= 18:
            raise ValueError('placements must be between 0 and 18')
        if (placements < 18) != (phase == 'opening'):
            raise ValueError('phase disagrees with placements')
        if placements < 18 and game_estimate is None:
            raise ValueError('phase-aware search needs a midgame estimator')

    evaluated = 0
    # Copy once, then increment and restore along each search path.
    counts = dict(repetitions or {})
    track_draws = repetitions is not None

    def leaf(position, current_phase, forced_value=None):
        nonlocal evaluated
        evaluator = estimate
        if current_phase == 'midgame' and game_estimate is not None:
            evaluator = game_estimate
        value = evaluator(position)
        evaluated += 1
        # The baseline is intentionally asymmetric. Game-ending rules must
        # still recognize a blocked White player and a threefold draw.
        if forced_value is not None:
            value = forced_value
        return position, value

    def visit(position, remaining, white_turn, placed, alpha, beta):
        if deadline is not None and monotonic() >= deadline:
            raise SearchTimeout()
        current_phase = phase
        if placed is not None:
            current_phase = 'opening' if placed < 18 else 'midgame'

        if current_phase == 'midgame':
            if position.count('B') <= 2:
                return leaf(position, current_phase, 10000)
            if position.count('W') <= 2:
                return leaf(position, current_phase, -10000)
        if track_draws and counts.get((position, white_turn), 0) >= 3:
            return leaf(position, current_phase, 0)

        moves = None
        if current_phase == 'midgame':
            moves = legal_moves(position, current_phase, white_turn)
            if not moves:
                return leaf(position, current_phase, -10000 if white_turn else 10000)
        if remaining == 0:
            return leaf(position, current_phase)
        if moves is None:
            moves = legal_moves(position, current_phase, white_turn)
        if not moves:
            # Defensive behavior for a full opening input board.
            return leaf(position, current_phase)

        best_board = moves[0]
        best_value = -inf if white_turn else inf
        next_placed = placed
        if placed is not None and placed < 18:
            next_placed = placed + 1

        for child in moves:
            key = (child, not white_turn)
            if track_draws:
                counts[key] = counts.get(key, 0) + 1
            try:
                _, child_value = visit(child, remaining - 1, not white_turn, next_placed, alpha, beta)
            finally:
                if track_draws:
                    counts[key] -= 1

            if white_turn:
                if child_value > best_value:
                    best_board, best_value = child, child_value
                alpha = max(alpha, best_value)
            else:
                if child_value < best_value:
                    best_board, best_value = child, child_value
                beta = min(beta, best_value)
            if pruning and alpha >= beta:
                break  # Remaining siblings cannot improve this decision.

        return best_board, best_value

    chosen, value = visit(board, depth, True, placements, -inf, inf)
    return chosen, evaluated, int(value)
