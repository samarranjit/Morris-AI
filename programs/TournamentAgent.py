#!/usr/bin/env python3
"""Tournament driver.

The class plays by posting 23-character boards in Teams. This program
chooses the next board for one side. It is not a separate graded
algorithm: it should call the same minimax or alpha-beta search as the
other programs.

Usage:
    python programs/TournamentAgent.py <input> <output> <depth> <white|black> <opening|midgame>

Opening versus midgame cannot be recovered from the board alone.
Captures during placement change the piece counts, and each player
still places nine pieces. The person running the match passes the phase.
"""

from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_root = _here if (_here / "morris").is_dir() else _here.parent
sys.path.insert(0, str(_root))

from morris.cli import run


def main(argv: list[str]) -> int:
    if len(argv) != 6 or argv[4] not in {"white", "black"} or argv[5] not in {"opening", "midgame"}:
        print(
            "usage: python programs/TournamentAgent.py <input> <output> <depth> <white|black> <opening|midgame>",
            file=sys.stderr,
        )
        return 2
    program, input_path, output_path, depth, color, phase = argv
    return run(
        [program, input_path, output_path, depth],
        phase=phase,
        algorithm="alphabeta",
        color=color,
        estimation="improved",
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
