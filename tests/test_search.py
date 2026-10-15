"""Search checked against a separate small, exhaustive oracle."""
import random
import unittest
from morris.estimation import static_estimate_opening as opening
from morris.estimation import static_estimate_midgame_endgame as game
from morris.search import minimax, alphabeta, legal_moves
from test_moves import board


def oracle(position, depth, phase, white_turn, estimate):
    terminal = None
    if phase == 'midgame':
        if position.count('B') <= 2:
            terminal = 10000
        elif position.count('W') <= 2:
            terminal = -10000
    moves = legal_moves(position, phase, white_turn)
    if terminal is None and phase == 'midgame' and not moves:
        terminal = -10000 if white_turn else 10000
    if terminal is not None:
        return position, terminal
    if depth == 0 or not moves:
        return position, estimate(position)
    scores = [oracle(child, depth - 1, phase, not white_turn, estimate)[1] for child in moves]
    value = max(scores) if white_turn else min(scores)
    return moves[scores.index(value)], value


class SearchTests(unittest.TestCase):
    def test_empty_opening_exact_counts(self):
        for search in (minimax, alphabeta):
            self.assertEqual(search('x'*23, 0, phase='opening', estimate=opening), ('x'*23, 1, 0))
            self.assertEqual(search('x'*23, 1, phase='opening', estimate=opening), ('W'+'x'*22, 23, 1))
        self.assertEqual(minimax('x'*23, 2, phase='opening', estimate=opening), ('W'+'x'*22, 506, 0))
        self.assertEqual(alphabeta('x'*23, 2, phase='opening', estimate=opening), ('W'+'x'*22, 44, 0))

    def test_terminal_blocked_white_and_piece_losses(self):
        cases = [(board([0,1,2,4], [3,5,8,13]), -10000),
                 (board([0,1,2], [8,9]), 10000),
                 (board([0,1], [8,9,10]), -10000)]
        for position, value in cases:
            for search in (minimax, alphabeta):
                for depth in (0, 2):
                    self.assertEqual(search(position, depth, phase='midgame', estimate=game), (position,1,value))

    def test_estimator_call_count_is_real(self):
        for search in (minimax, alphabeta):
            calls = []
            def recorded(position):
                calls.append(position)
                return opening(position)
            _, count, _ = search('x'*23, 3, phase='opening', estimate=recorded)
            self.assertEqual(count, len(calls))

    def test_against_oracle_both_phases_depths_one_to_three(self):
        positions = ['xxxxxBxWWWWWBBBBxxxxxxx', 'WxWWxWWWWWBBBBBBBBxxxxx']
        rng = random.Random(4346)
        for _ in range(3):
            indices = rng.sample(range(23), 10)
            positions.append(board(indices[:5], indices[5:]))
        for phase, estimate in [('opening', opening), ('midgame', game)]:
            for position in positions:
                for depth in (1, 2, 3):
                    expected_board, expected_value = oracle(position, depth, phase, True, estimate)
                    mm = minimax(position, depth, phase=phase, estimate=estimate)
                    ab = alphabeta(position, depth, phase=phase, estimate=estimate)
                    self.assertEqual((mm[0],mm[2]), (expected_board,expected_value))
                    self.assertEqual((ab[0],ab[2]), (expected_board,expected_value))
                    self.assertLessEqual(ab[1], mm[1])
                    self.assertIn(mm[0], legal_moves(position,phase,True))

    def test_hopping_search_matches(self):
        position = board([0,1,21], [8,9,10,18])
        mm = minimax(position, 2, phase='midgame', estimate=game)
        ab = alphabeta(position, 2, phase='midgame', estimate=game)
        self.assertEqual((mm[0],mm[2]),(ab[0],ab[2]))
