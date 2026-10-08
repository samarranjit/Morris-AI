# Board

A position is 23 characters, read left to right from the bottom of the diagram. `W` is White, `B` is Black, `x` is empty.

| Index | Name | Neighbors | Mills through this square |
| --- | --- | --- | --- |
| 0 | a0 | d0, b1, a3 | a0-d0-g0, a0-b1-c2, a0-a3-a6 |
| 1 | d0 | a0, g0, d1 | a0-d0-g0 |
| 2 | g0 | d0, f1, g3 | a0-d0-g0, g0-f1-e2, g0-g3-g6 |
| 3 | b1 | a0, d1, c2, b3 | b1-d1-f1, b1-b3-b5, a0-b1-c2 |
| 4 | d1 | d0, b1, f1 | b1-d1-f1 |
| 5 | f1 | g0, d1, e2, f3 | b1-d1-f1, f1-f3-f5, g0-f1-e2 |
| 6 | c2 | b1, e2, c3 | c2-c3-c4, a0-b1-c2 |
| 7 | e2 | f1, c2, e3 | e2-e3-e4, g0-f1-e2 |
| 8 | a3 | a0, b3, a6 | a3-b3-c3, a0-a3-a6 |
| 9 | b3 | b1, a3, c3, b5 | a3-b3-c3, b1-b3-b5 |
| 10 | c3 | c2, b3, c4 | a3-b3-c3, c2-c3-c4 |
| 11 | e3 | e2, f3, e4 | e3-f3-g3, e2-e3-e4 |
| 12 | f3 | f1, e3, g3, f5 | e3-f3-g3, f1-f3-f5 |
| 13 | g3 | g0, f3, g6 | e3-f3-g3, g0-g3-g6 |
| 14 | c4 | c3, d4, b5 | c4-d4-e4, c2-c3-c4, a6-b5-c4 |
| 15 | d4 | c4, e4, d5 | c4-d4-e4, d4-d5-d6 |
| 16 | e4 | e3, d4, f5 | c4-d4-e4, e2-e3-e4, g6-f5-e4 |
| 17 | b5 | b3, c4, d5, a6 | b5-d5-f5, b1-b3-b5, a6-b5-c4 |
| 18 | d5 | d4, b5, f5, d6 | b5-d5-f5, d4-d5-d6 |
| 19 | f5 | f3, e4, d5, g6 | b5-d5-f5, f1-f3-f5, g6-f5-e4 |
| 20 | a6 | a3, b5, d6 | a6-d6-g6, a0-a3-a6, a6-b5-c4 |
| 21 | d6 | d5, a6, g6 | a6-d6-g6, d4-d5-d6 |
| 22 | g6 | g3, f5, d6 | a6-d6-g6, g0-g3-g6, g6-f5-e4 |

The handout states the neighbor list and the mill test for index 0 (`a0`) and index 1. Index 1 is `d0`. The case label `d3` in that handout paragraph does not match the index table or the condition, which tests `a0` and `g0`.

Squares that are not on the board: `d2`, `d3`. Because of that, `d0-d1` has no third square, and `c2` connects directly to `e2`. Neither pair is a mill.

The four diagonals are mills: `a0-b1-c2`, `g0-f1-e2`, `a6-b5-c4`, `g6-f5-e4`.

Row 3 is two separate lines, `a3-b3-c3` and `e3-f3-g3`.

## Handout examples

`examples/handout_position_1.txt`

```
xxxxxBxWWWWWBBBBxxxxxxx
```

`f1` is Black. `e2`, `a3`, `b3`, `c3`, and `e3` are White. `f3`, `g3`, `c4`, and `d4` are Black. Five pieces each.

`examples/handout_position_2.txt`

```
WxWWxWWWWWBBBBBBBBxxxxx
```

White: `a0`, `g0`, `b1`, `f1`, `c2`, `e2`, `a3`, `b3`. Black: `c3`, `e3`, `f3`, `g3`, `c4`, `d4`, `e4`, `b5`. Eight pieces each.

`morris.board.format_board` prints either string as a diagram.
