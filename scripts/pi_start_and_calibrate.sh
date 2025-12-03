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
START_SERVICE_IF_MISSING=0
START_FOREGROUND=0
ASSUME_YES=0
LOG_DIR="logs"
PIDFILE=".donkeycar.pid"

while [[ ${#} -gt 0 ]]; do
  case "$1" in
    --service) SERVICE_NAME="$2"; shift 2;;
    --venv) VENV_DIR="$2"; shift 2;;
    --calibrate) CALIBRATE=1; shift 1;;
      --start) START_SERVICE_IF_MISSING=1; shift 1;;
      --foreground) START_FOREGROUND=1; shift 1;;
      --yes) ASSUME_YES=1; shift 1;;
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

# Helper to run the car directly when systemd unit is not available.
start_car_directly(){
  # Ensure log dir exists
  mkdir -p "$LOG_DIR"

  if [ "$START_FOREGROUND" -eq 1 ]; then
    info "Starting car in foreground: python3 mycar/manage.py drive"
    python3 mycar/manage.py drive
  else
    info "Starting car in background (logs -> $LOG_DIR/donkeycar.log)"
    nohup python3 mycar/manage.py drive >"$LOG_DIR/donkeycar.log" 2>&1 &
    echo $! > "$PIDFILE"
    info "Car started (pid $(cat "$PIDFILE")). Logs: $LOG_DIR/donkeycar.log"
  fi
}

# Default: restart systemd service if available
if command -v systemctl >/dev/null 2>&1; then
  # Check whether the named unit exists (loaded or known by systemd) before restarting.
  if systemctl list-units --all --type=service --no-legend | awk '{print $1}' | grep -xq "$SERVICE_NAME"; then
    info "Restarting systemd service: $SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME" || {
      err "Failed to restart $SERVICE_NAME. Check 'sudo systemctl status $SERVICE_NAME'"
      exit 2
    }
    info "Showing recent journal lines for $SERVICE_NAME:"
    sudo journalctl -u "$SERVICE_NAME" -n 40 --no-pager || true
  else
    err "Unit $SERVICE_NAME not found."
    info "If you intended to run the realtime calibrator instead, run:"
    info "  bash scripts/pi_start_and_calibrate.sh --calibrate"
    info "To troubleshoot the service, check:"
    info "  sudo systemctl list-units --all --type=service | grep $SERVICE_NAME || true"
    info "  sudo systemctl status $SERVICE_NAME || true"

    if [ "$START_SERVICE_IF_MISSING" -eq 1 ] || [ "$ASSUME_YES" -eq 1 ]; then
      # Non-interactive or forced start requested
      if [ "$ASSUME_YES" -eq 0 ]; then
        info "About to start the car directly (no systemd unit). Proceed? [y/N]"
        read -r resp || resp=n
        case "$resp" in
          [yY]|[yY][eE][sS]) ;;
          *) info "Aborting as requested."; exit 4;;
        esac
      fi

      # Try to start the car directly (background by default)
      start_car_directly
      exit 0
    else
      info "If you'd like this script to attempt to start the car directly, re-run with --start"
      info "Or to auto-accept prompts, add --yes"
      exit 3
    fi
  fi
else
  info "systemctl not available. To run the car manually, activate venv and run your start command."
fi

info "Done."
