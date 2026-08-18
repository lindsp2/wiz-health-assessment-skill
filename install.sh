#!/usr/bin/env bash
#
# Wiz Health Assessment & Skills installer - macOS / Linux (and Git Bash on Windows).
#
#   ./install.sh                 interactive install
#   ./install.sh --yes           accept defaults, no prompts
#   ./install.sh --target all    install into every supported agent environment
#
# All arguments are passed through to install.py, which does the real work so
# that bash, PowerShell, and direct python runs behave identically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Find an interpreter that is actually Python 3.8+. The version probe matters
# on Windows, where "python3" is often a Microsoft Store stub that exists on
# PATH but cannot run anything.
PYTHON=""
for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[!] Python 3.8+ is required but was not found on PATH."
    echo "    Looked for: python3, python, py"
    echo "    Install it from https://www.python.org/downloads/ and re-run this script."
    exit 1
fi

exec "$PYTHON" install.py "$@"
