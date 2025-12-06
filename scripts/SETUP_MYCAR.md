# Setup helper scripts

What these scripts do

- They copy a small set of template files from `donkeycar/templates` into your `mycar/` folder:
  - `cfg_basic.py` -> `mycar/config.py`
  - `train.py` -> `mycar/train.py`
  - `calibrate.py` -> `mycar/calibrate.py`
  - `myconfig.py` -> `mycar/myconfig.py`
- If a destination file already exists, the script renames the existing file to `name.YYYYMMDDHHMMSS.bak` before copying.

Files added

- `scripts/setup_mycar.py` — Cross-platform Python helper

Usage

- Python (cross-platform):
  ```powershell
  python .\scripts\setup_mycar.py
  ```

After running

- Open and edit the copied files in `mycar/`:
  - `mycar/config.py` — vehicle hardware/config defaults
  - `mycar/myconfig.py` — user-specific overrides
  - `mycar/train.py` — training parameters and scripts
  - `mycar/calibrate.py` — calibrations you may want to adjust

Notes

- These scripts are intentionally conservative: they won't overwrite your files without making a backup.
- If you want a different default config (e.g. `cfg_complete.py`), modify the mapping in the scripts before running.

Raspberry Pi: Bluetooth / controller setup

- A helper script is included to install Bluetooth and joystick tooling on Raspberry Pi:
  - `scripts/setup_bluetooth_pi.sh`
- Run on the Pi as root:
  ```bash
  sudo bash ./scripts/setup_bluetooth_pi.sh
  ```
- The script runs `apt update`, installs `bluetooth`, `bluez`, `pi-bluetooth`, `joystick`, and `evtest`, unblocks Bluetooth via `rfkill`, and enables the `bluetooth` systemd service.
- After running, pair your controller with `bluetoothctl` or the Pi GUI and verify events with `evtest`.

Joystick configuration helper (no `jstest` required)

- If `jstest` is incompatible with your kernel, you can still configure a controller using `evtest` or the included Python helper.
- Install the helper dependency:
  ```bash
  sudo apt install python3-evdev
  ```
- Run the interactive helper to monitor events and write a mapping into `mycar/myconfig.py`:
  ```bash
  python ./scripts/configure_joystick.py
  ```
- The helper will list detected input devices, let you monitor live events (shows ABS axis codes and KEY button codes), and prompt you to assign steering/throttle/button mappings. It will back up any existing `mycar/myconfig.py` before writing.
