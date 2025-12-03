#!/usr/bin/env python3
"""Write measured PWM values into mycar/myconfig.py safely.

Usage examples:
  python3 scripts/write_pwm_to_myconfig.py --left 470 --right 280
  python3 scripts/write_pwm_to_myconfig.py --left 470 --right 280 --inverted
  python3 scripts/write_pwm_to_myconfig.py --file mycar/myconfig.py --left 470 --right 280

Behavior:
- Makes a timestamped backup of the target file before editing.
- If a `PWM_STEERING_THROTTLE = { ... }` dict exists, it updates or inserts
  the `STEERING_LEFT_PWM` and `STEERING_RIGHT_PWM` keys there.
- Otherwise it will try to update top-level `STEERING_LEFT_PWM`/`STEERING_RIGHT_PWM` assignments.
- If neither exist, it appends a `PWM_STEERING_THROTTLE` block at the end.

This is a best-effort textual edit (keeps comments and formatting elsewhere).
"""

from __future__ import annotations
import argparse
import re
import shutil
import sys
from datetime import datetime
import difflib


def backup(path: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    bkp = f"{path}.bak.{ts}"
    shutil.copy2(path, bkp)
    return bkp


def find_dict_block(content: str, name: str):
    # Find 'NAME = {' and return (start_index, end_index) of the braces block (inclusive)
    pattern = re.compile(rf"^{re.escape(name)}\s*=\s*\{{", re.MULTILINE)
    m = pattern.search(content)
    if not m:
        return None
    start = m.end() - 1  # position of '{'
    # find matching brace
    i = start
    depth = 0
    while i < len(content):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                return (m.start(), i + 1)
        i += 1
    return None


def replace_or_insert_in_dict(content: str, dict_name: str, key: str, val: int) -> str:
    block = find_dict_block(content, dict_name)
    entry_re = re.compile(rf"(['\"]?{re.escape(key)}['\"]?\s*:\s*)(-?\d+)")
    if block:
        s, e = block
        block_text = content[s:e]
        if entry_re.search(block_text):
            block_text = entry_re.sub(
                lambda mm: f"{mm.group(1)}{val}", block_text)
        else:
            # insert before closing brace
            block_text = block_text.rstrip()
            block_text = block_text[:-1] + f"\n    \"{key}\": {val},\n}}"
        return content[:s] + block_text + content[e:]
    else:
        return None


def replace_top_level_constant(content: str, key: str, val: int) -> str:
    # match KEY = number
    pat = re.compile(rf"^\s*{re.escape(key)}\s*=\s*-?\d+\s*$", re.MULTILINE)
    if pat.search(content):
        return pat.sub(f"{key} = {val}", content)
    return None


def append_pwm_block(content: str, left: int, right: int, inverted: bool | None) -> str:
    block = []
    block.append("\n# Added by scripts/write_pwm_to_myconfig.py")
    block.append("PWM_STEERING_THROTTLE = {")
    block.append("    \"PWM_STEERING_PIN\": \"PCA9685.1:40.1\",")
    block.append("    \"PWM_STEERING_SCALE\": 1.0,")
    block.append(f"    \"PWM_STEERING_INVERTED\": {str(bool(inverted))},")
    block.append("    \"PWM_THROTTLE_PIN\": \"PCA9685.1:40.0\",")
    block.append("    \"PWM_THROTTLE_SCALE\": 1.0,")
    block.append("    \"PWM_THROTTLE_INVERTED\": False,")
    block.append(f"    \"STEERING_LEFT_PWM\": {left},")
    block.append(f"    \"STEERING_RIGHT_PWM\": {right},")
    block.append("    \"THROTTLE_FORWARD_PWM\": 500,")
    block.append("    \"THROTTLE_STOPPED_PWM\": 370,")
    block.append("    \"THROTTLE_REVERSE_PWM\": 220,")
    block.append("}\n")
    return content + "\n" + "\n".join(block)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Write measured PWM values into mycar/myconfig.py")
    p.add_argument("--file", default="mycar/myconfig.py",
                   help="Target config file")
    p.add_argument("--left", type=int, required=False,
                   help="STEERING_LEFT_PWM value (int)")
    p.add_argument("--right", type=int, required=False,
                   help="STEERING_RIGHT_PWM value (int)")
    p.add_argument("--inverted", action="store_true",
                   help="Set PWM_STEERING_INVERTED to True")
    p.add_argument("--from-runtime", dest="from_runtime", action="store_true",
                   help="Fetch current values from running webserver API (localhost:8887 by default)")
    p.add_argument("--host", default="localhost",
                   help="Host for runtime API (default: localhost)")
    p.add_argument("--port", type=int, default=8887,
                   help="Port for runtime API (default: 8887)")
    p.add_argument("-y", "--yes", dest="yes", action="store_true",
                   help="Skip interactive confirmation and proceed")
    p.add_argument("--preview", dest="preview", action="store_true",
                   help="Show unified diff of changes before writing")
    args = p.parse_args()

    path = args.file
    # If requested, fetch values from running LocalWebController
    if args.from_runtime:
        try:
            import requests
        except Exception:
            print("Error: requests package is required to use --from-runtime")
            return 3

        url = f"http://{args.host}:{args.port}/api/config"
        try:
            resp = requests.get(url, timeout=2.0)
            resp.raise_for_status()
            j = resp.json()
        except Exception as e:
            print(f"Error fetching runtime config from {url}: {e}")
            return 4

        left_val = j.get("STEERING_LEFT_PWM")
        right_val = j.get("STEERING_RIGHT_PWM")
        inv = j.get("PWM_STEERING_INVERTED")

        if left_val is None or right_val is None:
            print(f"Runtime API did not return steering PWM values: {j}")
            return 5

        args.left = int(left_val)
        args.right = int(right_val)
        # only set inverted flag if present and truthy
        if inv is not None:
            args.inverted = bool(inv)

    # Ensure left/right are provided at this point
    if args.left is None or args.right is None:
        print("Error: --left and --right must be provided unless --from-runtime is used.")
        return 2
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return 2

    orig_content = content
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return 2

    # Interactive confirmation before making changes unless --yes supplied
    if not args.yes:
        print(f"Target file: {path}")
        print(
            f"Values to write: STEERING_LEFT_PWM={args.left}, STEERING_RIGHT_PWM={args.right}, PWM_STEERING_INVERTED={bool(args.inverted)}")
        resp = input(
            "Create timestamped backup and write these values to the file? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted by user.")
            return 0

    bkp = backup(path)
    print(f"Backup created: {bkp}")

    modified = False

    # First try updating values inside PWM_STEERING_THROTTLE dict if present
    new_content = replace_or_insert_in_dict(
        content, "PWM_STEERING_THROTTLE", "STEERING_LEFT_PWM", args.left)
    if new_content is not None:
        content = new_content
        modified = True

    new_content = replace_or_insert_in_dict(
        content, "PWM_STEERING_THROTTLE", "STEERING_RIGHT_PWM", args.right)
    if new_content is not None:
        content = new_content
        modified = True

    if args.inverted:
        new_content = replace_or_insert_in_dict(
            content, "PWM_STEERING_THROTTLE", "PWM_STEERING_INVERTED", 1)
        if new_content is not None:
            content = new_content
            modified = True

    # If no dict was present (modified still False), try top-level constants
    if not modified:
        tl = replace_top_level_constant(
            content, "STEERING_LEFT_PWM", args.left)
        if tl is not None:
            content = tl
            modified = True

        tr = replace_top_level_constant(
            content, "STEERING_RIGHT_PWM", args.right)
        if tr is not None:
            content = tr
            modified = True

    # If still not modified, append a new block at the end
    if not modified:
        content = append_pwm_block(
            content, args.left, args.right, args.inverted)
        modified = True

    if modified:
        # If preview requested, show unified diff
        if args.preview:
            diff_lines = difflib.unified_diff(
                orig_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=path,
                tofile=f"{path}.updated",
            )
            diff_text = ''.join(diff_lines)
            if not diff_text:
                print("No textual differences detected.")
            else:
                print("--- Preview diff ---")
                print(diff_text)
                print("--- End diff ---")

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"Updated values written to {path}")
        return 0
    else:
        print("No changes made.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
