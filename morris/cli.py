"""Command-line entry used by the required program names.

    python programs/MiniMaxOpening.py board1.txt board2.txt 2

prints:

    Board Position: <23 characters>
    Positions evaluated by static estimation: <count>
    MINIMAX estimate: <integer>

and writes the chosen position to the output file. Alpha-beta programs
use the same three lines. The value is still the minimax estimate.
"""

from __future__ import annotations

import sys

from morris.board import swap_colors
from morris.estimation import static_estimate_midgame_endgame, static_estimate_opening
from morris.improved import (
    static_estimate_midgame_endgame_improved,
    static_estimate_opening_improved,
)
from morris.io import read_board, write_board
from morris.search import alphabeta, minimax

_ESTIMATORS = {
    ("opening", "baseline"): static_estimate_opening,
    ("midgame", "baseline"): static_estimate_midgame_endgame,
    ("opening", "improved"): static_estimate_opening_improved,
    ("midgame", "improved"): static_estimate_midgame_endgame_improved,
}


def run(argv: list[str], *, phase: str, algorithm: str, color: str, estimation: str) -> int:
    if len(argv) != 4:
        print(
            f"usage: python {argv[0] if argv else 'program.py'} <input board> <output board> <depth>",
            file=sys.stderr,
        )
        return 2
    _, input_path, output_path, depth_text = argv
    try:
        depth = int(depth_text)
        if depth < 0:
            raise ValueError
        board = read_board(input_path)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    search = minimax if algorithm == "minimax" else alphabeta
    estimate = _ESTIMATORS[(phase, estimation)]
    query = swap_colors(board) if color == "black" else board
    try:
        chosen, evaluated, value = search(query, depth, phase=phase, estimate=estimate)
    except NotImplementedError as exc:
        print(exc, file=sys.stderr)
        return 1

    if color == "black":
        chosen = swap_colors(chosen)
    write_board(output_path, chosen)
    print(f"Board Position: {chosen}")
    print(f"Positions evaluated by static estimation: {evaluated}")
    print(f"MINIMAX estimate: {value}")
    return 0
