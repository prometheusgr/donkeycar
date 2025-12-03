#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Simple deploy helper for Raspberry Pi
# Usage: run from inside your git repo, or pass --service to set systemd service name
# Examples:
#   bash scripts/deploy_pi.sh
#   bash scripts/deploy_pi.sh --service donkeycar.service

SERVICE_NAME="donkeycar.service"
VENV_DIR=".venv"
NO_RESTART=0

while [[ ${#} -gt 0 ]]; do
  case "$1" in
    --service) SERVICE_NAME="$2"; shift 2;;
    --no-restart) NO_RESTART=1; shift 1;;
    --venv) VENV_DIR="$2"; shift 2;;
    -h|--help) sed -n '1,120p' "$0"; exit 0;;
    *) shift 1;;
  esac
done

info(){ printf "[INFO] %s\n" "$*"; }
warn(){ printf "[WARN] %s\n" "$*"; }
err(){ printf "[ERROR] %s\n" "$*" >&2; }

if ! command -v git >/dev/null 2>&1; then
  err "git is required but not installed on this Pi. Aborting."
  exit 2
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
  err "Not inside a git repository. cd to your project folder and run this script."
  exit 2
fi
cd "$REPO_ROOT"

ORIG_REMOTE=$(git remote get-url origin 2>/dev/null || true)
info "Repository: $REPO_ROOT"
info "Origin: ${ORIG_REMOTE:-(none)}"

has_ssh_key(){
  for k in id_ed25519 id_rsa id_ecdsa id_ed25519_sk id_rsa_sk; do
    if [ -f "$HOME/.ssh/$k" ]; then
      return 0
    fi
  done
  return 1
}

convert_ssh_to_https(){
  local url="$1"
  # git@github.com:owner/repo.git -> https://github.com/owner/repo.git
  echo "$url" | sed -E 's#^(git@|ssh://git@)github.com[:/](.*)#https://github.com/\2#'
}

try_git_pull(){
  info "Fetching remote changes..."
  if git fetch --all --prune --quiet; then
    info "Running git pull --ff-only"
    if git pull --ff-only --quiet; then
      return 0
    fi
  fi
  return 1
}

info "Attempting to update code from origin..."
if try_git_pull; then
  info "Code updated via SSH/HTTPS successfully."
else
  warn "git pull failed. Checking for SSH key presence to determine next step..."
  if ! has_ssh_key; then
    warn "No SSH private key found in ~/.ssh. Attempting to switch origin to HTTPS and retry."
    if [[ "$ORIG_REMOTE" == git@* || "$ORIG_REMOTE" == ssh://* ]]; then
      HTTPS_URL=$(convert_ssh_to_https "$ORIG_REMOTE")
      if [ -n "$HTTPS_URL" ]; then
        info "Setting origin to HTTPS: $HTTPS_URL"
        git remote set-url origin "$HTTPS_URL"
        # try again
        if try_git_pull; then
          info "Pulled changes over HTTPS. Keeping origin as HTTPS (you can change it back later)."
        else
          err "Pull still failed over HTTPS. Please inspect network/auth settings."
          exit 3
        fi
      else
        err "Could not derive HTTPS URL from origin ($ORIG_REMOTE). Fix remote manually."
        exit 3
      fi
    else
      err "Origin does not look like an SSH URL and pull failed. Inspect remote and network."
      exit 3
    fi
  else
    err "An SSH key exists but git pull failed. Run 'git pull' manually to inspect errors."
    exit 3
  fi
fi

# Virtualenv setup and dependency install
if [ -d "$VENV_DIR" ]; then
  info "Activating existing venv: $VENV_DIR"
else
  info "Creating venv in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel >/dev/null

if [ -f requirements.txt ]; then
  info "Installing from requirements.txt"
  pip install -r requirements.txt
elif [ -f setup.py ] || [ -f pyproject.toml ]; then
  info "Installing package in editable mode"
  pip install -e .
else
  warn "No requirements.txt or setup.py/pyproject.toml found — skipping pip install."
fi

if [ "$NO_RESTART" -eq 0 ]; then
  if command -v systemctl >/dev/null 2>&1; then
    info "Restarting systemd service: $SERVICE_NAME"
    if sudo systemctl restart "$SERVICE_NAME"; then
      info "Service restarted. Showing last 20 journal lines:"
      sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true
    else
      warn "Failed to restart $SERVICE_NAME via systemctl. You may need to run the following manually:"
      echo "  sudo systemctl restart $SERVICE_NAME"
    fi
  else
    warn "systemctl not found. Start your car process manually (for example: run your vehicle start script)."
  fi
else
  info "--no-restart specified; skipping service restart."
fi

info "Deploy script finished."
