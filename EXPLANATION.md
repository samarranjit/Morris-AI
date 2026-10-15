# Implementation walkthrough and tournament preparation

## What the program does

This is a deterministic game-playing program, not a trained machine-learning
model. It generates legal moves, explores replies using minimax or alpha-beta,
and evaluates positions at the end of the explored lines.

A position is a string of 23 characters. W and B are pieces; x is empty.
A move generator returns complete successor strings, including any required
capture. Search never constructs a move by editing a string itself.

## 1. Board and moves

`morris/board.py` stores the 23 names, adjacent locations, and mill pairs.
There are 18 distinct mill lines, including four diagonals. There is no d2 or
d3. The PDF's closeMill case for index 1 says d3; its table and tested mill
identify d0. The ASCII diagram's extra line above d1 was removed.

`morris/moves.py` has three operations:

1. Opening: place a piece on an empty location.
2. Midgame: move a piece to an adjacent empty location.
3. Endgame: a player with exactly three pieces can move to any empty location.

After a move closes a mill, the generator creates one successor for each
eligible capture. Eligible opponents are outside mills. If there are no such
opponents, we retain the moved board without a capture, following the final
GenerateRemove line on page 4 of the Variant PDF. This also fixes the case
where a mill-forming move vanished when there were no opposing pieces.

The old setup assumed any piece could be removed when all opponents were in
mills. That rule is common in other Morris versions but is not what the final
pseudocode line explicitly describes. The handout uses b ambiguously, so our
choice is documented rather than presented as confirmed instructor intent.
An instructor ruling overrides this interpretation. Change generate_remove,
update capture tests and notes, and regenerate evidence together if necessary.

Black move generation swaps colors, calls the White generator, then swaps back.
This reuses exactly the same movement and capture rules for both players.

## 2. Minimax

`morris/search.py` implements one recursive traversal. At a White node it keeps
the largest child score. At a Black node it keeps the smallest. At depth zero
it calls the selected evaluator. A depth of two means our move and one reply.

The return value is `(chosen_board, evaluation_count, value)`. The chosen board
is the immediate successor at the root, not a distant leaf. Strict greater-than
and less-than comparisons keep the earliest generated move on ties.

The counter increments exactly when an estimator is called. Terminal positions
also call the estimator once, then search overrides its score when a game rule
requires it. This matters for blocked White: the handout's baseline formula
only tests Black's mobility, but White must also lose if it is White's turn and
no legal move exists. Piece losses, blockades, and tournament repetitions are
checked before ordinary horizon evaluation. During opening, low on-board piece
counts are not a loss because placements remain.

## 3. Alpha-beta

The same traversal optionally uses alpha and beta bounds. Alpha is the best
value the maximizing side can already guarantee along the current path; beta
is the minimizing side's corresponding upper bound. When alpha >= beta, the
remaining siblings cannot improve the ancestor's decision, so traversal stops.

This is ordinary alpha-beta, not a different decision algorithm. The fixed-phase
minimax and alpha-beta programs share order, evaluator, depth, and tie behavior.
An independent exhaustive reference in the tests checks both algorithms.

Two actual depth-3 examples show evaluations falling from 3778 to 481 and from
544 to 129, with identical selected boards and values. They are fully recorded
in deliverables/Examples.txt. There is no transposition table or move ordering;
keeping these out makes correctness and evaluation counts easier to explain.

## 4. Baseline, Black, and interfaces

`morris/estimation.py` is unchanged. The eight assignment entry points choose
the phase, search algorithm, evaluator, and player, then use `morris/cli.py`.
The Black programs swap the input and chosen output around the White search.
Their positive estimates favor Black, not White.

`morris/io.py` requires exactly one valid board token. File errors are reported
without a traceback. Output directories are created when needed and writes use
a temporary file followed by replacement to avoid partially written boards.
The three stdout labels are unchanged. Depth zero is supported for inspection;
it deliberately does not make a move. The tournament requires depth >= 1.

## 5. Improved evaluation

`morris/improved.py` contains the complete formulas, short comments, and feature
names. The baseline remains separate. The required explanation of features,
rationale, combination, and expected benefit is in MyStaticEstimation.txt.

The important distinction is between an opening opportunity (two pieces plus
an empty point) and a legal moving-phase mill threat. A moving piece cannot
both leave its square and count as one of the two remaining mill pieces.
Hopping mobility is computed as hopping rather than adjacency.

These weights are understandable initial choices. The implementation does not
claim they are optimal. The evaluator is deliberately small; further features
should be added only if measured games justify their runtime and complexity.

## 6. Tournament timing and state

`morris/tournament.py` wraps alpha-beta with iterative deepening. Each finished
depth replaces the previous answer. If the deadline interrupts a deeper search,
the runner keeps the last completed answer. It also stores a first legal move
before searching so even a tiny budget has a fallback. A fallback is explicitly
reported as such, with a static score rather than a completed minimax result.

The timer uses monotonic time and is checked at recursive node entry. This is
a cooperative deadline: one generator/evaluator call and I/O can extend slightly
past it. It is not an operating-system hard real-time guarantee. Leave time for
copying and posting. The runner counts all actual evaluations, including its
fallback, completed iterations, and an interrupted iteration; this differs from
the fixed-depth assignment programs' single-search counts.

Tournament search knows how many of the 18 placements have been made. When a
simulated line reaches placement 18, it switches move generation and evaluation
to midgame immediately. Surviving piece counts cannot tell us this number.

An optional JSON history stores board, side to move, and placements for each
position from the initial empty board. Loading it validates every transition.
The runner accepts an opponent's new board only if it is a legal successor.
Search includes historical and simulated repetitions; the same board with the
same side to move for the third time is a draw. The file must belong to one game.

The runner refuses to move from an ended game and checks its own chosen move
against generated legal successors before writing it. It does not post to Teams
or make claims against opponents. Those remain human decisions.

## 7. What was verified

The automated suite covers board facts, capture protection and fallback,
placement/sliding/hopping for both colors, blocked players, exact opening leaf
counts, terminal leaves, minimax/alpha-beta equivalence against an independent
oracle, Black color symmetry, all nine real entry points, input failures,
phase transitions, timeouts, history validation, and repetition semantics.

The verification script additionally validates six complete games, including
a natural repetition draw. Four compare baseline and improved evaluators at
the same depth with swapped colors. Two exercise the timed tournament chooser
for both players. Logs contain every state, allowing replay and inspection.
The first four placements are seeded random legal moves to diversify openings;
those moves are explicitly part of the test, not an agent decision.

The improved evaluator's four-game sample was three wins and one draw. This is
encouraging evidence against this baseline at depth two, not evidence of being
the best agent in class. See Validation.txt for actual measured times. No game
that hits the test move cap is called a draw; only the official repetition rule
or a real terminal position ends a game in the results.

The submission builder checks every entry point from a clean archive extraction.
The package is required beside the scripts. No external dependencies or private
machine paths are needed to run the submission.

## How to prepare for official play

1. Confirm the instructor's capture interpretation and extended deadlines.
2. Use one designated communicator and one history file per game.
3. Test the chosen budget on the actual tournament computer, especially hopping.
4. Run the command promptly after receiving the opponent's board; the four-minute
   window begins at the Teams post, not at program startup.
5. Check exit status and output. Post move number, side, and the 23-character board.
6. Keep the Teams record. Complete both colors against each assigned opponent.
7. After both games, report the official result using the assigned team IDs:
   `MATCH|TeamA|TeamB|Game1|Game2|YYYY-MM-DD`, with A, B, or D result codes.

The competitive strengths are legal moves, terminal correctness, an evaluator
that sees more than material, efficient pruning, and deadline/repetition handling.
There is no guaranteed winning strategy demonstrated here. More representative
opponents and equal-time matches are the next evidence needed for further tuning.
