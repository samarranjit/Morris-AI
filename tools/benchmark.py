#!/usr/bin/env python3
"""Compare tournament search depth for different worker counts on fixed boards.

    python3 tools/benchmark.py --seconds 20 --workers 1 14
"""
import argparse
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'programs'))

from TournamentAgent import choose_move_parallel, default_workers, shutdown_pool, start_pool
from morris.io import read_board
from morris.search import legal_moves
from morris.tournament import initial_state, next_state, phase_for


def random_midgame(seed):
    """A reproducible midgame position with White to move."""
    rng = random.Random(seed)
    while True:
        state = initial_state()
        while state['placements'] < 18 or state['side'] != 'white':
            moves = legal_moves(state['board'], phase_for(state['placements']), state['side'] == 'white')
            if not moves:
                break
            state = next_state(state, rng.choice(moves))
        else:
            if len(legal_moves(state['board'], 'midgame', True)) > 1:
                return state['board']
        seed += 1000
        rng = random.Random(seed)


def boards():
    yield 'opening, empty board', 'x' * 23, 0
    yield 'midgame, handout P2', read_board(ROOT / 'examples/handout_position_2.txt'), 18
    yield 'midgame, random', random_midgame(1), 18


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--depth', type=int, default=40)
    parser.add_argument('--workers', type=int, nargs='+', default=[1, default_workers()])
    args = parser.parse_args()
    try:
        for name, board, placements in boards():
            for workers in args.workers:
                if workers > 1:
                    start_pool(workers)
                decision = choose_move_parallel(board, 'white', placements, args.depth, args.seconds,
                                                workers=workers)
                rate = decision.evaluated / max(decision.elapsed, 1e-9)
                print(f'{name:22} workers={workers:<3} depth={decision.completed_depth:<3} '
                      f'evaluations={decision.evaluated:<10} {rate:>9.0f}/s  value={decision.value:<6} '
                      f'move={decision.board}', flush=True)
    finally:
        shutdown_pool()


if __name__ == '__main__':
    main()
