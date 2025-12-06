"""
Cross-platform helper to copy donkeycar template files into `mycar/`.
Backs up existing files with a timestamp suffix.

Run from the repo root:
  python .\scripts\setup_mycar.py
"""
import shutil
from pathlib import Path
from datetime import datetime
import sys


def repo_root() -> Path:
    # assume this file is in scripts/ under repo root
    return Path(__file__).resolve().parent.parent


def backup_if_exists(dst: Path):
    if dst.exists():
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        bak = dst.with_name(dst.name + "." + ts + ".bak")
        print(f"Backing up {dst} -> {bak}")
        dst.rename(bak)


def main():
    root = repo_root()
    templates = root / 'donkeycar' / 'templates'
    dest = root / 'mycar'

    if not templates.exists():
        print(f"Templates directory not found: {templates}")
        sys.exit(1)

    dest.mkdir(parents=True, exist_ok=True)

    mapping = {
        'cfg_basic.py': 'config.py',
        'train.py': 'train.py',
        'calibrate.py': 'calibrate.py',
        'myconfig.py': 'myconfig.py',
    }

    for src_name, dst_name in mapping.items():
        src = templates / src_name
        dst = dest / dst_name
        if not src.exists():
            print(f"Warning: template missing: {src} -- skipping")
            continue
        backup_if_exists(dst)
        shutil.copy2(src, dst)
        print(f"Copied {src_name} -> {dst_name}")

    print('\nDone. Edit the copied files in mycar/ to configure your car.')


if __name__ == '__main__':
    main()
