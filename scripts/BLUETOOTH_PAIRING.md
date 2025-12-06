# Bluetooth pairing walkthrough (Raspberry Pi)

This file walks through pairing a Bluetooth controller to a Raspberry Pi, verifying events, and troubleshooting common issues.

Prerequisites

- You ran the installer script or installed the packages:
  ```bash
  sudo bash ./scripts/setup_bluetooth_pi.sh
  ```
- `bluetoothctl` and `rfkill` should be available (provided by `bluez` / `pi-bluetooth`).

## Quick interactive pairing (recommended)

1. Make sure Bluetooth is not blocked:

   ```bash
   sudo rfkill unblock bluetooth
   rfkill list
   ```

2. Start an interactive bluetoothctl session:

   ```bash
   sudo bluetoothctl
   ```

   Inside `bluetoothctl` run:

   - `power on` — turn on the adapter
   - `agent on` — enable the pairing agent
   - `default-agent` — make it the default
   - `scan on` — begin scanning

   Wait until your controller appears (you'll see a line starting with `Device <MAC> <NAME>`).
   Note the `<MAC>` (form like `AA:BB:CC:DD:EE:FF`).

   - `pair <MAC>` — start pairing (you may need to accept/pin on device)
   - `trust <MAC>` — optionally trust so reconnections are automatic
   - `connect <MAC>` — connect to the device
   - `info <MAC>` — check the device state

   After pairing, `scan off` and `quit`.

## Automated helper (script)

If you prefer a helper that scans and tries to pair, use the included script:

```bash
sudo bash ./scripts/pair_controller.sh
# or pass a MAC directly:
sudo bash ./scripts/pair_controller.sh AA:BB:CC:DD:EE:FF
```

The script will:

- scan for 10 seconds and list discovered devices
- prompt you to enter the MAC to pair
- attempt `pair`, `trust`, and `connect` using `bluetoothctl`

If the scripted pairing fails, run `bluetoothctl` interactively (see above) so you can follow and enter any PIN prompts.

## Automated pairing by name

For fully automated pairing that waits for a device name and then pairs, use:

```bash
sudo bash ./scripts/pair_controller_auto.sh --name "Xbox" --timeout 90
# or directly by MAC:
sudo bash ./scripts/pair_controller_auto.sh --mac AA:BB:CC:DD:EE:FF
```

Options:

- `--name PATTERN` — wait until a discovered device name matches PATTERN (case-insensitive)
- `--mac MAC` — pair a specific MAC immediately
- `--timeout SECS` — how many seconds to wait for a matching device (default 60)
- `--noninteractive` — do not prompt; useful for scripts

If automated pairing fails, try interactive `bluetoothctl` to follow any prompts and PIN confirmations.

## Verifying input events

- Install `evtest` (already included in the setup script). Then list input event devices:

  ```bash
  ls -l /dev/input/by-id/
  sudo evtest
  ```

- `evtest` will show a numbered list of devices. Choose the controller device to watch button/axis events.

- Optionally install `jstest-gtk` (GUI) for mapping and calibration:
  ```bash
  sudo apt install jstest-gtk
  jstest-gtk
  ```

## Troubleshooting

- Pairing requires agent prompts: sometimes the controller needs a PIN or to accept the pair on the controller. If pairing stalls, run `bluetoothctl` interactively to follow prompts.
- If `connect` fails, try powering the controller off/on and `trust` then `connect` again.
- For BLE controllers, you may need `lescan` (`hcitool`/`bluetoothctl` handles most cases).
- Check systemd logs for the bluetooth service:
  ```bash
  sudo systemctl status bluetooth
  sudo journalctl -u bluetooth -n 200
  ```

## Security note

Trusting a device with `trust <MAC>` allows it to reconnect without prompting. Only trust devices you control.

## Next steps

- After pairing and verifying events, update `mycar/myconfig.py` or your controller configuration to ensure the car software reads controller input correctly.
- If you want, I can add an automated pairing flow that accepts a MAC and waits for the controller response, or a remote SSH runner to execute the setup on a Pi from your workstation.
