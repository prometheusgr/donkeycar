#!/usr/bin/env python3
"""
Interactive joystick configurator using python-evdev.

Features:
- Lists input devices and lets you choose one
- Live-monitor events so you can observe axis/button ids
- Prompts for steering/throttle/button assignments
- Writes a mapping block into `mycar/myconfig.py` (backs up existing file)

Requirements:
  sudo apt install python3-evdev

Usage:
  python scripts/configure_joystick.py
"""
import sys
from pathlib import Path
import time

try:
    from evdev import InputDevice, list_devices, ecodes
except Exception as e:
    print("Error: python-evdev is required. Install with: sudo apt install python3-evdev")
    sys.exit(2)


def list_input_devices():
    devs = [InputDevice(path) for path in list_devices()]
    for i, d in enumerate(devs):
        print(f"[{i}] {d.path} — {d.name}")
    return devs


def monitor_device(dev: InputDevice, duration: int = 10):
    print(
        f"Monitoring {dev.path} ({dev.name}) for {duration} seconds. Move sticks / press buttons now...")
    start = time.time()
    try:
        for event in dev.read_loop():
            if event.type == ecodes.EV_ABS:
                code = event.code
                # get human name for abs code
                inv_abs = {v: k for k, v in ecodes.ABS.items()}
                name = inv_abs.get(code, str(code))
                print(f"ABS {code} ({name}) = {event.value}")
            elif event.type == ecodes.EV_KEY:
                inv_key = {v: k for k, v in ecodes.KEY.items()}
                name = inv_key.get(event.code, str(event.code))
                print(f"KEY {event.code} ({name}) = {event.value}")
            if time.time() - start > duration:
                break
    except KeyboardInterrupt:
        pass


def prompt_assignments():
    print('\nEnter the axis/button numbers you observed in monitor:')
    steering = input('Steering axis code (e.g. 0): ').strip()
    throttle = input('Throttle axis code (e.g. 1): ').strip()
    steering_inv = input(
        'Invert steering? [y/N]: ').strip().lower().startswith('y')
    throttle_inv = input(
        'Invert throttle? [y/N]: ').strip().lower().startswith('y')
    rec_btn = input('Record button code (or blank): ').strip()
    mode_btn = input('Mode button code (or blank): ').strip()
    return {
        'STEERING_AXIS': int(steering) if steering else None,
        'THROTTLE_AXIS': int(throttle) if throttle else None,
        'STEERING_INVERTED': steering_inv,
        'THROTTLE_INVERTED': throttle_inv,
        'RECORD_BUTTON': int(rec_btn) if rec_btn else None,
        'MODE_BUTTON': int(mode_btn) if mode_btn else None,
    }


def write_mapping(mapping: dict, device_path: str):
    myconfig = Path('mycar') / 'myconfig.py'
    myconfig.parent.mkdir(parents=True, exist_ok=True)
    if myconfig.exists():
        ts = time.strftime('%Y%m%d%H%M%S')
        bak = myconfig.with_name(myconfig.name + '.' + ts + '.bak')
        print(f"Backing up existing {myconfig} -> {bak}")
        myconfig.rename(bak)

    lines = ["# Auto-generated joystick mapping by scripts/configure_joystick.py\n"]
    lines.append(f"JOYSTICK_DEVICE = '{device_path}'\n")
    for k, v in mapping.items():
        if v is None:
            continue
        if isinstance(v, bool):
            lines.append(f"{k} = {v}\n")
        else:
            # integers
            lines.append(f"{k} = {v}\n")

    # add explanatory comment
    lines.append(
        "\n# Example: STEERING_AXIS is the ABS axis code seen in evtest/monitor output\n")

    myconfig.write_text(''.join(lines))
    print(f"Wrote mapping to {myconfig}")


def main():
    print('Joystick configuration helper')
    devs = list_input_devices()
    if not devs:
        print('No input devices found. Plug in controller and try again.')
        sys.exit(1)

    choice = input(
        '\nChoose device index to configure (or press Enter to use 0): ').strip()
    if not choice:
        idx = 0
    else:
        try:
            idx = int(choice)
        except ValueError:
            print('Invalid index')
            sys.exit(2)

    device = devs[idx]

    while True:
        action = input(
            "Enter 'm' to monitor events, 'c' to capture mapping, 'q' to quit: ").strip().lower()
        if action == 'm':
            duration = input('Monitor duration seconds (default 10): ').strip()
            try:
                d = int(duration) if duration else 10
            except ValueError:
                d = 10
            monitor_device(device, duration=d)
        elif action == 'c':
            mapping = prompt_assignments()
            write_mapping(mapping, device.path)
            break
        elif action == 'q':
            break
        else:
            print('Unknown command')


if __name__ == '__main__':
    main()
