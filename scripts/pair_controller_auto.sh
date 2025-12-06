#!/usr/bin/env bash
# Automated Bluetooth pairing helper for Raspberry Pi
# Features:
#  - wait for a device with a matching name pattern and auto-pair
#  - or accept a MAC to pair/trust/connect directly
#  - configurable timeout
#
# Usage:
#   sudo bash ./scripts/pair_controller_auto.sh --name "Xbox" --timeout 60
#   sudo bash ./scripts/pair_controller_auto.sh --mac AA:BB:CC:DD:EE:FF
#
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

SCRIPT_NAME=$(basename "$0")

usage() {
  cat <<EOF
Usage: sudo $SCRIPT_NAME [--mac MAC] [--name NAME-PATTERN] [--timeout SECS]

Options:
  --mac MAC           Directly try to pair/trust/connect the given MAC address
  --name PATTERN      Wait for a discovered device with NAME matching PATTERN (case-insensitive)
  --timeout SECS      How long to wait for a matching device (default 60)
  --noninteractive    Do not prompt, exit on errors
  -h, --help          Show this help

Examples:
  sudo $SCRIPT_NAME --name "Xbox" --timeout 90
  sudo $SCRIPT_NAME --mac AA:BB:CC:DD:EE:FF
EOF
  exit 1
}

MAC=""
NAME_PAT=""
TIMEOUT=60
NONINTERACTIVE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mac) MAC="$2"; shift 2;;
    --name) NAME_PAT="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --noninteractive) NONINTERACTIVE=1; shift;;
    -h|--help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

if [ -z "$MAC" -a -z "$NAME_PAT" ]; then
  echo "Either --mac or --name is required." >&2
  usage
fi

if [ -n "$MAC" ]; then
  echo "Will attempt to pair MAC: $MAC"
fi

if [ -n "$NAME_PAT" ]; then
  echo "Will wait up to $TIMEOUT seconds for a device with name matching: $NAME_PAT"
fi

function pair_trust_connect() {
  local target_mac="$1"
  echo "Pairing/trusting/connecting $target_mac"

  ( 
    echo "agent on"
    echo "default-agent"
    echo "trust $target_mac"
    echo "pair $target_mac"
    sleep 2
    echo "connect $target_mac"
    echo "quit"
  ) | bluetoothctl || true

  echo "Done. Check 'bluetoothctl info $target_mac' to verify."
}

if [ -n "$MAC" ]; then
  pair_trust_connect "$MAC"
  exit 0
fi

# Otherwise wait for a matching name
echo "Starting scan to find a device matching: $NAME_PAT"

end_time=$(( $(date +%s) + TIMEOUT ))

found_mac=""

# Start a bluetoothctl scan in background and parse Device lines
# We'll run bluetoothctl in a subshell to issue scan on/off commands
(
  bluetoothctl <<'BT' 2>/dev/null
scan on
BT
) &

trap 'echo "Stopping scan..."; (echo "scan off" | bluetoothctl >/dev/null 2>&1 || true)' EXIT

while [ $(date +%s) -lt $end_time ]; do
  # list devices and look for name match
  devices=$(bluetoothctl devices 2>/dev/null || true)
  if [ -n "$devices" ]; then
    # Devices lines look like: Device AA:BB:CC:DD:EE:FF Name
    while IFS= read -r line; do
      mac=$(echo "$line" | awk '{print $2}')
      name=$(echo "$line" | cut -d' ' -f3-)
      if echo "$name" | grep -i -q -- "$NAME_PAT"; then
        found_mac="$mac"
        found_name="$name"
        break 2
      fi
    done <<< "$devices"
  fi
  sleep 2
done

echo "Stopping scan..."
(echo "scan off" | bluetoothctl >/dev/null 2>&1 || true)

if [ -z "$found_mac" ]; then
  echo "No device matching '$NAME_PAT' discovered within $TIMEOUT seconds." >&2
  exit 2
fi

echo "Found device: $found_name ($found_mac)"

if [ $NONINTERACTIVE -eq 0 ]; then
  read -p "Proceed to pair/trust/connect $found_name ($found_mac)? [y/N] " -r
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user."
    exit 0
  fi
fi

pair_trust_connect "$found_mac"

exit 0
