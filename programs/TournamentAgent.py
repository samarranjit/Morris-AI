#!/usr/bin/env python3
"""Tournament agent: interactive match console, or one timed move.

Interactive (recommended for official games):
    python3 TournamentAgent.py
    python3 TournamentAgent.py --resume out/tournament-console/<session>.json

One move from a board file:
    python3 TournamentAgent.py input output depth white|black opening|midgame --history game.json

Use --history match.json from the beginning of a game to validate opponent
moves, infer placements, and recognize threefold repetition. Nothing is posted
online: the designated communicator checks and posts the output board.
"""
import argparse
from pathlib import Path
import sys

_here = Path(__file__).resolve().parent
_root = _here if (_here / 'morris').is_dir() else _here.parent
sys.path.insert(0, str(_root))

from morris.io import read_board, write_board
from morris.tournament import (
    choose_move, load_history, next_state, phase_for, run_console, save_history,
)

_VALUE_OPTIONS = {'--seconds', '--placements', '--history', '--resume', '--depth'}


def _has_board_arguments(argv):
    skip = False
    for token in argv:
        if skip:
            skip = False
        elif token.startswith('-'):
            skip = token in _VALUE_OPTIONS
        else:
            return True
    return False


def console_main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--resume', type=Path, help='resume a console session JSON')
    parser.add_argument('--seconds', type=float, help='skip the search-budget question')
    parser.add_argument('--depth', type=int, help='skip the depth-ceiling question')
    args = parser.parse_args(argv)
    return run_console(args.resume, args.seconds, args.depth)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not _has_board_arguments(argv):
        return console_main(argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('depth', type=int, help='maximum search depth; completed iterations are retained')
    parser.add_argument('color', choices=['white', 'black'])
    parser.add_argument('phase', choices=['opening', 'midgame'])
    parser.add_argument('--seconds', type=float, default=180, help='search budget (0.01 to 210 seconds)')
    parser.add_argument('--placements', type=int, help='placements already made, both players combined (0..18)')
    parser.add_argument('--history', help='one JSON file per game, kept from the first move')
    args = parser.parse_args(argv)
    try:
        if not 0.01 <= args.seconds <= 210:
            raise ValueError('seconds must be between 0.01 and 210; reserve time for posting')
        paths = [Path(args.input).resolve(), Path(args.output).resolve()]
        if args.history:
            paths.append(Path(args.history).resolve())
        if len(set(paths)) != len(paths):
            raise ValueError('input, output, and history must be different files')
        board = read_board(args.input)
        history = load_history(args.history, board, args.color) if args.history else None
        placements = args.placements
        if history is not None:
            if placements is not None and placements != history[-1]['placements']:
                raise ValueError('placements disagree with history')
            placements = history[-1]['placements']
        elif placements is None:
            if args.phase == 'opening':
                raise ValueError('opening requires --placements or a --history file; piece counts cannot determine the phase')
            placements = 18
        if phase_for(placements) != args.phase:
            raise ValueError('phase disagrees with placement count')
        result = choose_move(board, args.color, placements, args.depth, args.seconds, history)
        write_board(args.output, result.board)
        if history is not None:
            history.append(next_state(history[-1], result.board))
            save_history(args.history, history)
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    print(f'Board Position: {result.board}')
    print(f'Positions evaluated by static estimation: {result.evaluated}')
    print(f'MINIMAX estimate: {result.value}')
    print(f'Completed depth: {result.completed_depth}; elapsed: {result.elapsed:.3f}s; '
          f'time budget reached: {result.timed_out}', file=sys.stderr)
    if result.completed_depth == 0:
        print('Fallback move: no search depth completed; estimate is a static fallback score.', file=sys.stderr)
    if history is None:
        print('No history supplied: repetition must be tracked manually.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
