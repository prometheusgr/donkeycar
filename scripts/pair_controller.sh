#!/usr/bin/env bash
# Interactive Bluetooth pairing helper for controllers on Raspberry Pi
# Usage:
#   sudo bash ./scripts/pair_controller.sh         # interactive scan + pair
#   sudo bash ./scripts/pair_controller.sh <MAC>   # attempt pair/trust/connect to MAC

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

function scan_devices() {
  echo "Scanning for Bluetooth devices for 10 seconds..."
  # Run bluetoothctl, enable scanning for 10s, then list devices
  output=$( (echo 'scan on'; sleep 10; echo 'scan off'; echo 'devices'; echo 'quit') | bluetoothctl 2>/dev/null )
  echo "$output" | sed -n '1,200p'
  echo
  echo "Discovered devices:"
  echo "$output" | awk '/^Device/ { $1=""; print $0 }' | sed 's/^ //g' || true
}

function try_pair_trust_connect() {
  local mac=$1
  echo "Attempting to pair/trust/connect device $mac"

  # Use bluetoothctl scripted session to pair, trust and connect
  echo "Running bluetoothctl commands (output follows). If pairing requires input or a PIN, run 'bluetoothctl' interactively."

  ( 
    echo "agent on"
    echo "default-agent"
    echo "trust $mac"
    echo "pair $mac"
    sleep 2
    echo "connect $mac"
    echo "quit"
  ) | bluetoothctl || true

  echo
  echo "Check device status with:"
  echo "  bluetoothctl info $mac"
  echo "If pairing failed, open an interactive bluetoothctl session and try the commands there to follow prompts."
}

if [ $# -ge 1 ]; then
  MAC="$1"
  try_pair_trust_connect "$MAC"
  exit 0
fi

scan_devices

echo
read -p "Enter device MAC to pair (or blank to exit): " -r MAC
if [ -z "$MAC" ]; then
  echo "No MAC provided; exiting."
  exit 0
fi

try_pair_trust_connect "$MAC"

echo
echo "You can verify joystick events with `evtest` or tools like `jstest-gtk` (GUI)."
echo "For example: sudo evtest /dev/input/eventX (pick the device for your controller)."

exit 0
