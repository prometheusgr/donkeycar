#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Helper to start the car service or run the realtime calibration UI on a Pi.
# Usage:
#   bash scripts/pi_start_and_calibrate.sh --calibrate
#   bash scripts/pi_start_and_calibrate.sh --service donkeycar.service

SERVICE_NAME="donkeycar.service"
VENV_DIR=".venv"
CAR_DIR=""
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
    --path|--car-dir) CAR_DIR="$2"; shift 2;;
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

# Determine car directory. Priority: CLI --path, repo mycar, repo root if manage.py, else prompt.
if [ -n "$CAR_DIR" ]; then
  info "Using car directory from --path: $CAR_DIR"
elif [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT/mycar" ]; then
  CAR_DIR="$REPO_ROOT/mycar"
  info "Found car directory: $CAR_DIR"
elif [ -f "manage.py" ]; then
  CAR_DIR="$REPO_ROOT"
  info "Using repository root as car directory: $CAR_DIR"
else
  # prompt the user with retries and a create option
  while true; do
    echo
    echo "Enter car directory path (absolute or relative)."
    echo "  - Press Enter to use current directory ($(pwd))."
    echo "  - Type 'create' to create a new car directory now."
    echo "  - Type 'q' to abort."
    read -r -p "Car dir or action: " INPUT_DIR

    if [ -z "$INPUT_DIR" ]; then
      CAR_DIR="$(pwd)"
    elif [ "$INPUT_DIR" = "q" ] || [ "$INPUT_DIR" = "Q" ]; then
      err "Aborted by user."
      exit 1
    elif [ "$INPUT_DIR" = "create" ]; then
      # prompt for new car path
      read -r -p "Enter new car path to create (will be created): " NEW_DIR
      if [ -z "$NEW_DIR" ]; then
        echo "No path entered; returning to prompt."
        continue
      fi
      # expand and make absolute
      NEW_DIR=$(python3 - <<PY
import os,sys
p = sys.argv[1]
print(os.path.abspath(os.path.expanduser(p)))
PY
      "$NEW_DIR")
      echo "Creating new car at: $NEW_DIR"
      # run the createcar command via module so script works even if entry script not on PATH
      if python3 -m donkeycar.management.base createcar --path "$NEW_DIR"; then
        CAR_DIR="$NEW_DIR"
        echo "Created car at $CAR_DIR"
        break
      else
        echo "Failed to create car at $NEW_DIR. Try another path or check permissions." >&2
        continue
      fi
    else
      # expand tilde and make absolute
      CAR_DIR=$(python3 - <<PY
import os,sys
p = sys.argv[1]
print(os.path.abspath(os.path.expanduser(p)))
PY
      "$INPUT_DIR")
    fi

    # Validate CAR_DIR exists
    if [ -d "$CAR_DIR" ]; then
      info "Using car directory: $CAR_DIR"
      break
    else
      echo "Directory does not exist: $CAR_DIR"
      read -r -p "Create this directory and a new car there? [y/N]: " CRE
      case "$CRE" in
        [yY]|[yY][eE][sS])
          if python3 -m donkeycar.management.base createcar --path "$CAR_DIR"; then
            echo "Created car at $CAR_DIR"
            break
          else
            echo "Failed to create car at $CAR_DIR; try a different path or check permissions." >&2
            continue
          fi
          ;;
        *)
          echo "Let's try again."
          continue
          ;;
      esac
    fi
  done
fi

if [ "$CALIBRATE" -eq 1 ]; then
  info "Starting realtime calibration server (LocalWebController)."
  info "Open the URL printed below on a browser on the same network."
  # Change into the car directory for running the car-specific calibrator
  cd "$CAR_DIR"

  # If this repo contains the top-level `donkeycar` package, add the repo root
  # to PYTHONPATH so that `python3 manage.py` or `python3 mycar/calibrate.py`
  # can import the package even when run from inside the `mycar` folder.
  if [ -n "$REPO_ROOT" ] && [ -d "$REPO_ROOT/donkeycar" ]; then
    export PYTHONPATH="$REPO_ROOT${PYTHONPATH+:$PYTHONPATH}"
    info "Added $REPO_ROOT to PYTHONPATH"
  fi

  # Prefer generated mycar/calibrate.py (created by templates), else try manage.py calibrate
  if [ -f "mycar/calibrate.py" ]; then
    python3 mycar/calibrate.py drive
    exit 0
  elif [ -f "manage.py" ]; then
    # try the manage.py calibrate command; fall back to drive if calibrate not available
    if python3 manage.py calibrate; then
      exit 0
    else
      info "'manage.py calibrate' failed or is unavailable; attempting 'manage.py drive'"
      python3 manage.py drive
      exit 0
    fi
  else
    err "Could not find 'mycar/calibrate.py' or 'manage.py' in $CAR_DIR"
    err "Either run this script from your repo root, pass --path <car_dir>, or create your car with 'donkey createcar --path <dir>'"
    exit 3
  fi
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
