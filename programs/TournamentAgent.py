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

--workers N splits the search over N processes (default: every CPU core).
--workers 1 searches in a single process; the chosen move is the same.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from functools import partial
import math
from math import inf
import multiprocessing
import os
from pathlib import Path
import signal
import sys
from time import monotonic

_here = Path(__file__).resolve().parent
_root = _here if (_here / 'morris').is_dir() else _here.parent
sys.path.insert(0, str(_root))

from morris import tournament
from morris.board import swap_colors
from morris.improved import static_estimate_opening_improved, static_estimate_midgame_endgame_improved
from morris.io import read_board, write_board
from morris.search import legal_moves, SearchTimeout
from morris.tournament import (
    Decision, choose_move, load_history, next_state, phase_for, run_console, save_history, time_warning,
)

_VALUE_OPTIONS = {'--seconds', '--placements', '--history', '--resume', '--depth', '--workers'}


# Parallel alpha-beta. Workers share the best root score, and when a position has
# fewer root moves than cores the opponent's replies are split across workers too.
# Inside each worker, captures, killer moves, the history heuristic, and a
# transposition table make cutoffs happen sooner. The table is used for a cutoff
# only when it was stored at the same depth, so the value stays equal to plain
# alpha-beta; a saved move from any depth is still tried first.
# The chosen board and value equal morris.tournament.choose_move at the same
# depth, including the first-generated tie-break.

NO_BOUND = -1  # Depth slot value meaning no root move has finished at this depth yet.
_HUGE = 10 ** 15  # Shared beta meaning "no extra cutoff".
_TT_CAP = 1_000_000
EXACT, LOWER, UPPER = 0, 1, 2

_pool = None
_pool_workers = 0
_pool_shared = None
_shared = None  # [depth, best root value, best root index, split beta, split epoch].
_buf = None
_tt = {}
_killers = {}
_history = {}


class _Pruned(Exception):
    """A split reply can no longer change its root move's result."""


def default_workers():
    """Cores this process may use. On Linux a job can be limited below the machine size."""
    affinity = getattr(os, 'sched_getaffinity', None)
    if affinity is not None:
        allowed = affinity(0)
        if allowed:
            return len(allowed)
    return os.cpu_count() or 1


def _leaf(position, placed, tally, forced=None):
    if placed < 18:
        value = static_estimate_opening_improved(position)
    else:
        value = static_estimate_midgame_endgame_improved(position)
    tally[0] += 1
    return value if forced is None else forced


def _fnv(position, side, count):
    h = 0xCBF29CE484222325
    for character in position:
        h ^= ord(character)
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    h ^= (0x100 + count) if side else count
    return (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF


def _signature(counts):
    sig = 0
    if counts:
        for (position, side), count in counts.items():
            if count:
                sig ^= _fnv(position, side, count)
    return sig


def _bump(sig, position, side, old, new):
    if old:
        sig ^= _fnv(position, side, old)
    if new:
        sig ^= _fnv(position, side, new)
    return sig


def _store(key, depth, flag, value, move):
    if value == inf or value == -inf:
        return
    current = _tt.get(key)
    if current is not None and current[0] > depth:
        return
    if current is None and len(_tt) >= _TT_CAP:
        return
    _tt[key] = (depth, flag, int(value), move)


def _note_cutoff(ply, white_turn, move, remaining):
    if len(_history) > 200_000:
        _history.clear()
    _history[(white_turn, move)] = _history.get((white_turn, move), 0) + remaining * remaining
    pair = _killers.get(ply)
    if pair is None:
        _killers[ply] = [move, None]
    elif pair[0] != move:
        pair[1] = pair[0]
        pair[0] = move


def _order(moves, position, white_turn, ply, tt_move):
    if len(moves) < 2:
        return moves
    opponent = 'B' if white_turn else 'W'
    opponent_count = position.count(opponent)
    killers = _killers.get(ply)
    history = _history

    def rank(move):
        if move == tt_move:
            return 4_000_000_000
        if move.count(opponent) < opponent_count:
            return 3_000_000_000
        if killers:
            if move == killers[0]:
                return 2_000_000_000
            if move == killers[1]:
                return 1_000_000_000
        return history.get((white_turn, move), 0)

    return sorted(moves, key=rank, reverse=True)


def _alphabeta(position, remaining, white_turn, placed, alpha, beta, deadline, counts, tally,
               sig=0, ply=0, follow_beta=False, epoch=0):
    """Alpha-beta with the same rules and value as morris.search.

    Move order differs: captures, killer moves, history, and a saved best move
    go first. A value outside (alpha, beta) is only a bound. counts maps
    (board, white to move) to occurrences, or is None. sig is the running
    hash of those counts, so a repeated position is never confused with one
    that was not repeated.
    """
    if deadline is not None and monotonic() >= deadline:
        raise SearchTimeout()
    if follow_beta:
        live = _buf[3]
        if live < beta:
            beta = live
        if alpha >= beta or _buf[4] != epoch:
            raise _Pruned()
    midgame = placed >= 18
    if midgame:
        if position.count('B') <= 2:
            return _leaf(position, placed, tally, 10000)
        if position.count('W') <= 2:
            return _leaf(position, placed, tally, -10000)
    if counts is not None and counts.get((position, white_turn), 0) >= 3:
        return _leaf(position, placed, tally, 0)
    key = (position, white_turn, placed, sig)
    entry = _tt.get(key)
    if entry is not None and entry[0] == remaining:
        flag, value = entry[1], entry[2]
        if flag == EXACT or (flag == LOWER and value >= beta) or (flag == UPPER and value <= alpha):
            return value
    moves = None
    if midgame:
        moves = legal_moves(position, 'midgame', white_turn)
        if not moves:
            return _leaf(position, placed, tally, -10000 if white_turn else 10000)
    if remaining == 0:
        return _leaf(position, placed, tally)
    if moves is None:
        moves = legal_moves(position, 'opening', white_turn)
    if not moves:
        return _leaf(position, placed, tally)

    moves = _order(moves, position, white_turn, ply, entry[3] if entry else None)
    best = -inf if white_turn else inf
    best_move = None
    next_placed = placed + 1 if placed < 18 else placed
    cutoff = False
    for child in moves:
        child_key = (child, not white_turn)
        old = 0
        if counts is not None:
            old = counts.get(child_key, 0)
            counts[child_key] = old + 1
        child_sig = _bump(sig, child, not white_turn, old, old + 1) if counts is not None else sig
        try:
            value = _alphabeta(child, remaining - 1, not white_turn, next_placed,
                               alpha, beta, deadline, counts, tally, child_sig, ply + 1,
                               follow_beta, epoch)
        finally:
            if counts is not None:
                if old:
                    counts[child_key] = old
                else:
                    del counts[child_key]
        if white_turn:
            if value > best:
                best, best_move = value, child
            alpha = max(alpha, best)
        else:
            if value < best:
                best, best_move = value, child
            beta = min(beta, best)
        if alpha >= beta:
            _note_cutoff(ply, white_turn, child, remaining)
            cutoff = True
            break
    flag = (LOWER if white_turn else UPPER) if cutoff else EXACT
    _store(key, remaining, flag, best, best_move)
    return best


def _init_worker(shared):
    global _shared, _buf, _tt, _killers, _history
    _shared = shared
    _buf = shared.get_obj()  # Raw array: the beta and epoch are read at every node, without the lock.
    _tt = {}
    _killers = {}
    _history = {}
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ctrl+C is handled by the parent.


def _ready():
    return os.getpid()


def _get_pool(workers):
    global _pool, _pool_workers, _pool_shared
    if _pool is None or _pool_workers != workers:
        shutdown_pool()
        # spawn behaves the same on macOS, Linux, and Windows.
        context = multiprocessing.get_context('spawn')
        _pool_shared = context.Array('q', [NO_BOUND, 0, 0, _HUGE, 0])
        _pool = ProcessPoolExecutor(workers, mp_context=context,
                                    initializer=_init_worker, initargs=(_pool_shared,))
        _pool_workers = workers
    return _pool, _pool_shared


def start_pool(workers):
    """Start every worker now, so the first timed search does not pay for it."""
    pool, _ = _get_pool(workers)
    for future in [pool.submit(_ready) for _ in range(workers)]:
        future.result()


def shutdown_pool():
    """Stop the workers immediately. A search they were running is discarded."""
    global _pool, _pool_workers
    pool, _pool, _pool_workers = _pool, None, 0
    if pool is None:
        return
    terminate = getattr(pool, 'terminate_workers', None)  # Python 3.14+
    if terminate is not None:
        try:
            terminate()
            return
        except Exception:
            pass
    for process in list((getattr(pool, '_processes', None) or {}).values()):
        process.terminate()
    pool.shutdown(wait=False, cancel_futures=True)


def _search_root_move(depth, index, child, placements, deadline, counts):
    """Search one root move in a worker. Returns (index, value, exact, evaluated)."""
    with _shared.get_lock():
        bound_depth, best, best_index = _shared[:3]
    alpha = -inf
    if bound_depth == depth:
        # An earlier root move must strictly beat best - 1 to be rejected, so a
        # tie still goes to the first generated move. Values are integers.
        alpha = best if index > best_index else best - 1
    tally = [0]
    try:
        value = _alphabeta(child, depth - 1, False, min(18, placements + 1),
                           alpha, inf, deadline, counts, tally, _signature(counts))
    except SearchTimeout:
        return index, None, False, tally[0]
    value = int(value)
    exact = value > alpha
    if exact:
        with _shared.get_lock():
            if _shared[0] != depth or value > _shared[1] or (value == _shared[1] and index < _shared[2]):
                _shared[0], _shared[1], _shared[2] = depth, value, index
    return index, value, exact, tally[0]


def _search_reply(depth, reply, placed, deadline, counts, alpha, beta, epoch):
    """Search one opponent reply in a worker. Returns (value or 'pruned' or None, evaluated)."""
    tally = [0]
    try:
        value = _alphabeta(reply, depth - 2, True, placed, alpha, beta, deadline, counts, tally,
                           _signature(counts), 0, True, epoch)
    except SearchTimeout:
        return None, tally[0]
    except _Pruned:
        return 'pruned', tally[0]
    return int(value), tally[0]


def _reply_count(child, placements):
    placed = min(18, placements + 1)
    phase = 'opening' if placed < 18 else 'midgame'
    return len(legal_moves(child, phase, False))


def _search_split_move(depth, child, placements, deadline, repetitions, alpha):
    """Split one root move across the opponent's replies.

    Returns (value, exact, evaluated), or None when the move is too small to split.
    The first reply is searched alone so its score cuts the others, and a shared
    beta tightens as replies finish. Raising the epoch stops replies that are
    already running once they can no longer change the result.
    """
    placed = min(18, placements + 1)
    phase = 'opening' if placed < 18 else 'midgame'
    replies = legal_moves(child, phase, False)
    if len(replies) < 4 or depth < 5:
        return None
    opponent = 'W'  # Black is to move and would capture a white piece.
    opponent_count = child.count(opponent)
    replies = sorted(replies, key=lambda move: move.count(opponent) < opponent_count, reverse=True)
    reply_placed = placed + 1 if placed < 18 else placed
    base = None
    if repetitions is not None:
        base = dict(repetitions)
        key = (child, False)
        base[key] = base.get(key, 0) + 1

    def counts_for(reply):
        if base is None:
            return None
        counts = dict(base)
        key = (reply, True)
        counts[key] = counts.get(key, 0) + 1
        return counts

    pool, shared = _get_pool(_pool_workers)
    buf = shared.get_obj()
    epoch = buf[4] + 1
    buf[4] = epoch
    buf[3] = _HUGE
    evaluated = 0
    futures = []
    try:
        first = pool.submit(_search_reply, depth, replies[0], reply_placed, deadline,
                            counts_for(replies[0]), alpha, inf, epoch)
        value, count = first.result()
        evaluated += count
        if value is None:
            raise SearchTimeout()
        if value == 'pruned' or value <= alpha:
            buf[4] = epoch + 1
            return value if value != 'pruned' else alpha, False, evaluated
        best = value
        buf[3] = best
        for reply in replies[1:]:
            futures.append(pool.submit(_search_reply, depth, reply, reply_placed, deadline,
                                       counts_for(reply), alpha, best, epoch))
        for future in as_completed(futures):
            value, count = future.result()
            evaluated += count
            if value is None:
                raise SearchTimeout()
            if value == 'pruned':
                continue
            if value <= alpha:
                buf[4] = epoch + 1
                return value, False, evaluated
            if value < best:
                best = value
                buf[3] = best
    except BaseException:
        buf[4] = epoch + 1
        for future in futures:
            future.cancel()
        raise
    finally:
        buf[3] = _HUGE
    return best, best > alpha, evaluated


def search_root(board, moves, depth, placements, deadline, repetitions, workers, order=None):
    """Alpha-beta at one depth with the root moves split across processes.

    board has White to move; moves is legal_moves(board, phase, True) in
    generator order. order lists move indices, most promising first.
    Returns ((best_board, evaluations, value), order for the next depth).
    Raises SearchTimeout if the deadline stops any root move.
    """
    if depth < 2:
        raise ValueError('parallel search needs depth >= 2')
    pool, shared = _get_pool(workers)
    with shared.get_lock():
        shared[0] = NO_BOUND
    futures = []
    results = {}
    evaluated = 0

    def submit(index):
        counts = None
        if repetitions is not None:
            counts = dict(repetitions)
            key = (moves[index], False)
            counts[key] = counts.get(key, 0) + 1
        future = pool.submit(_search_root_move, depth, index, moves[index], placements, deadline, counts)
        futures.append(future)
        return future

    def collect(future):
        nonlocal evaluated
        index, value, exact, count = future.result()
        evaluated += count
        if value is None:
            raise SearchTimeout()
        results[index] = (value, exact)

    def alpha_for(index):
        with shared.get_lock():
            bound_depth, best, best_index = shared[0], shared[1], shared[2]
        if bound_depth != depth:
            return -inf
        # An earlier generated move wins a tie, so it is allowed to match best.
        return best if index > best_index else best - 1

    def record(index, value, exact, count):
        nonlocal evaluated
        evaluated += count
        if value is None:
            raise SearchTimeout()
        results[index] = (value, exact)
        if exact:
            with shared.get_lock():
                if shared[0] != depth or value > shared[1] or (value == shared[1] and index < shared[2]):
                    shared[0], shared[1], shared[2] = depth, value, index

    def search_one(index):
        """Split this move's replies when there are enough of them; otherwise one worker."""
        if depth >= 5 and workers >= 2 and _reply_count(moves[index], placements) >= 4:
            result = _search_split_move(depth, moves[index], placements, deadline,
                                        repetitions, alpha_for(index))
            if result is not None:
                return result
        index, value, exact, count = submit(index).result()
        return value, exact, count

    try:
        indices = list(order if order is not None else range(len(moves)))
        # Few root moves (typical of the midgame): search them one at a time and
        # give every core some of the opponent's replies. Many root moves (the
        # opening): split only the first move, which used to run on one core, then
        # search the other root moves all at once.
        if (depth >= 5 and workers >= 2 and len(indices) <= 12
                and _reply_count(moves[indices[0]], placements) >= 4):
            for index in indices:
                record(index, *search_one(index))
        else:
            record(indices[0], *search_one(indices[0]))
            for future in as_completed([submit(index) for index in indices[1:]]):
                collect(future)
    except (KeyboardInterrupt, BrokenProcessPool):
        shutdown_pool()
        raise
    except BaseException:
        for future in futures:
            future.cancel()
        raise
    best = min((i for i, (_, exact) in results.items() if exact),
               key=lambda i: (-results[i][0], i))
    next_order = sorted(results, key=lambda i: (-results[i][0], i))
    return (moves[best], evaluated, results[best][0]), next_order


def choose_move_parallel(board, color, placements, max_depth, seconds=180.0, history=None, workers=1):
    """choose_move with depths 2 and up split across worker processes.

    Depth 1 runs in this process through choose_move, which also validates the
    input and keeps a legal fallback. If workers cannot start or one dies, the
    rest of the move is searched in one process.
    """
    if type(workers) is not int or workers < 1:
        raise ValueError('workers must be a positive integer')
    if workers == 1:
        return choose_move(board, color, placements, max_depth, seconds, history)
    start = monotonic()
    deadline = start + seconds
    first = choose_move(board, color, placements, 1, seconds, history)
    if max_depth == 1 or first.completed_depth < 1 or first.value == 10000:
        return first

    query = swap_colors(board) if color == 'black' else board
    phase = phase_for(placements)
    moves = legal_moves(query, phase, True)
    repetitions = None
    if history is not None:
        repetitions = Counter()
        for item in history:
            position = swap_colors(item['board']) if color == 'black' else item['board']
            repetitions[(position, item['side'] == color)] += 1
        repetitions = dict(repetitions)

    chosen = swap_colors(first.board) if color == 'black' else first.board
    value, completed, evaluated, timed_out = first.value, 1, first.evaluated, False
    order = None
    for depth in range(2, max_depth + 1):
        try:
            (chosen, count, value), order = search_root(query, moves, depth, placements, deadline,
                                                        repetitions, workers, order)
        except SearchTimeout:
            timed_out = True
            break
        except (BrokenProcessPool, OSError):
            shutdown_pool()
            single = choose_move(board, color, placements, max_depth,
                                 max(0.0, deadline - monotonic()), history)
            if single.completed_depth >= completed:
                return Decision(single.board, evaluated + single.evaluated, single.value,
                                single.completed_depth, monotonic() - start, single.timed_out)
            timed_out = True
            break
        evaluated += count
        completed = depth
        if value == 10000:
            break  # A forced win is already proven within this search horizon.
    if color == 'black':
        chosen = swap_colors(chosen)
    if chosen not in legal_moves(board, phase, color == 'white'):
        raise RuntimeError('search returned an illegal successor')
    return Decision(chosen, evaluated, value, completed, monotonic() - start, timed_out)


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
    parser.add_argument('--workers', type=int, default=default_workers(),
                        help='search processes (default: CPU cores; 1 = single process)')
    args = parser.parse_args(argv)
    workers = args.workers
    if workers < 1:
        print('Error: workers must be at least 1', file=sys.stderr)
        return 2
    if workers > 1:
        print(f'Starting {workers} search worker processes...')
        try:
            start_pool(workers)
        except (BrokenProcessPool, OSError) as exc:
            shutdown_pool()
            print(f'Worker processes unavailable ({exc}); searching in one process.')
            workers = 1
    print(f'Search workers: {workers}')
    # run_console looks up play_session when it runs; give it the parallel chooser.
    original = tournament.play_session
    tournament.play_session = partial(original, chooser=partial(choose_move_parallel, workers=workers))
    try:
        return run_console(args.resume, args.seconds, args.depth)
    finally:
        tournament.play_session = original
        shutdown_pool()


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
    parser.add_argument('--seconds', type=float, default=180, help='search budget in seconds (at least 0.01)')
    parser.add_argument('--placements', type=int, help='placements already made, both players combined (0..18)')
    parser.add_argument('--history', help='one JSON file per game, kept from the first move')
    parser.add_argument('--workers', type=int, default=default_workers(),
                        help='search processes (default: CPU cores; 1 = single process)')
    args = parser.parse_args(argv)
    try:
        if not math.isfinite(args.seconds) or args.seconds < 0.01:
            raise ValueError('seconds must be at least 0.01')
        if time_warning(args.seconds):
            print(time_warning(args.seconds), file=sys.stderr)
        if args.workers < 1:
            raise ValueError('workers must be at least 1')
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
        try:
            result = choose_move_parallel(board, args.color, placements, args.depth, args.seconds,
                                          history, workers=args.workers)
        finally:
            shutdown_pool()
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
