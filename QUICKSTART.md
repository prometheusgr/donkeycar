# DonkeyCar CLI - Quick Start (5 Minutes)

## Installation

```bash
# Install DonkeyCar with the new CLI
pip install click>=8.0

# Or from the repository
cd /path/to/donkeycar
pip install -e .
```

## Verify Installation

```bash
# Check the CLI is working
donkey --version
donkey --help
```

## 5-Minute Workflow

### 1. Create Your First Car (1 minute)

```bash
cd ~
donkey car create --path mycar
```

**What happens:**
- Creates `mycar/` directory
- Sets up `config/` folder for car settings
- Creates `myconfig.py` for local customization
- Creates `data/`, `models/`, and `logs/` directories

### 2. Configure Hardware (2 minutes)

```bash
donkey car configure --car-path mycar
```

**What it asks:**
```
Steering axis code: 0
Invert steering? [y/N]: N
Throttle axis code: 1
Invert throttle? [y/N]: N
Record button code (or -1): 4
Mode button code (or -1): 5
```

Just press Enter for defaults if unsure. You can change these later.

### 3. Check Your Configuration (1 minute)

```bash
donkey car info --path mycar
```

**Shows:**
- Directory structure
- Current configuration values
- File count in each directory

### 4. Ready to Go! (1 minute)

You now have a car project ready to use:

```bash
# Explore more commands
donkey data --help
donkey training --help
donkey system --help

# Check your system is ready
donkey system check

# View examples
cat EXAMPLES.md
```

## Common Next Steps

### Record Some Data
```bash
donkey data record --car-path mycar --duration 60
```

### Check What Was Recorded
```bash
donkey data analyze --data-dir mycar/data
```

### Set Up Everything
```bash
donkey car create --path mycar
donkey car configure --car-path mycar
donkey system check
donkey system calibrate --device joystick
```

## Command Cheat Sheet

```bash
# MOST COMMON (use these first)
donkey car create --path mycar
donkey car configure --car-path mycar
donkey car info --car-path mycar

donkey data record --car-path mycar
donkey data analyze --data-dir mycar/data/dataset

donkey training train --car-path mycar --data-dir mycar/data/dataset
donkey training deploy --car-path mycar --model model_v1

# SYSTEM STUFF
donkey system check          # Verify setup
donkey system install        # Install dependencies
donkey system calibrate      # Set up hardware
donkey system info           # Show environment

# GET HELP ANYWHERE
donkey --help                # All commands
donkey car --help            # Car commands only
donkey <command> --help      # Detailed help
```

## Troubleshooting

### "donkey: command not found"
```bash
# Install Click first
pip install click>=8.0

# Or run with Python
python -m donkeycar.cli --help
```

### "No input devices found"
You need a joystick/controller connected for the joystick configuration step.

### "Car already exists"
If you get an error when creating, use a different path:
```bash
donkey car create --path mycar2
```

### Need More Help?
```bash
# Read the user guide
less donkeycar/cli/README.md

# See lots of examples
less EXAMPLES.md

# Check migration from old scripts
less MIGRATION.md
```

## What's Next?

After the quick start:

1. **Read the full guide**: `donkeycar/cli/README.md`
2. **Explore examples**: `EXAMPLES.md`
3. **Record real data**: Use your actual car
4. **Train a model**: `donkey training train ...`
5. **Deploy it**: `donkey training deploy ...`

## Project Structure Created

```
mycar/
├── config/car_config.py      ← Base configuration
├── myconfig.py               ← Your customizations
├── data/                     ← Training data goes here
├── models/                   ← Trained models go here
└── logs/                     ← Training logs go here
```

Edit `myconfig.py` to customize your car:
```python
# myconfig.py
from config.car_config import *

# Override any settings here
MAX_THROTTLE = 0.5           # Limit max speed
STEERING_INVERTED = True     # Invert steering if needed
```

## Pro Tips

```bash
# Use environment variables to avoid typing paths
export DONKEY_CAR_PATH=$HOME/mycar
donkey data record           # Uses DONKEY_CAR_PATH

# Chain commands for automation
donkey data record --car-path mycar --name session_1 && \
donkey training train --car-path mycar --data-dir mycar/data/session_1

# Get detailed help for any command
donkey car create --help
donkey training train --help
```

## Need to Learn More?

| Topic | File |
|-------|------|
| Full user guide | `donkeycar/cli/README.md` |
| Development guide | `donkeycar/cli/DEVELOPMENT.md` |
| Architecture | `donkeycar/cli/ARCHITECTURE.md` |
| Migration from old scripts | `MIGRATION.md` |
| Many examples | `EXAMPLES.md` |

## Get Help

- Run `donkey --help` at any time
- Check the main guide: `donkeycar/cli/README.md`
- Look at examples: `EXAMPLES.md`
- Open an issue on GitHub

---

**That's it!** You're ready to start using the DonkeyCar CLI. 🚗

Create a car, record some data, train a model, and deploy it.
