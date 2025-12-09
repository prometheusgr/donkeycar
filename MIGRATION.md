# DonkeyCar CLI - Migration Guide

This guide helps you migrate from the old script-based workflow to the new organized CLI.

## Old vs New

### Old Workflow

```bash
# Old scattered scripts approach
python scripts/setup_mycar.py
python scripts/configure_joystick.py
python mycar/manage.py drive
python mycar/train.py
python scripts/convert_to_tflite.py
```

### New Workflow

```bash
# New organized CLI approach
donkey car create --path mycar
donkey car configure --car-path mycar
# ... drive from your car's manage.py or new CLI ...
donkey training train --car-path mycar --data-dir mycar/data/session_001
donkey training convert --model mycar/models/model_v1.h5
```

## Migration Steps

### 1. Install the Updated DonkeyCar

```bash
# Install from updated repository
pip install -e /path/to/donkeycar

# Or upgrade existing installation
pip install --upgrade donkeycar
```

### 2. Verify CLI Installation

```bash
# Test the CLI
donkey --version
donkey --help

# Or run directly
python -m donkeycar.cli --help
```

### 3. Create a New Car Project

```bash
# Create car with CLI (replaces scripts/setup_mycar.py)
donkey car create --path mycar

# Compare old approach:
# python scripts/setup_mycar.py
```

### 4. Configure Hardware

```bash
# Interactive configuration (replaces scripts/configure_joystick.py)
donkey car configure --car-path mycar

# Old approach:
# python scripts/configure_joystick.py
```

### 5. Check Configuration

```bash
# View current configuration
donkey car info --car-path mycar
```

## Script Mapping

Here's how old scripts map to new CLI commands:

| Old Script              | New Command                  | Purpose                |
| ----------------------- | ---------------------------- | ---------------------- |
| `setup_mycar.py`        | `donkey car create`          | Create car project     |
| `configure_joystick.py` | `donkey car configure`       | Configure hardware     |
| (manage.py drive)       | (Future: `donkey car drive`) | Drive the car          |
| `multi_train.py`        | `donkey training train`      | Train models           |
| `convert_to_tflite.py`  | `donkey training convert`    | Convert models         |
| `freeze_model.py`       | (Integrated in training)     | Model optimization     |
| `convert_to_tub_v2.py`  | `donkey data convert`        | Convert data formats   |
| Various calibration     | `donkey system calibrate`    | Hardware calibration   |
| `import_test.py`        | `donkey system check`        | Environment validation |

## Legacy Support

The old command interface is still available:

```bash
# Old approach still works for backward compatibility
donkey-legacy --help

# Python scripts still work
python scripts/setup_mycar.py
python scripts/configure_joystick.py
```

However, we recommend using the new CLI for new projects.

## Organizing Existing Projects

If you have an existing car project, here's how to organize it:

### Before (Old Structure)

```
mycar/
├── ai.py
├── calibrate.py
├── camera.py
├── config.py
├── controller.py
├── drivetrain.py
├── manage.py
├── myconfig.py
├── recording.py
├── telemetry.py
├── train.py
├── __pycache__/
├── data/
├── logs/
└── models/
```

### After (New CLI Structure)

```
mycar/
├── config/
│   └── car_config.py          # New: Base configuration
├── myconfig.py                # Keep: Local overrides
├── manage.py                  # Keep: Custom drive logic
├── data/                      # Keep: Training data
├── models/                    # Keep: Trained models
├── logs/                      # Keep: Training logs
└── [archived]/
    ├── ai.py                  # Archive old files
    ├── calibrate.py
    ├── controller.py
    └── ...
```

### Migration Steps for Existing Projects

1. **Backup your current car**

   ```bash
   cp -r mycar mycar.backup
   ```

2. **Create new config structure**

   ```bash
   mkdir -p mycar/config
   ```

3. **Move base configuration**

   ```bash
   # Copy relevant settings to mycar/config/car_config.py
   cp mycar/config.py mycar/config/car_config.py
   ```

4. **Update myconfig.py**

   ```python
   # myconfig.py should now only have local overrides
   from config.car_config import *

   # Your local customizations here
   MAX_THROTTLE = 0.5
   ```

5. **Test the new structure**
   ```bash
   donkey car info --path mycar
   ```

## Data Management

### Recording Data (Old vs New)

**Old approach:**

```bash
cd mycar
python manage.py drive  # Records to mycar/data/
```

**New approach (planned):**

```bash
donkey data record --car-path mycar --name session_001
```

During transition, continue using `manage.py drive` and the CLI will auto-detect datasets.

### Training Models

**Old approach:**

```bash
cd mycar
python train.py
# or
python ../scripts/multi_train.py
```

**New approach:**

```bash
donkey training train \
  --car-path mycar \
  --data-dir mycar/data/dataset_001 \
  --epochs 100
```

## Environment Variables

For easier CLI usage, set environment variables:

```bash
# In ~/.bashrc or ~/.bash_profile

# Default car path
export DONKEY_CAR_PATH=$HOME/mycar

# Default data path (for large SSD)
export DONKEY_DATA_PATH=/media/data/donkeycar

# Enable debug output
export DONKEY_DEBUG=1
```

Then use shorter commands:

```bash
donkey car info              # Uses $DONKEY_CAR_PATH
donkey data record           # Uses $DONKEY_DATA_PATH
```

## Troubleshooting Migration

### Issue: `donkey` command not found

**Solution:**

```bash
# Reinstall package in development mode
cd /path/to/donkeycar
pip install -e .

# Or run with python module
python -m donkeycar.cli --help
```

### Issue: Click dependency missing

**Solution:**

```bash
# Install Click
pip install click>=8.0

# Or install full requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: Custom scripts in mycar don't work

**Solution:**
Your custom files in `mycar/` will continue to work. The CLI is additive and doesn't break existing functionality.

Keep your custom scripts and use CLI for new operations:

```bash
# Old custom logic still works
python mycar/manage.py drive

# New CLI handles training
donkey training train --car-path mycar --data-dir mycar/data/session_001
```

## Gradual Migration Strategy

Don't need to migrate everything at once. Here's a suggested approach:

**Phase 1: Try the CLI** (Week 1)

- Install updated DonkeyCar
- Run `donkey --help` and explore
- Run `donkey system check` to verify environment
- Keep using old scripts for production

**Phase 2: Use for New Projects** (Week 2-4)

- Use `donkey car create` for new cars
- Use `donkey car configure` for new hardware
- Continue using `manage.py drive` and `train.py` for now

**Phase 3: Migrate Existing Projects** (Month 2)

- Gradually migrate training to `donkey training train`
- Reorganize car directories
- Archive old scripts

**Phase 4: Full CLI Adoption** (Month 3+)

- Use CLI for all operations
- Keep old scripts for reference only
- Contribute improvements back to project

## Questions?

- Check the main CLI README: `donkeycar/cli/README.md`
- See command help: `donkey <command> --help`
- Open an issue on GitHub for problems
