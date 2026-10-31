#!/bin/sh
# Makes the LOGIN_HASH for Claude's login. Asks for the passphrase, prints only the hash. Run it from anywhere.
cd "$(dirname "$0")/.." && PYTHONPATH=src exec uv run python -m opsmcp.server hash
