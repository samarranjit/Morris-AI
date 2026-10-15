# Interactive tournament console

This folder is for playing your matches. It reuses the existing engine and
changes no game rules or submission programs. The submission builder does not
include this folder, its launcher, its tests, or the saved session files.

## Open it

On macOS, open this folder in Finder and double-click `Start-Tournament.command`.
It opens Terminal. Alternatively, from the project root:

    python3 tournament_console/play.py

Choose `new`, then `white` or `black`. Press Enter for a 180-second search
budget and depth ceiling 12. Use 2 seconds for a quick practice session.

- White: the agent calculates immediately and prints your first Teams message.
- Black: the console waits for White's board before calculating your response.
- Paste a 23-character opponent board, then press Enter. You can also paste the
  two-line Teams post (Move N - Color followed by its board).
- An invalid board is rejected without advancing the game. Paste again.
- After a valid board, the agent searches and prints TWO lines to copy to Teams.
- Post those two lines yourself. The console waits for the next opponent board.

The console handles phase changes, hopping, numbering, and repetition. Your
color stays fixed throughout the game. It stops when the recorded game ends.
The saved state assumes you post the displayed move; do not post a different
board or switch to another history file midway through the match.

## Commands while waiting for the opponent

- `show`: display the current board and last recorded move.
- `time 60`: give future searches 60 seconds instead of the current budget.
- `quit`: stop; your progress is already saved.

The opponent's Teams timestamp starts the four-minute window. Waiting to paste
their move consumes that window. Adjust the budget with `time N` if necessary.
The console timer cannot know when the opponent posted to Teams.

## Resume safely

Every new game gets its own JSON in `out/tournament-console/`. The exact path
appears in Terminal. Keep it until the game and any reporting are complete.

Launch again, choose `resume`, and paste that JSON path. Or run:

    python3 tournament_console/play.py --resume /absolute/path/to/session.json

If your last calculated move was saved, it is shown again without recalculating.
If an opponent move was saved but the search was interrupted, search resumes
from that board. Ctrl+C or closing Terminal does not erase accepted moves.
This format includes your color and search settings; do not pass an older
TournamentAgent.py history array as a console session.

Start a new session only for a NEW game. To continue a game already played
through TournamentAgent.py, keep using that runner and its original history.

## Tests

    python3 -m unittest discover -s tournament_console/tests -v

The engine's tests still run separately:

    python3 -m unittest discover -s tests -v
