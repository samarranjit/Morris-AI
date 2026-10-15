#!/bin/zsh
# Finder opens an executable .command file in Terminal on macOS.
cd -- "$(dirname -- "$0")/.." || exit 1
python3 programs/TournamentAgent.py
printf '\nPress Enter to close this launcher...'
read -r reply
