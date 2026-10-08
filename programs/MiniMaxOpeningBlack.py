#!/usr/bin/env python3
"""Black's best opening move, minimax, baseline estimator.

The White search runs on a color-swapped board. The printed estimate is
the value of that swapped search, so a larger number favors Black.
"""

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_root = _here if (_here / "morris").is_dir() else _here.parent
sys.path.insert(0, str(_root))

from morris.cli import run

if __name__ == "__main__":
    sys.exit(run(sys.argv, phase="opening", algorithm="minimax", color="black", estimation="baseline"))
