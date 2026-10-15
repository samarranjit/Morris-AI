import unittest
from morris.board import swap_colors
from morris.improved import features, static_estimate_opening_improved as opening
from morris.improved import static_estimate_midgame_endgame_improved as game
from morris.search import minimax, alphabeta
from test_moves import board


class ImprovedTests(unittest.TestCase):
    def test_color_symmetry_and_nonterminal_bounds(self):
        for position in ['xxxxxBxWWWWWBBBBxxxxxxx','WxWWxWWWWWBBBBBBBBxxxxx',board([0,1,21],[8,9,10])]:
            for estimate in (opening, game):
                self.assertEqual(estimate(position),-estimate(swap_colors(position)))
                self.assertLess(abs(estimate(position)),10000)

    def test_hopping_mobility_and_real_mill_threats(self):
        position=board([0,1,21],[8,9,10,18])
        result=features(position,'W')
        self.assertEqual(result['mobility'],3*16)
        self.assertEqual(result['blocked'],0)
        self.assertGreater(result['threats'],0)

    def test_terminal_values(self):
        self.assertEqual(game(board([0,1,2],[8,9])),10000)
        self.assertEqual(game(board([0,1],[8,9,10])),-10000)

    def test_search_equivalence_with_improved_evaluation(self):
        for phase,estimate in [('opening',opening),('midgame',game)]:
            for position in ['xxxxxBxWWWWWBBBBxxxxxxx','WxWWxWWWWWBBBBBBBBxxxxx']:
                mm=minimax(position,3,phase=phase,estimate=estimate)
                ab=alphabeta(position,3,phase=phase,estimate=estimate)
                self.assertEqual((mm[0],mm[2]),(ab[0],ab[2]))
