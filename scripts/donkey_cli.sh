#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Simple interactive installer / launcher for DonkeyCar on a fresh Debian/Pi
# Usage: sudo bash scripts/donkey_cli.sh  (sudo only required for apt installs)

DEFAULT_GIT_URL="https://github.com/autorope/donkeycar.git"
REPO_DIR="$HOME/donkeycar"
VENV_DIR=".venv"

info(){ printf "[INFO] %s\n" "$*"; }
err(){ printf "[ERROR] %s\n" "$*" >&2; }

ask_yes_no(){
  local prompt="$1" default="$2"
  local resp
  read -r -p "$prompt" resp || resp=""
  resp=${resp:-$default}
  case "$resp" in
    [yY]|[yY][eE][sS]) return 0;;
    *) return 1;;
  esac
}

ensure_sudo(){
  if [ "$EUID" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
      SUDO=sudo
    else
      err "This step requires root privileges but 'sudo' is not available. Run this script as root."; exit 1
    fi
  else
    SUDO=""
  fi
}

install_prereqs(){
  info "Installing Debian prerequisites (apt packages)"
  ensure_sudo
  $SUDO apt update
  $SUDO apt install -y git python3 python3-venv python3-pip build-essential libjpeg-dev ffmpeg || {
    err "apt install failed. Check your network or package sources."; return 1
  }
  info "Prerequisite packages installed."
}

# Ensure we have a suitable Python interpreter (>=3.11). On Debian/Ubuntu offer to
# install python3.11 via the deadsnakes PPA when the system python is too old.
ensure_python_version(){
  info "Checking python3 version"
  PY_VER="0.0"
  if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
  fi
  PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
  if [ -z "$PY_MAJOR" ] || [ -z "$PY_MINOR" ]; then
    PY_MAJOR=0; PY_MINOR=0
  fi

  if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 11 ]; }; then
    info "Found python $PY_VER"
    PYTHON_BIN=python3
    return 0
  fi

  info "Detected python3 version $PY_VER which is older than required (>=3.11)."
  # If Debian/Ubuntu, prompt to install python3.11 via deadsnakes
  if [ -f /etc/os-release ] && grep -qiE 'debian|ubuntu' /etc/os-release; then
    if ask_yes_no "Install Python 3.11 via deadsnakes PPA now? [y/N]: " "N"; then
      ensure_sudo
      $SUDO apt update
      $SUDO apt install -y software-properties-common || { err "failed to install prerequisites for add-apt-repository"; return 1; }
      $SUDO add-apt-repository -y ppa:deadsnakes/ppa || { err "adding deadsnakes PPA failed"; return 1; }
      $SUDO apt update
      $SUDO apt install -y python3.11 python3.11-venv python3.11-distutils || { err "Failed to install python3.11"; return 1; }
      PYTHON_BIN=python3.11
      info "Installed python3.11 and will use $PYTHON_BIN for venv creation."
      return 0
    else
      err "Python 3.11 is required. Install it manually (pyenv/conda or system packages) and re-run.";
      return 1
    fi
  else
    err "Automatic install not supported on this OS. Please install Python 3.11+ and re-run.";
    return 1
  fi
}

clone_repo(){
  read -r -p "Git URL to clone [${DEFAULT_GIT_URL}]: " GIT_URL
  GIT_URL=${GIT_URL:-$DEFAULT_GIT_URL}
  read -r -p "Destination directory [${REPO_DIR}]: " DEST
  DEST=${DEST:-$REPO_DIR}
  if [ -d "$DEST/.git" ]; then
    info "Repository already cloned at $DEST. Pulling latest changes."
    git -C "$DEST" pull || true
  else
    mkdir -p "$(dirname "$DEST")"
    git clone "$GIT_URL" "$DEST" || { err "git clone failed"; return 1; }
  fi
  REPO_DIR="$DEST"
  info "Repository available at: $REPO_DIR"
}

create_venv_and_install(){
  cd "$REPO_DIR"
  # Ensure system-level prerequisites are installed before creating venv
  install_prereqs || { err "Failed to install system prerequisites"; return 1; }

  # Ensure we have a suitable python interpreter (may install python3.11 on Debian/Ubuntu)
  PYTHON_BIN=python3
  ensure_python_version || return 1

  if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment at $VENV_DIR using $PYTHON_BIN"
    $PYTHON_BIN -m venv "$VENV_DIR"
  else
    info "Virtualenv already exists at $VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  pip install -U pip setuptools wheel
  if [ -f "requirements-pi.txt" ]; then
    info "Installing requirements from requirements-pi.txt"
    pip install -r requirements-pi.txt
  elif [ -f "requirements.txt" ]; then
    info "Installing requirements from requirements.txt"
    pip install -r requirements.txt
  else
    info "No requirements file found; skipping pip installs. You may install packages manually.";
  fi
  deactivate
}

validate_install(){
  info "Validating installation"
  if ! command -v git >/dev/null 2>&1; then err "git missing"; return 1; fi
  if ! command -v python3 >/dev/null 2>&1; then err "python3 missing"; return 1; fi
  if [ ! -d "$REPO_DIR" ]; then err "repo not found at $REPO_DIR"; return 1; fi
  cd "$REPO_DIR"
  if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    if python3 manage.py --help >/dev/null 2>&1; then
      info "manage.py runnable inside venv"
    else
      err "manage.py not runnable; some packages may be missing"
      deactivate
      return 1
    fi
    deactivate
  else
    err "virtualenv not found at $VENV_DIR"
    return 1
  fi
  info "Validation complete."
}

list_cars(){
  info "Scanning for car directories (searching for 'mycar' folders and 'manage.py')"
  local found=0
  # look for directories containing manage.py (repo root or other folders)
  while IFS= read -r -d '' d; do
    echo "- $d"
    found=1
  done < <(find "$REPO_DIR" -maxdepth 3 -type f -name manage.py -print0 | xargs -0 -n1 dirname -I 2>/dev/null || true)

  # also check for top-level mycar directory(s)
  if [ -d "$REPO_DIR/mycar" ]; then
    echo "- $REPO_DIR (contains mycar)"
    found=1
  fi

  if [ "$found" -eq 0 ]; then
    info "No car directories found. You can create one."
  fi
}

create_car(){
  read -r -p "Enter new car directory path (absolute or relative): " NEW
  if [ -z "$NEW" ]; then err "No path entered"; return 1; fi
  # expand
  NEW_ABS=$(python3 - <<PY
import os,sys
print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
  "$NEW")
  info "Creating car at: $NEW_ABS"
  cd "$REPO_DIR"
  # shellcheck disable=SC2086
  if python3 -m donkeycar.management.base createcar --path "$NEW_ABS"; then
    info "Car created at $NEW_ABS"
  else
    err "Failed to create car at $NEW_ABS"
    return 1
  fi
}

launch_calibrate(){
  cd "$REPO_DIR"
  info "Starting calibrate via existing helper script"
  bash scripts/pi_start_and_calibrate.sh --path "$REPO_DIR" --calibrate
}

launch_start(){
  cd "$REPO_DIR"
  info "Attempt to start the car service (will try systemd then fall back to direct start)"
  bash scripts/pi_start_and_calibrate.sh --path "$REPO_DIR" --start
}

main_menu(){
  while true; do
    echo
    echo "DonkeyCar Quick CLI"
    echo "1) Clone or update repository"
    echo "2) Install Debian prerequisites (apt)"
    echo "3) Create virtualenv and install Python requirements"
    echo "4) Validate installation"
    echo "5) List discovered cars"
    echo "6) Create a new car"
    echo "7) Launch realtime calibrator"
    echo "8) Start car (service or background)"
    echo "9) Exit"
    read -r -p "Choose an option [1-9]: " CH
    case "$CH" in
      1) clone_repo ;; 
      2) install_prereqs ;; 
      3) create_venv_and_install ;; 
      4) validate_install ;; 
      5) list_cars ;; 
      6) create_car ;; 
      7) launch_calibrate ;; 
      8) launch_start ;; 
      9) info "Goodbye"; exit 0 ;; 
      *) echo "Invalid choice" ;;
    esac
  done
}

# If run directly, greet and run menu
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  echo
  echo "Welcome to DonkeyCar Quick CLI"
  echo "This helper will guide you through cloning, installing, and managing cars on a fresh Debian/Pi." 
  main_menu
fi
