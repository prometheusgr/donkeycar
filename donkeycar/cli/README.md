# DonkeyCar CLI - Organized Command Interface

A unified, organized command-line interface for managing DonkeyCar projects across three main areas: **Car**, **Data**, and **Training**.

## Overview

The DonkeyCar CLI is organized around three core workflows:

```
donkey
├── car       - Create, configure, and manage car instances
├── data      - Capture, process, and manage training data
├── training  - Train, evaluate, and deploy models
└── system    - Setup utilities and hardware calibration
```

## Installation

The CLI is included with DonkeyCar. Install it with:

```bash
pip install donkeycar
```

Or run it directly from the repository:

```bash
python -m donkeycar.cli --help
```

## Quick Start

### 1. Create a Car Project

```bash
# Create a new car with default template
donkey car create --path mycar

# Or use advanced template
donkey car create --path mycar --template advanced
```

### 2. Configure Your Car Hardware

```bash
# Interactive configuration wizard
donkey car configure --car-path mycar

# View current configuration
donkey car info --car-path mycar
```

### 3. Record Training Data

```bash
# Start recording a dataset
donkey data record --car-path mycar --duration 300 --name dataset_001

# Analyze recorded data
donkey data analyze --data-dir mycar/data/dataset_001
```

### 4. Train a Model

```bash
# Train a model on your data
donkey training train \
  --car-path mycar \
  --data-dir mycar/data/dataset_001 \
  --model-name model_v1 \
  --epochs 100

# Evaluate model performance
donkey training evaluate \
  --car-path mycar \
  --model model_v1 \
  --data-dir mycar/data/dataset_001

# Deploy model to car
donkey training deploy --car-path mycar --model model_v1
```

## Command Structure

### CAR Commands

```bash
donkey car create       # Create a new car project
donkey car configure    # Configure hardware (steering, throttle, buttons)
donkey car info         # Display car configuration
```

**Example Workflow:**

```bash
# New car setup
donkey car create --path mycar
donkey car configure --car-path mycar
donkey car info --car-path mycar
```

### DATA Commands

```bash
donkey data record      # Start recording training data
donkey data convert     # Convert data between formats (v2, TFLite, CSV)
donkey data analyze     # Show dataset statistics
donkey data visualize   # View sample frames with control inputs
```

**Example Workflow:**

```bash
# Data management
donkey data record --car-path mycar --name session_001
donkey data analyze --data-dir mycar/data/session_001
donkey data convert --source mycar/data/session_001 --format v2
```

### TRAINING Commands

```bash
donkey training train    # Train a neural network model
donkey training evaluate # Evaluate model performance
donkey training convert  # Convert TensorFlow to TFLite
donkey training deploy   # Deploy model to a car
```

**Example Workflow:**

```bash
# Training pipeline
donkey training train \
  --car-path mycar \
  --data-dir mycar/data/session_001 \
  --epochs 100

donkey training evaluate \
  --car-path mycar \
  --model model_v1 \
  --data-dir mycar/data/session_001

donkey training convert --model mycar/models/model_v1.h5
donkey training deploy --car-path mycar --model model_v1
```

### SYSTEM Commands

```bash
donkey system check      # Verify environment and dependencies
donkey system install    # Install/update dependencies
donkey system update     # Update CLI from GitHub main branch
donkey system calibrate  # Interactive hardware calibration
donkey system info       # Display system information
donkey system completion # Generate shell completion
```

**Example Workflow:**

```bash
# Setup new system
donkey system check
donkey system install
donkey system calibrate --device joystick

# Update to latest version
donkey system update
```

## Project Structure

A typical DonkeyCar project created with the CLI has this structure:

```
mycar/
├── config/
│   └── car_config.py       # Base car configuration
├── myconfig.py             # Local configuration overrides
├── models/                 # Trained models
│   ├── model_v1.h5
│   └── model_v1.tflite
├── data/                   # Training datasets
│   ├── session_001/
│   ├── session_002/
│   └── ...
└── logs/                   # Training logs
    ├── training_001.log
    └── ...
```

## Configuration Management

Each car has two configuration layers:

1. **car_config.py** - Base configuration for hardware and behavior
2. **myconfig.py** - Local overrides (specific to your car instance)

Edit `myconfig.py` to customize settings:

```python
# myconfig.py
from config.car_config import *

# Override specific settings
STEERING_INVERTED = True
MAX_THROTTLE = 0.5
CAMERA_WIDTH = 320
```

## Advanced Usage

### Running the CLI from Different Directories

The CLI can be run from any directory and will auto-detect local cars:

```bash
cd /path/to/donkeycar
donkey car info              # Shows all local cars
donkey data record mycar     # Records to mycar/data
```

### Multiple Car Management

Manage multiple cars in one project:

```bash
donkey car create --path car1
donkey car create --path car2

donkey data record --car-path car1 --name dataset_001
donkey data record --car-path car2 --name dataset_001

# Train separate models
donkey training train --car-path car1 --data-dir car1/data/dataset_001
donkey training train --car-path car2 --data-dir car2/data/dataset_001
```

### Data Organization

Organize datasets by experiment:

```bash
mycar/
├── data/
│   ├── baseline/           # Baseline training data
│   ├── improved/           # Improved driving technique
│   ├── edge_cases/         # Edge cases and failures
│   └── augmented/          # Augmented dataset
```

## Environment Variables

Configure CLI behavior with environment variables:

```bash
# Set verbosity
export DONKEY_DEBUG=1
donkey system check

# Set default car directory
export DONKEY_CAR_PATH=/path/to/mycar
donkey data record

# Set data directory
export DONKEY_DATA_PATH=/external/ssd/data
donkey data record
```

## Integration with Existing Scripts

The CLI integrates with existing DonkeyCar scripts:

- **configure_joystick.py** → `donkey car configure`
- **setup_mycar.py** → `donkey car create`
- **multi_train.py** → `donkey training train`
- **convert_to_tflite.py** → `donkey training convert`

## Troubleshooting

### CLI not found

```bash
# Install click dependency
pip install click

# Or install full requirements
pip install -r requirements.txt
```

### Permission denied (Linux/Mac)

```bash
# Make script executable
chmod +x /path/to/donkey

# Or run with python
python -m donkeycar.cli --help
```

### Missing dependencies

```bash
# Run system check
donkey system check

# Install missing packages
donkey system install
```

## Updating the CLI

The CLI can be easily updated to the latest version from GitHub:

```bash
# Update to latest main branch
donkey system update

# This will:
# 1. Fetch latest changes from GitHub
# 2. Switch to main branch
# 3. Pull latest code
# 4. Reinstall with pip install -e .
```

### Manual Update

If you're not in a git repository or prefer manual updates:

```bash
# Navigate to your donkeycar directory
cd /path/to/donkeycar

# Fetch latest changes
git fetch origin

# Switch to main branch
git checkout main

# Pull latest code
git pull origin main

# Reinstall
pip install -e .
```

### Alternative: Upgrade via pip

If DonkeyCar is installed from PyPI:

```bash
pip install --upgrade donkeycar
```

## Future Enhancements

Planned features for the CLI:

- [ ] Remote car management (SSH, VPN)
- [ ] Cloud data upload/sync
- [ ] Automated training pipelines
- [ ] Model versioning and rollback
- [ ] Performance monitoring dashboard
- [ ] Integration with MLflow/Weights & Biases
- [ ] WebUI for configuration
- [ ] Docker integration

## Contributing

To extend the CLI with new commands:

1. Add a new module in `donkeycar/cli/commands/`
2. Create a Click command group
3. Import and register in `donkeycar/cli/core.py`

Example new command:

```python
# donkeycar/cli/commands/cloud.py
import click

@click.group()
def cloud():
    """Cloud integration commands."""
    pass

@cloud.command()
def upload():
    """Upload data to cloud storage."""
    click.echo("Uploading data...")

# Then in core.py:
from .commands import cloud
cli.add_command(cloud.cloud)
```

## Support

For issues or questions:

- GitHub Issues: https://github.com/prometheusgr/donkeycar/issues
- Documentation: https://docs.donkeycar.com
- Community: https://donkeycar.com
