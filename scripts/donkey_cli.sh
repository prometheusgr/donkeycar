#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Simple interactive installer / launcher for DonkeyCar on a fresh Debian/Pi
# Usage: sudo bash scripts/donkey_cli.sh  (sudo only required for apt installs)

DEFAULT_GIT_URL="https://github.com/prometheusgr/donkeycar.git"
# If the script is run with sudo, prefer the invoking user's home directory
# (SUDO_USER) so we don't default to /root. Fall back to $HOME when absent.
if [ -n "${SUDO_USER-}" ]; then
  USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6 || true)
  # fallback if getent failed for some reason
  USER_HOME=${USER_HOME:-"/home/$SUDO_USER"}
else
  USER_HOME="$HOME"
fi
REPO_DIR="$USER_HOME/donkeycar"
VENV_DIR=".venv"
LOGFILE="${USER_HOME}/donkey_cli_install.log"

info(){ printf "[INFO] %s\n" "$*"; printf "%s [INFO] %s\n" "$(date --iso-8601=seconds)" "$*" >> "$LOGFILE"; }
err(){ printf "[ERROR] %s\n" "$*" >&2; printf "%s [ERROR] %s\n" "$(date --iso-8601=seconds)" "$*" >> "$LOGFILE"; }

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
  $SUDO apt update >> "$LOGFILE" 2>&1
  $SUDO apt install -y git python3 python3-venv python3-pip python3-dev build-essential libjpeg-dev libcap-dev ffmpeg >> "$LOGFILE" 2>&1 || {
    err "apt install failed. Check your network or package sources."; return 1
  }
  info "Prerequisite packages installed."
}

# Ensure we have a suitable Python interpreter (>=3.11).
# On Debian try installing `python3.11` from apt. On Ubuntu fall back to
# deadsnakes PPA. If the package is not available, instruct the user to
# install via pyenv or similar.
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

  # If a virtualenv already exists in the repo, prefer it if it already
  # provides a suitable Python (>=3.11). Prompt the user to use it and
  # skip any Python install steps if they agree.
  if [ -n "${REPO_DIR-}" ] && [ -n "${VENV_DIR-}" ] && [ -d "$REPO_DIR/$VENV_DIR" ]; then
    VENV_PY="$REPO_DIR/$VENV_DIR/bin/python3"
    if [ ! -x "$VENV_PY" ]; then
      VENV_PY="$REPO_DIR/$VENV_DIR/bin/python"
    fi
    if [ -x "$VENV_PY" ]; then
      VENV_VER=$($VENV_PY -c 'import sys; print(f"%s.%s"%(sys.version_info.major, sys.version_info.minor))' 2>/dev/null || true)
      if [ -n "$VENV_VER" ]; then
        VENV_MAJOR=$(echo "$VENV_VER" | cut -d. -f1)
        VENV_MINOR=$(echo "$VENV_VER" | cut -d. -f2)
        if [ "$VENV_MAJOR" -gt 3 ] || { [ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -ge 11 ]; }; then
          if ask_yes_no "Detected existing venv at $REPO_DIR/$VENV_DIR using Python $VENV_VER. Use it and skip installing Python 3.11? [Y/n]: " "Y"; then
            PYTHON_BIN="$VENV_PY"
            info "Using existing venv Python $VENV_VER (no Python install needed)"
            return 0
          fi
        fi
      fi
    fi
  fi

  if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 11 ]; }; then
    info "Found python $PY_VER"
    # Ask user whether to use system python or force-install 3.11 (useful when system has newer like 3.13)
    if ask_yes_no "Use system Python $PY_VER instead of installing Python 3.11? [Y/n]: " "Y"; then
      PYTHON_BIN=python3
      return 0
    else
      info "User requested forcing Python 3.11 install (via pyenv)."
      install_pyenv_python311 || { err "Failed to install Python 3.11 via pyenv"; return 1; }
      return 0
    fi
  fi

  info "Detected python3 version $PY_VER which is older than required (>=3.11)."
  # Try to install python3.11 from apt on Debian systems
  if [ -f /etc/os-release ] && grep -qiE 'debian' /etc/os-release; then
    if ask_yes_no "Attempt to install Python 3.11 from apt now? [y/N]: " "N"; then
      ensure_sudo
      $SUDO apt update >> "$LOGFILE" 2>&1
      # Show candidate version and ask for explicit confirmation before install
      CANDIDATE_VER=$(apt-cache policy python3.11 2>/dev/null | awk '/Candidate:/ {print $2}' || true)
      if [ -n "$CANDIDATE_VER" ]; then
        if ! ask_yes_no "Found candidate python3.11 version: ${CANDIDATE_VER}. Install it now? [y/N]: " "N"; then
          err "User declined installation of python3.11 from apt.";
          return 1
        fi
      else
        info "No candidate package version for python3.11 found in apt metadata. Will attempt install anyway."
      fi
      # Try to install python3.11 packages from the distro repositories
      if $SUDO apt install -y python3.11 python3.11-venv python3.11-distutils >> "$LOGFILE" 2>&1; then
        PYTHON_BIN=python3.11
        info "Installed python3.11 and will use $PYTHON_BIN for venv creation."
        return 0
      else
        err "apt could not install python3.11 from the repositories."
        if ask_yes_no "Install Python 3.11 via pyenv (will build from source; may take long)? [y/N]: " "N"; then
          install_pyenv_python311 || { err "pyenv-based install failed"; return 1; }
          return 0
        fi
        err "You can install Python 3.11 using pyenv or by adding an appropriate repository."
        return 1
      fi
    else
      err "Python 3.11 is required. Install it manually (pyenv/conda or system packages) and re-run.";
      return 1
    fi
  fi

  # For Ubuntu use deadsnakes PPA as before
  if [ -f /etc/os-release ] && grep -qiE 'ubuntu' /etc/os-release; then
    if ask_yes_no "Install Python 3.11 via deadsnakes PPA now? [y/N]: " "N"; then
      ensure_sudo
      $SUDO apt update >> "$LOGFILE" 2>&1
      $SUDO apt install -y software-properties-common >> "$LOGFILE" 2>&1 || { err "failed to install prerequisites for add-apt-repository"; return 1; }
      $SUDO add-apt-repository -y ppa:deadsnakes/ppa >> "$LOGFILE" 2>&1 || { err "adding deadsnakes PPA failed"; return 1; }
      $SUDO apt update >> "$LOGFILE" 2>&1
      # Show candidate version and ask for explicit confirmation before install
      CANDIDATE_VER=$(apt-cache policy python3.11 2>/dev/null | awk '/Candidate:/ {print $2}' || true)
      if [ -n "$CANDIDATE_VER" ]; then
        if ! ask_yes_no "Found candidate python3.11 version: ${CANDIDATE_VER}. Install it now? [y/N]: " "N"; then
          err "User declined installation of python3.11 from apt.";
          return 1
        fi
      else
        info "No candidate package version for python3.11 found in apt metadata. Will attempt install anyway."
      fi
      if $SUDO apt install -y python3.11 python3.11-venv python3.11-distutils >> "$LOGFILE" 2>&1; then
        PYTHON_BIN=python3.11
        info "Installed python3.11 and will use $PYTHON_BIN for venv creation."
        return 0
      else
        err "Failed to install python3.11 via apt/deadsnakes."
        if ask_yes_no "Install Python 3.11 via pyenv (will build from source; may take long)? [y/N]: " "N"; then
          install_pyenv_python311 || { err "pyenv-based install failed"; return 1; }
          return 0
        fi
        return 1
      fi
    else
      err "Python 3.11 is required. Install it manually (pyenv/conda or system packages) and re-run.";
      return 1
    fi
  fi

  err "Automatic install not supported on this OS. Please install Python 3.11+ and re-run.";
  return 1
}


# Install pyenv in the invoking user's homedir (if necessary) and build Python 3.11
install_pyenv_python311(){
  info "Installing Python 3.11 via pyenv (this will build from source)."
  # Install system build deps
  ensure_sudo
  info "Installing build dependencies for pyenv/python build"
  $SUDO apt update >> "$LOGFILE" 2>&1
  $SUDO apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
    tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev libcap-dev python3-dev >> "$LOGFILE" 2>&1 || {
    err "Failed to install build dependencies via apt"; return 1
  }

  # Determine user to install pyenv for (when run via sudo prefer SUDO_USER)
  if [ -n "${SUDO_USER-}" ]; then
    PYENV_USER="$SUDO_USER"
    PYENV_HOME=$(getent passwd "$PYENV_USER" | cut -d: -f6 || true)
    PYENV_HOME=${PYENV_HOME:-"/home/$PYENV_USER"}
  else
    PYENV_USER="$USER"
    PYENV_HOME="$HOME"
  fi

  PYENV_ROOT="$PYENV_HOME/.pyenv"

  # Clone pyenv if needed
    if [ ! -d "$PYENV_ROOT" ]; then
    info "Cloning pyenv into $PYENV_ROOT"
    if [ -n "${SUDO_USER-}" ]; then
      sudo -u "$PYENV_USER" -H git clone https://github.com/pyenv/pyenv.git "$PYENV_ROOT" >> "$LOGFILE" 2>&1 || { err "git clone pyenv failed"; return 1; }
    else
      git clone https://github.com/pyenv/pyenv.git "$PYENV_ROOT" >> "$LOGFILE" 2>&1 || { err "git clone pyenv failed"; return 1; }
    fi
  else
    info "pyenv already present at $PYENV_ROOT"
  fi

  # Prefer calling the pyenv binary directly from the cloned location
  PYENV_BIN="$PYENV_ROOT/bin/pyenv"
  # Find latest 3.11.x available to pyenv
  if [ -n "${SUDO_USER-}" ]; then
    LATEST_311=$(sudo -u "$PYENV_USER" -H "$PYENV_BIN" install --list 2>>"$LOGFILE" | grep -E '^\s*3\.11' | tail -1 | tr -d '[:space:]' || true)
    if [ -z "$LATEST_311" ]; then
      # Try calling pyenv directly as the user (fallback)
      LATEST_311=$(sudo -u "$PYENV_USER" -H bash -lc "'$PYENV_BIN' install --list 2>>\"$LOGFILE\" | grep -E '^\\s*3\\.11' | tail -1 | tr -d '[:space:]'" || true)
    fi
  else
    LATEST_311=$($PYENV_BIN install --list 2>>"$LOGFILE" | grep -E '^\s*3\.11' | tail -1 | tr -d '[:space:]' || true)
  fi

  if [ -z "$LATEST_311" ]; then
    info "Could not determine latest 3.11 release from pyenv. Defaulting to '3.11.0'."
    LATEST_311="3.11.0"
  fi

  info "Installing Python $LATEST_311 via pyenv (this may take a long time)"
  if [ -n "${SUDO_USER-}" ]; then
    sudo -u "$PYENV_USER" -H "$PYENV_BIN" install -s "$LATEST_311" >> "$LOGFILE" 2>&1 || { err "pyenv install failed (see $LOGFILE)"; return 1; }
    sudo -u "$PYENV_USER" -H "$PYENV_BIN" global "$LATEST_311" >> "$LOGFILE" 2>&1 || { err "pyenv global failed (see $LOGFILE)"; return 1; }
  else
    "$PYENV_BIN" install -s "$LATEST_311" >> "$LOGFILE" 2>&1 || { err "pyenv install failed (see $LOGFILE)"; return 1; }
    "$PYENV_BIN" global "$LATEST_311" >> "$LOGFILE" 2>&1 || { err "pyenv global failed (see $LOGFILE)"; return 1; }
  fi

  # Set PYTHON_BIN to the installed python3.11
  PYTHON_BIN="$PYENV_ROOT/versions/$LATEST_311/bin/python3.11"
  if [ ! -x "$PYTHON_BIN" ]; then
    err "Expected python binary not found at $PYTHON_BIN"
    return 1
  fi
  info "Installed Python $LATEST_311 via pyenv; using $PYTHON_BIN"
  return 0
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
  # Ensure the repository directory exists. If not, offer to clone it now.
  if [ ! -d "$REPO_DIR" ]; then
    info "Repository directory $REPO_DIR not found."
    if ask_yes_no "Clone repository now into $REPO_DIR? [y/N]: " "N"; then
      clone_repo || { err "Clone failed"; return 1; }
    else
      read -r -p "Enter an existing repository path to use (or leave empty to abort): " NEW_REPO
      if [ -z "$NEW_REPO" ]; then
        err "No repository available; aborting venv creation."; return 1
      fi
      if [ -d "$NEW_REPO" ]; then
        REPO_DIR="$NEW_REPO"
      else
        err "Provided path does not exist: $NEW_REPO"; return 1
      fi
    fi
  fi
  cd "$REPO_DIR"
  # Ensure system-level prerequisites are installed before creating venv
  install_prereqs || { err "Failed to install system prerequisites"; return 1; }

  # Ensure we have a suitable python interpreter (may install python3.11 on Debian/Ubuntu)
  PYTHON_BIN=python3
  ensure_python_version || return 1
  # If a venv already exists, check its python version. If it doesn't match
  # the requested PYTHON_BIN, offer to recreate it so the correct interpreter
  # is used (important for packages that require specific Python versions).
  if [ -d "$VENV_DIR" ]; then
    VENV_PY="$VENV_DIR/bin/python3"
    if [ ! -x "$VENV_PY" ]; then
      VENV_PY="$VENV_DIR/bin/python"
    fi
    if [ -x "$VENV_PY" ]; then
      EXISTING_VER=$($VENV_PY -c 'import sys; print(f"%s.%s"%(sys.version_info.major, sys.version_info.minor))' 2>/dev/null || echo "0.0")
    else
      EXISTING_VER="none"
    fi
    # get requested python version
    REQ_VER=$($PYTHON_BIN -c 'import sys; print(f"%s.%s"%(sys.version_info.major, sys.version_info.minor))' 2>/dev/null || echo "0.0")
    if [ "$EXISTING_VER" != "$REQ_VER" ]; then
      info "Existing virtualenv at $VENV_DIR uses Python $EXISTING_VER but requested interpreter is $REQ_VER"
      if ask_yes_no "Remove and recreate virtualenv using Python $REQ_VER? [y/N]: " "N"; then
        info "Removing existing virtualenv at $VENV_DIR"
        rm -rf "$VENV_DIR" || { err "Failed to remove $VENV_DIR"; return 1; }
        info "Creating virtual environment at $VENV_DIR using $PYTHON_BIN"
        $PYTHON_BIN -m venv "$VENV_DIR"
      else
        info "Keeping existing virtualenv (packages will be installed into Python $EXISTING_VER)."
      fi
    else
      info "Virtualenv already exists at $VENV_DIR and uses Python $EXISTING_VER"
    fi
  else
    info "Creating virtual environment at $VENV_DIR using $PYTHON_BIN"
    $PYTHON_BIN -m venv "$VENV_DIR"
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

remove_venv(){
  # Remove the virtualenv directory so the installer can start from step 3
  local VENV_PATH="$REPO_DIR/$VENV_DIR"
  read -r -p "Remove virtualenv at ${VENV_PATH}? [y/N]: " resp || resp="N"
  resp=${resp:-N}
  case "$resp" in
    [yY]|[yY][eE][sS])
      if [ -d "$VENV_PATH" ]; then
        info "Removing virtualenv at $VENV_PATH"
        rm -rf "$VENV_PATH" || { err "Failed to remove $VENV_PATH"; return 1; }
        info "Removed virtualenv. You can now re-run option 3 to recreate it."
      else
        info "No virtualenv found at $VENV_PATH"
      fi
      ;;
    *)
      info "Aborted; virtualenv not removed."
      ;;
  esac
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
    echo "10) Remove virtualenv (.venv)"
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
      10) remove_venv ;; 
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
