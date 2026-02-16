#!/usr/bin/env sh
set -eu

# Example:
#   ./backend/model/generate.sh --timesteps 300000
python -m backend.model.generate "$@"
