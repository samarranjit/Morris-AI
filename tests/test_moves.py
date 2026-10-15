"""Concrete rule examples, including the PDF's no-eligible-capture fallback."""
import unittest
from morris.board import MILLS, NEIGHBORS, swap_colors
from morris.moves import (
    generate_add, generate_move, generate_hopping,
    generate_moves_opening_black, generate_moves_midgame_endgame,
    generate_moves_midgame_endgame_black,
)


def board(white, black):
    cells = ['x'] * 23
    for index in white:
        cells[index] = 'W'
    for index in black:
        cells[index] = 'B'
    return ''.join(cells)


class MoveRuleTests(unittest.TestCase):
    def test_all_18_mills_are_consistent_at_every_endpoint(self):
        lines = {tuple(sorted((i, *pair))) for i, pairs in enumerate(MILLS) for pair in pairs}
        self.assertEqual(len(lines), 18)
        for line in lines:
            for index in line:
                others = tuple(i for i in line if i != index)
                self.assertIn(others, MILLS[index])

    def test_empty_opponent_does_not_delete_mill_move(self):
        self.assertIn(board([0, 1, 2], []), generate_add(board([1, 2], [])))

    def test_slide_capture_and_protected_mill(self):
        before = board([0, 1, 5, 21], [8, 9, 10, 18])
        expected = board([0, 1, 2, 21], [8, 9, 10])
        self.assertIn(expected, generate_move(before))
        at_two = [b for b in generate_move(before) if b[2] == 'W' and b[5] == 'x']
        self.assertEqual(at_two, [expected])

    def test_hopping_capture_and_black_equivalence(self):
        before = board([0, 1, 21], [8, 9, 10, 18])
        expected = board([0, 1, 2], [8, 9, 10])
        self.assertIn(expected, generate_hopping(before))
        self.assertNotIn(2, NEIGHBORS[21])
        self.assertIn(swap_colors(expected), generate_moves_midgame_endgame_black(swap_colors(before)))

    def test_black_opening_capture_and_no_capture_fallback(self):
        for black in ([8, 9, 10], [8, 9, 10, 18], []):
            before = board([1, 2], black)
            expected = [swap_colors(b) for b in generate_add(before)]
            self.assertEqual(generate_moves_opening_black(swap_colors(before)), expected)

    def test_blocked_player_has_no_move(self):
        before = board([0, 1, 2, 4], [3, 5, 8, 13])
        self.assertEqual(generate_moves_midgame_endgame(before), [])
        self.assertEqual(generate_moves_midgame_endgame_black(swap_colors(before)), [])

    def test_three_pieces_hop_but_four_slide(self):
        before = board([0, 1, 4], [8, 9, 10, 18])
        self.assertIn(board([1, 4, 22], [8, 9, 10, 18]), generate_moves_midgame_endgame(before))
        before = board([0, 1, 4, 7], [8, 9, 10, 18])
        self.assertNotIn(board([1, 4, 7, 22], [8, 9, 10, 18]), generate_moves_midgame_endgame(before))
