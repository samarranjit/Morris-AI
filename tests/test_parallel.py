"""Parallel search in TournamentAgent.py matches morris alpha-beta exactly."""
from collections import Counter
from pathlib import Path
import random
import sys
from time import monotonic
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'programs'))

import TournamentAgent as agent
from morris.board import swap_colors
from morris.improved import static_estimate_opening_improved, static_estimate_midgame_endgame_improved
from morris.search import alphabeta, legal_moves, SearchTimeout
from morris.tournament import choose_move, initial_state, next_state, phase_for

WORKERS = 3


def sequential(board, depth, placements, repetitions=None):
    phase = phase_for(placements)
    return alphabeta(board, depth, phase=phase,
                     estimate=static_estimate_opening_improved if phase == 'opening'
                     else static_estimate_midgame_endgame_improved,
                     game_estimate=static_estimate_midgame_endgame_improved,
                     placements=placements, repetitions=repetitions)


def random_states(seed, count):
    """Positions from random legal games, with White (the searching side) to move."""
    rng = random.Random(seed)
    states = []
    while len(states) < count:
        state = initial_state()
        for _ in range(rng.randrange(4, 40)):
            moves = legal_moves(state['board'], phase_for(state['placements']), state['side'] == 'white')
            if not moves:
                break
            state = next_state(state, rng.choice(moves))
        board = state['board'] if state['side'] == 'white' else swap_colors(state['board'])
        if state['placements'] == 18 and (board.count('W') <= 2 or board.count('B') <= 2):
            continue
        if len(legal_moves(board, phase_for(state['placements']), True)) > 1:
            states.append((board, state['placements']))
    return states


class ParallelSearchTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        agent.shutdown_pool()

    def assert_same(self, board, placements, depth, repetitions=None):
        moves = legal_moves(board, phase_for(placements), True)
        expected = sequential(board, depth, placements, repetitions)
        (chosen, _, value), _ = agent.search_root(board, moves, depth, placements, None,
                                                  repetitions, WORKERS)
        self.assertEqual((chosen, value), (expected[0], expected[2]), (board, placements, depth))

    def test_matches_sequential_on_random_positions(self):
        for board, placements in random_states(7, 24):
            for depth in (2, 3):
                self.assert_same(board, placements, depth)

    def test_matches_sequential_at_phase_change_and_deeper(self):
        for board, placements in random_states(11, 6):
            self.assert_same(board, placements, 4)
        opening = [s for s in random_states(3, 60) if s[1] == 17][:3]
        for board, placements in opening:
            self.assert_same(board, placements, 3)

    def test_reuses_move_order_without_changing_the_result(self):
        board, placements = random_states(5, 1)[0]
        moves = legal_moves(board, phase_for(placements), True)
        _, order = agent.search_root(board, moves, 2, placements, None, None, WORKERS)
        (chosen, _, value), _ = agent.search_root(board, moves, 3, placements, None, None, WORKERS, order)
        expected = sequential(board, 3, placements)
        self.assertEqual((chosen, value), (expected[0], expected[2]))

    def test_matches_sequential_with_repetition_counts(self):
        board, placements = next(s for s in random_states(9, 40) if s[1] == 18)
        moves = legal_moves(board, 'midgame', True)
        repetitions = Counter({(board, True): 2, (moves[0], False): 2})
        self.assert_same(board, placements, 3, dict(repetitions))

    def test_deadline_raises_timeout(self):
        board, placements = random_states(13, 1)[0]
        moves = legal_moves(board, phase_for(placements), True)
        with self.assertRaises(SearchTimeout):
            agent.search_root(board, moves, 6, placements, monotonic(), None, WORKERS)

    def test_same_decision_as_choose_move_for_both_colors(self):
        for board, placements in random_states(17, 4):
            color = 'white' if placements >= 18 or placements % 2 == 0 else 'black'
            if color == 'black':
                board = swap_colors(board)
            one = choose_move(board, color, placements, 3, 60)
            many = agent.choose_move_parallel(board, color, placements, 3, 60, workers=WORKERS)
            self.assertEqual((one.board, one.value, one.completed_depth),
                             (many.board, many.value, many.completed_depth))
            self.assertIn(many.board, legal_moves(board, phase_for(placements), color == 'white'))

    def test_tiny_budget_still_returns_a_legal_move(self):
        decision = agent.choose_move_parallel('x' * 23, 'white', 0, 8, 0.05, workers=WORKERS)
        self.assertIn(decision.board, legal_moves('x' * 23, 'opening', True))

    def test_one_worker_is_plain_choose_move(self):
        board, placements = next(s for s in random_states(19, 40) if s[1] == 18)
        one = choose_move(board, 'white', placements, 3, 60)
        same = agent.choose_move_parallel(board, 'white', placements, 3, 60, workers=1)
        self.assertEqual((one.board, one.value, one.evaluated), (same.board, same.value, same.evaluated))


if __name__ == '__main__':
    unittest.main()
