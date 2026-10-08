"""Checks against the Morris handout: indexing, mills, generators, estimators."""

from __future__ import annotations

import unittest

from morris.board import (
    LOCATIONS,
    NEIGHBORS,
    close_mill,
    neighbors,
    swap_colors,
    validate_board,
)
from morris.estimation import static_estimate_midgame_endgame, static_estimate_opening
from morris.moves import (
    generate_add,
    generate_hopping,
    generate_move,
    generate_moves_midgame_endgame,
    generate_moves_midgame_endgame_black,
    generate_moves_opening_black,
)

# The two positions drawn in the handout.
EXAMPLE_1 = "xxxxxBxWWWWWBBBBxxxxxxx"
EXAMPLE_2 = "WxWWxWWWWWBBBBBBBBxxxxx"

# Left-right mirror of the diagram: a<->g, b<->f, c<->e, d stays.
MIRROR = {
    0: 2, 1: 1, 2: 0,
    3: 5, 4: 4, 5: 3,
    6: 7, 7: 6,
    8: 13, 9: 12, 10: 11, 11: 10, 12: 9, 13: 8,
    14: 16, 15: 15, 16: 14,
    17: 19, 18: 18, 19: 17,
    20: 22, 21: 21, 22: 20,
}


def empty_board() -> list[str]:
    return ["x"] * 23


class BoardTests(unittest.TestCase):
    def test_location_table_matches_handout(self):
        self.assertEqual(
            LOCATIONS,
            (
                "a0", "d0", "g0", "b1", "d1", "f1", "c2", "e2",
                "a3", "b3", "c3", "e3", "f3", "g3", "c4", "d4",
                "e4", "b5", "d5", "f5", "a6", "d6", "g6",
            ),
        )

    def test_handout_neighbor_cases(self):
        self.assertEqual(set(neighbors(0)), {1, 3, 8})  # a0: d0, b1, a3
        self.assertEqual(set(neighbors(1)), {0, 2, 4})  # d0: a0, g0, d1

    def test_graph_is_symmetric(self):
        for location, adjacent in enumerate(NEIGHBORS):
            for other in adjacent:
                self.assertIn(location, NEIGHBORS[other])
            mirrored = tuple(sorted(MIRROR[other] for other in adjacent))
            self.assertEqual(mirrored, NEIGHBORS[MIRROR[location]])

    def test_close_mill_cases_from_handout(self):
        board = empty_board()
        board[0] = board[1] = board[2] = "W"  # a0-d0-g0
        self.assertTrue(close_mill(0, board))
        self.assertTrue(close_mill(1, board))
        board[1] = "x"
        self.assertFalse(close_mill(0, board))
        self.assertFalse(close_mill(1, board))

        board = empty_board()
        board[0] = board[3] = board[6] = "B"  # diagonal a0-b1-c2
        self.assertTrue(close_mill(0, board))

        board = empty_board()
        board[0] = board[8] = board[20] = "W"  # a0-a3-a6
        self.assertTrue(close_mill(0, board))

    def test_two_point_edges_are_not_mills(self):
        board = empty_board()
        board[6] = board[7] = "W"  # c2-e2
        self.assertFalse(close_mill(6, board))
        board[0] = board[1] = "W"  # d0 needs g0 as well
        self.assertFalse(close_mill(1, board))

    def test_example_strings(self):
        for board in (EXAMPLE_1, EXAMPLE_2):
            self.assertEqual(len(validate_board(board)), 23)
        self.assertEqual(EXAMPLE_1.count("W"), 5)
        self.assertEqual(EXAMPLE_1.count("B"), 5)
        self.assertEqual(EXAMPLE_2.count("W"), 8)
        self.assertEqual(EXAMPLE_2.count("B"), 8)

    def test_swap_round_trip(self):
        self.assertEqual(swap_colors(swap_colors(EXAMPLE_2)), EXAMPLE_2)
        self.assertEqual(swap_colors(EXAMPLE_1)[5], "W")
        self.assertTrue(swap_colors(EXAMPLE_1)[7] == "B")


class MoveTests(unittest.TestCase):
    def test_opening_on_empty_board_has_23_placements(self):
        moves = generate_add("x" * 23)
        self.assertEqual(len(moves), 23)
        self.assertTrue(all(move.count("W") == 1 and move.count("B") == 0 for move in moves))

    def test_placing_into_a_mill_removes_a_black_piece(self):
        board = empty_board()
        board[1] = board[2] = "W"  # d0, g0 waiting for a0
        board[8] = "B"
        moves = generate_add("".join(board))
        captures = [move for move in moves if move[0] == "W" and move[8] == "x"]
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0].count("W"), 3)
        self.assertEqual(captures[0].count("B"), 0)

    def test_blocked_mill_pieces_are_spared_until_every_black_piece_is_in_a_mill(self):
        board = empty_board()
        board[1] = board[2] = "W"
        board[8] = board[9] = board[10] = "B"  # a3-b3-c3 is a mill
        board[18] = "B"  # isolated
        moves = generate_add("".join(board))
        placed = [move for move in moves if move[0] == "W"]
        self.assertEqual(len(placed), 1)
        self.assertEqual(placed[0][18], "x")
        self.assertEqual(placed[0][8:11], "BBB")

    def test_when_all_black_pieces_are_in_mills_any_may_be_removed(self):
        board = empty_board()
        board[1] = board[2] = "W"
        board[8] = board[9] = board[10] = "B"
        moves = generate_add("".join(board))
        placed = [move for move in moves if move[0] == "W"]
        removed = [
            tuple(index for index in (8, 9, 10) if move[index] == "x") for move in placed
        ]
        self.assertEqual(sorted(removed), [(8,), (9,), (10,)])

    def test_midgame_slides_only_to_neighbors(self):
        board = "x" * 23
        board = "W" + board[1:]
        moves = generate_move(board)
        destinations = {move.find("W") for move in moves}
        self.assertEqual(destinations, {1, 3, 8})

    def test_hopping_is_used_only_at_three_white_pieces(self):
        three = list("x" * 23)
        three[0] = three[4] = three[21] = "W"
        hops = generate_moves_midgame_endgame("".join(three))
        self.assertEqual(len(hops), len(generate_hopping("".join(three))))
        four = three.copy()
        four[2] = "W"
        slides = generate_moves_midgame_endgame("".join(four))
        self.assertEqual(slides, generate_move("".join(four)))

    def test_black_opening_places_a_black_piece(self):
        moves = generate_moves_opening_black("x" * 23)
        self.assertEqual(len(moves), 23)
        self.assertTrue(all(move.count("B") == 1 for move in moves))


class EstimationTests(unittest.TestCase):
    def test_opening_estimate_is_the_piece_difference(self):
        self.assertEqual(static_estimate_opening(EXAMPLE_1), 0)
        self.assertEqual(static_estimate_opening(EXAMPLE_2), 0)
        self.assertEqual(static_estimate_opening("W" + "x" * 22), 1)

    def test_midgame_terminal_scores(self):
        two_black = "WWW" + "BB" + "x" * 18
        self.assertEqual(static_estimate_midgame_endgame(two_black), 10000)
        two_white = "WW" + "BBB" + "x" * 18
        self.assertEqual(static_estimate_midgame_endgame(two_white), -10000)

    def test_midgame_score_counts_black_moves(self):
        board = list("x" * 23)
        board[0] = board[4] = board[7] = "W"
        board[20] = board[21] = board[22] = "B"
        text = "".join(board)
        black_moves = generate_moves_midgame_endgame_black(text)
        self.assertGreater(len(black_moves), 0)
        self.assertEqual(
            static_estimate_midgame_endgame(text),
            1000 * (3 - 3) - len(black_moves),
        )


if __name__ == "__main__":
    unittest.main()
