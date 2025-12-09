#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Install donkeycar systemd service on Raspberry Pi
# This script copies the service file template and adjusts paths for the current environment
# Usage:
#   bash scripts/install_service.sh
#   bash scripts/install_service.sh --service mycar.service --repo /home/pi/mycarrepo --user pi --car-dir mycar

SERVICE_NAME="donkeycar.service"
REPO_PATH=""
CAR_USER=""
CAR_DIR="mycar"

info(){ printf "[INFO] %s\n" "$*"; }
warn(){ printf "[WARN] %s\n" "$*"; }
err(){ printf "[ERROR] %s\n" "$*" >&2; }

while [[ ${#} -gt 0 ]]; do
  case "$1" in
    --service) SERVICE_NAME="$2"; shift 2;;
    --repo) REPO_PATH="$2"; shift 2;;
    --user) CAR_USER="$2"; shift 2;;
    --car-dir) CAR_DIR="$2"; shift 2;;
    -h|--help) sed -n '1,30p' "$0"; exit 0;;
    *) shift 1;;
  esac
done

# Determine repo path if not provided
if [ -z "$REPO_PATH" ]; then
  REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -z "$REPO_PATH" ]; then
    err "Not inside a git repository. Provide --repo /path/to/repo or cd to your repo first."
    exit 1
  fi
fi

# Auto-detect the current user if not provided
if [ -z "$CAR_USER" ]; then
  CAR_USER=$(whoami)
  info "Auto-detected user: $CAR_USER"
fi

TEMPLATE_FILE="$REPO_PATH/scripts/donkeycar.service"
if [ ! -f "$TEMPLATE_FILE" ]; then
  err "Service template not found at: $TEMPLATE_FILE"
  exit 1
fi

# Create a temporary service file with the correct paths
TEMP_SERVICE=$(mktemp)
trap "rm -f $TEMP_SERVICE" EXIT

sed \
  -e "s|/home/pi/donkeycar|$REPO_PATH|g" \
  -e "s|User=pi|User=$CAR_USER|g" \
  -e "s|/home/pi/donkeycar/mycar|$REPO_PATH/$CAR_DIR|g" \
  "$TEMPLATE_FILE" > "$TEMP_SERVICE"

info "Service file will be installed:"
info "  Service name: $SERVICE_NAME"
info "  Repository path: $REPO_PATH"
info "  Car user: $CAR_USER"
info "  Car directory: $REPO_PATH/$CAR_DIR"
info ""
cat "$TEMP_SERVICE"
echo ""

read -r -p "Install this service? [y/N] " resp
case "$resp" in
  [yY]|[yY][eE][sS]) ;;
  *) info "Cancelled."; exit 0;;
esac

# Install the service file
INSTALL_PATH="/etc/systemd/system/$SERVICE_NAME"
info "Copying service file to $INSTALL_PATH"
sudo cp "$TEMP_SERVICE" "$INSTALL_PATH"
sudo chmod 644 "$INSTALL_PATH"

# Reload systemd daemon
info "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start the service
info "Enabling service to start on boot..."
if sudo systemctl enable "$SERVICE_NAME"; then
  info "Service enabled successfully"
else
  warn "Failed to enable service"
  exit 1
fi

info "Starting service..."
if sudo systemctl start "$SERVICE_NAME"; then
  info "Service started successfully"
  info ""
  info "Service status:"
  sudo systemctl status "$SERVICE_NAME" || true
  info ""
  info "Recent service logs:"
  sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true
else
  warn "Failed to start service. Check logs with:"
  echo "  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
  exit 1
fi

info ""
info "Installation complete!"
info "To manage the service, use:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo systemctl restart $SERVICE_NAME"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
