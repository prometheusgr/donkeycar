# Pi: Start service and calibrate steering

This document explains how to start the car service on a Raspberry Pi, run the realtime calibration UI, and persist steering calibration values so the car drives straight.

Quick summary

- Activate virtualenv: `source .venv/bin/activate`
- Update code and dependencies with `bash scripts/deploy_pi.sh`
- To run realtime calibrator UI: `bash scripts/pi_start_and_calibrate.sh --calibrate`
- Calibrate using the web UI at `http://<pi-ip>:8887/calibrate` and then update `mycar/myconfig.py` with the measured values.

1. Prepare the Pi

- SSH into your Pi and change to the repo root:

```bash
cd /home/pi/your-repo
```

- Make sure the virtualenv is created and dependencies installed (you said you already did this). To (re)run the standard deploy helper:

```bash
bash scripts/deploy_pi.sh
```

2. Run the realtime calibration UI

- Activate the venv (if not already):

```bash
source .venv/bin/activate
```

- Start the realtime calibration server (this runs the LocalWebController and hosts the calibration page):

```bash
bash scripts/pi_start_and_calibrate.sh --calibrate
```

- The script prints a message like `Go to http://<hostname>.local:8887/calibrate to calibrate`.
- On a machine on the same network open that URL (you can also use the Pi IP address: `http://<pi-ip>:8887/calibrate`).

3. Calibrate steering (web UI)

- The UI shows buttons that increment/decrement PWM values by 10. Use the `STEERING_LEFT_PWM` and `STEERING_RIGHT_PWM` controls to find values where:
  - The left value is the PWM that moves the servo full left
  - The right value is the PWM that moves the servo full right
- Use these steps to find the correct values:
  1. With the web UI open, press the `-`/`+` buttons next to `STEERING_LEFT_PWM` and `STEERING_RIGHT_PWM` to move the servo. Each press changes the value by 10.
  2. Try setting `STEERING_LEFT_PWM` so that when the angle is -1 (full left) the servo reaches the physical full-left stop without binding.
  3. Try setting `STEERING_RIGHT_PWM` so that when the angle is +1 (full right) the servo reaches the physical full-right stop without binding.
  4. Test center: set angle to 0 (center). The wheels should point straight. If the car still turns left while angle==0, you'll need to shift the center or invert steering direction (see next section).

Keyboard shortcuts in the UI

- Left/Right arrow keys adjust MM1 mid when using MM1.
- Up arrow will apply a short throttle pulse so you can confirm throttle calibration.

4. Persist values

The UI only changes values in RAM and pulses the hardware. After you find good values, update your `mycar/myconfig.py` (recommended for per-car overrides) so they persist across reboots:

Open `mycar/myconfig.py` and add or update the relevant entries. Example (edit the numbers to the values you measured):

```python
# Steering PWM (PCA9685 / PWM_STEERING_THROTTLE)
PWM_STEERING_THROTTLE = {
    "PWM_STEERING_PIN": "PCA9685.1:40.1",
    "PWM_STEERING_SCALE": 1.0,
    "PWM_STEERING_INVERTED": False,
    "PWM_THROTTLE_PIN": "PCA9685.1:40.0",
    "PWM_THROTTLE_SCALE": 1.0,
    "PWM_THROTTLE_INVERTED": False,
    "STEERING_LEFT_PWM": 470,   # <- measured value for your car
    "STEERING_RIGHT_PWM": 280,  # <- measured value for your car
    "THROTTLE_FORWARD_PWM": 500,
    "THROTTLE_STOPPED_PWM": 370,
    "THROTTLE_REVERSE_PWM": 220,
}
```

Alternatively you can set the top-level constants if you are using older configs:

```python
# top-level
STEERING_LEFT_PWM = 470
STEERING_RIGHT_PWM = 280
# or
STEERING_LEFT_PWM = 470
STEERING_RIGHT_PWM = 280
```

Use the provided writer utility to save values safely (creates a backup):

```bash
# If you measured values in the web UI, write them to myconfig.py:
python3 scripts/write_pwm_to_myconfig.py --left 470 --right 280

# Or fetch the current running values directly from the Pi's webserver (when LocalWebController is running):
python3 scripts/write_pwm_to_myconfig.py --from-runtime --host localhost --port 8887
```

5. If steering is reversed or always left

- If, after setting left/right pulses, the car still steers the wrong direction, you can try either:
  - Swap the `STEERING_LEFT_PWM` and `STEERING_RIGHT_PWM` values (sometimes the naming is reversed for your hardware), or
  - Toggle `PWM_STEERING_INVERTED` (set to `True`) in your `PWM_STEERING_THROTTLE` map, or
  - Multiply `JOYSTICK_STEERING_SCALE` by `-1.0` if the joystick control is inverted (in `mycar/myconfig.py`):

```python
JOYSTICK_STEERING_SCALE = -1.0
```

6. Restart the running service

- If you run the car as a systemd service (default `donkeycar.service`) restart it (from the Pi):

```bash
sudo systemctl restart donkeycar.service
sudo journalctl -u donkeycar.service -n 40 --no-pager
```

Or use the helper script to restart the service (will activate `.venv` before restart):

```bash
bash scripts/pi_start_and_calibrate.sh --service donkeycar.service
```

7. Safety notes

- Calibrate with wheels raised or the car suspended off the ground where possible (or with wheels lightly touching) to avoid uncontrolled motion.
- When applying throttle tests use small throttle durations and stand clear.

If you want, I can also:

- Add a small utility that will write measured values directly into `mycar/myconfig.py` (optional and automated), or
- Add a `systemd` service template under `scripts/` for `donkeycar.service` so it's easier to install.
