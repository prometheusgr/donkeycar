#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Helper to start the car service or run the realtime calibration UI on a Pi.
# Usage:
#   bash scripts/pi_start_and_calibrate.sh --calibrate
#   bash scripts/pi_start_and_calibrate.sh --service donkeycar.service

SERVICE_NAME="donkeycar.service"
VENV_DIR=".venv"
CALIBRATE=0

while [[ ${#} -gt 0 ]]; do
  case "$1" in
    --service) SERVICE_NAME="$2"; shift 2;;
    --venv) VENV_DIR="$2"; shift 2;;
    --calibrate) CALIBRATE=1; shift 1;;
    -h|--help) sed -n '1,120p' "$0"; exit 0;;
    *) shift 1;;
  esac
done

info(){ printf "[INFO] %s\n" "$*"; }
err(){ printf "[ERROR] %s\n" "$*" >&2; }

# Ensure we're at repo root (if inside git repo)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$REPO_ROOT" ]; then
  cd "$REPO_ROOT"
fi

if [ ! -d "$VENV_DIR" ]; then
  info "Virtualenv not found at $VENV_DIR. Creating..."
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [ "$CALIBRATE" -eq 1 ]; then
  info "Starting realtime calibration server (LocalWebController)."
  info "Open the URL printed below on a browser on the same network."
  # Run the calibrate drive loop which hosts the /calibrate web UI
  python3 mycar/calibrate.py drive
  exit 0
fi

# Default: restart systemd service if available
if command -v systemctl >/dev/null 2>&1; then
  info "Restarting systemd service: $SERVICE_NAME"
  sudo systemctl restart "$SERVICE_NAME" || {
    err "Failed to restart $SERVICE_NAME. Check 'sudo systemctl status $SERVICE_NAME'"
    exit 2
  }
  info "Showing recent journal lines for $SERVICE_NAME:"
  sudo journalctl -u "$SERVICE_NAME" -n 40 --no-pager || true
else
  info "systemctl not available. To run the car manually, activate venv and run your start command."
fi

info "Done."
