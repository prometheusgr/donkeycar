#!/usr/bin/env bash
# Setup Bluetooth and joystick tools on Raspberry Pi
# Run this on the Pi as root (or via sudo):
#   sudo bash ./scripts/setup_bluetooth_pi.sh

set -euo pipefail

echo "This script will update apt and install bluetooth/joystick tools."
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

read -p "Proceed with apt update/install (y/N)? " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted by user."
  exit 0
fi

echo "Updating apt..."
apt update -y || true

PKGS=(bluetooth bluez pi-bluetooth joystick evtest)
echo "Installing: ${PKGS[*]}"
apt install -y "${PKGS[@]}"

echo "Unblocking bluetooth via rfkill..."
if command -v rfkill >/dev/null 2>&1; then
  rfkill unblock bluetooth || true
else
  echo "rfkill not installed or not available; skipping unblock step."
fi

echo "Enabling and starting bluetooth service..."
systemctl enable --now bluetooth.service || true

echo
echo "Bluetooth + joystick packages installed."
echo "You may need to pair your controller using `bluetoothctl` and run `evtest` to confirm events." 
echo "If you're using a GUI, use the Pi's Bluetooth settings to pair the controller."

exit 0
