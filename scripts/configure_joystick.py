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


def sample_axes(dev: InputDevice, duration: int = 5):
    """Sample ABS events for `duration` seconds and return a dict of code -> (min, max, delta)."""
    print(f"Sampling axes for {duration} seconds...")
    start = time.time()
    stats = {}
    try:
        for event in dev.read_loop():
            if event.type == ecodes.EV_ABS:
                code = event.code
                val = event.value
                if code not in stats:
                    stats[code] = {'min': val, 'max': val}
                else:
                    if val < stats[code]['min']:
                        stats[code]['min'] = val
                    if val > stats[code]['max']:
                        stats[code]['max'] = val
            if time.time() - start > duration:
                break
    except KeyboardInterrupt:
        pass
    ranges = {c: (v['min'], v['max'], v['max'] - v['min'])
              for c, v in stats.items()}
    return ranges


def sample_buttons(dev: InputDevice, duration: int = 5):
    """Sample KEY events for `duration` seconds and return a set of codes seen."""
    print(
        f"Sampling buttons for {duration} seconds... Press the button(s) now.")
    start = time.time()
    seen = set()
    try:
        for event in dev.read_loop():
            if event.type == ecodes.EV_KEY:
                seen.add(event.code)
            if time.time() - start > duration:
                break
    except KeyboardInterrupt:
        pass
    return seen


def axis_name(code: int) -> str:
    inv_abs = {v: k for k, v in ecodes.ABS.items()}
    return inv_abs.get(code, str(code))


def key_name(code: int) -> str:
    inv_key = {v: k for k, v in ecodes.KEY.items()}
    return inv_key.get(code, str(code))


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
            "Enter 'm' to monitor events, 'a' to auto-detect, 'c' to capture mapping, 'q' to quit: ").strip().lower()
        if action == 'm':
            duration = input('Monitor duration seconds (default 10): ').strip()
            try:
                d = int(duration) if duration else 10
            except ValueError:
                d = 10
            monitor_device(device, duration=d)
        elif action == 'a':
            # Auto-detect steering axis
            print(
                "\nAuto-detect STEERING: move the steering control left and right repeatedly.")
            input('Press Enter to start sampling (5s)...')
            a_ranges = sample_axes(device, duration=5)
            if not a_ranges:
                print(
                    'No ABS events observed. Make sure you moved the sticks and try again.')
            else:
                # choose axis with largest range
                best = max(a_ranges.items(), key=lambda x: x[1][2])
                ste_code, (smin, smax, srange) = best
                print(
                    f"Suggested steering axis: {ste_code} ({axis_name(ste_code)}) range {smin}..{smax} (delta {srange})")
                use = input(
                    'Accept this as STEERING axis? [Y/n]: ').strip().lower()
                if use == 'n':
                    print('Detected axes:')
                    for c, (mn, mx, rng) in sorted(a_ranges.items(), key=lambda x: -x[1][2]):
                        print(
                            f"  {c} ({axis_name(c)}) range {mn}..{mx} delta {rng}")
                    ste_choice = input(
                        'Enter axis code to use for STEERING (or blank to skip): ').strip()
                    ste_code = int(ste_choice) if ste_choice else None
                steering_axis = ste_code if ste_code is not None else None

            # Auto-detect THROTTLE
            print(
                "\nAuto-detect THROTTLE: move the throttle control (forward/back) repeatedly.")
            input('Press Enter to start sampling (5s)...')
            t_ranges = sample_axes(device, duration=5)
            if not t_ranges:
                print(
                    'No ABS events observed for throttle. Make sure you moved the throttle and try again.')
            else:
                best_t = max(t_ranges.items(), key=lambda x: x[1][2])
                thr_code, (tmin, tmax, trange) = best_t
                print(
                    f"Suggested throttle axis: {thr_code} ({axis_name(thr_code)}) range {tmin}..{tmax} (delta {trange})")
                use_t = input(
                    'Accept this as THROTTLE axis? [Y/n]: ').strip().lower()
                if use_t == 'n':
                    print('Detected axes:')
                    for c, (mn, mx, rng) in sorted(t_ranges.items(), key=lambda x: -x[1][2]):
                        print(
                            f"  {c} ({axis_name(c)}) range {mn}..{mx} delta {rng}")
                    thr_choice = input(
                        'Enter axis code to use for THROTTLE (or blank to skip): ').strip()
                    thr_code = int(thr_choice) if thr_choice else None
                throttle_axis = thr_code if thr_code is not None else None

            # Auto-detect buttons
            print(
                '\nAuto-detect BUTTONS: when prompted, press the RECORD button once, then the MODE button once.')
            input('Press Enter to sample buttons for RECORD (4s)...')
            rec_seen = sample_buttons(device, duration=4)
            rec_btn = None
            if rec_seen:
                # pick first seen
                rec_btn = sorted(rec_seen)[0]
                print(
                    f"Detected candidate RECORD button: {rec_btn} ({key_name(rec_btn)})")
                if input('Accept as RECORD button? [Y/n]: ').strip().lower() == 'n':
                    rec_btn = None
            else:
                print('No button events detected for RECORD.')

            input('Press Enter to sample buttons for MODE (4s)...')
            mode_seen = sample_buttons(device, duration=4)
            mode_btn = None
            if mode_seen:
                mode_btn = sorted(mode_seen)[0]
                print(
                    f"Detected candidate MODE button: {mode_btn} ({key_name(mode_btn)})")
                if input('Accept as MODE button? [Y/n]: ').strip().lower() == 'n':
                    mode_btn = None
            else:
                print('No button events detected for MODE.')

            # Build mapping from detected values (use None if not found)
            mapping = {
                'STEERING_AXIS': steering_axis if 'steering_axis' in locals() else None,
                'THROTTLE_AXIS': throttle_axis if 'throttle_axis' in locals() else None,
                'STEERING_INVERTED': False,
                'THROTTLE_INVERTED': False,
                'RECORD_BUTTON': rec_btn,
                'MODE_BUTTON': mode_btn,
            }

            print('\nAuto-detection result:')
            for k, v in mapping.items():
                print(f"  {k}: {v}")
            if input('Write these values to mycar/myconfig.py? [y/N]: ').strip().lower().startswith('y'):
                write_mapping(mapping, device.path)
                break
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
