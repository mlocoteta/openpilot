#!/usr/bin/env bash
# Live-reload dev launcher for The Galaxy.
# Usage:
#   scripts/galaxy_live.sh            # serve repo live on :8083
#   scripts/galaxy_live.sh 8099       # or a specific port
#   scripts/galaxy_live.sh --sync     # sync host runtime first (after big pulls)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
WT="${ROOT}/.host_runtime/${PLATFORM}/worktree"
GX="starpilot/system/the_galaxy"
PORT="${SP_GALAXY_PORT:-8083}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: scripts/galaxy_live.sh [--sync] [port]"
  exit 0
fi
if [[ "${1:-}" == "--sync" ]]; then
  shift
  "${ROOT}/scripts/host_tool_runner.sh" sync
fi
if [[ -n "${1:-}" && "${1}" =~ ^[0-9]+$ ]]; then
  PORT="${1}"
fi

if [[ ! -d "${WT}/.venv" || ! -f "${WT}/${GX}/the_galaxy.py" ]]; then
  echo "Host runtime not ready yet. Run once: ${ROOT}/dev galaxy   (then stop it)"
  exit 1
fi

rm -rf "${WT}/${GX}"
ln -s "${ROOT}/${GX}" "${WT}/${GX}"

echo "Galaxy live-dev -> http://127.0.0.1:${PORT}/   (backend auto-reload ON)"
echo "Edit repo files. Backend .py restarts; frontend needs a hard-refresh. Errors print here."
echo "Stop with Ctrl+C."

cd "${WT}"
export PYTHONPATH="${WT}:${WT}/starpilot/third_party"
for d in "${WT}"/*_repo; do
  [[ -d "${d}" ]] && export PYTHONPATH="${PYTHONPATH}:${d}"
done
export SP_GALAXY_DIR="${SP_GALAXY_DIR:-${HOME}/.comma/starpilot/data/galaxy}"
export SP_GALAXY_HOST="0.0.0.0"
export SP_GALAXY_PORT="${PORT}"
export SP_GALAXY_DEBUG="1"
export SP_GALAXY_RELOAD="1"
exec "${WT}/.venv/bin/python3" -m openpilot.starpilot.system.the_galaxy.the_galaxy
