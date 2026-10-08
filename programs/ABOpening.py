#!/usr/bin/env python3
"""White's best opening move, alpha-beta, baseline estimator."""

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_root = _here if (_here / "morris").is_dir() else _here.parent
sys.path.insert(0, str(_root))

from morris.cli import run

if __name__ == "__main__":
    sys.exit(run(sys.argv, phase="opening", algorithm="alphabeta", color="white", estimation="baseline"))
