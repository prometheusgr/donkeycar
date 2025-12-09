"""
DonkeyCar CLI - Quick Examples

This file demonstrates common workflows using the organized CLI.
Run these commands from your donkeycar project directory.
"""

# ============================================================================

# GETTING STARTED - Your First Car

# ============================================================================

"""

# Step 1: Create a new car project

donkey car create --path mycar

# Step 2: Configure your car's hardware (steering, throttle, buttons)

donkey car configure --car-path mycar

# Step 3: View your car's configuration

donkey car info --car-path mycar

Expected output:
Car Configuration: /path/to/mycar
============================================================

Directory Structure:
📁 config/ (2 items)
📁 models/ (0 items)
📁 data/ (0 items)
📁 logs/ (0 items)
📄 myconfig.py

Configuration (/path/to/mycar/myconfig.py): # Auto-generated car configuration
JOYSTICK_DEVICE_FILE = '/dev/input/js0'
STEERING_AXIS = 0
...
"""

# ============================================================================

# DATA MANAGEMENT - Recording and Processing

# ============================================================================

"""

# Record training data from your car

donkey data record --car-path mycar --duration 300 --name session_001

# Analyze your recorded data

donkey data analyze --data-dir mycar/data/session_001

# View sample frames from your data

donkey data visualize --data-dir mycar/data/session_001 --sample 0

# Convert data to different formats

donkey data convert --source mycar/data/session_001 --format v2 --output mycar/data/session_001_v2

Expected workflow:
$ donkey data record --car-path mycar
Recording to: /path/to/mycar/data/dataset_20250108_143022
Duration: 300 seconds
Press Ctrl+C to stop recording

$ donkey data analyze --data-dir mycar/data/dataset_20250108_143022
Analyzing: /path/to/mycar/data/dataset_20250108_143022

Dataset Statistics:
Total frames: 1250
Steering distribution: mostly center with some left turns
Throttle distribution: mostly forward
"""

# ============================================================================

# TRAINING - Build Your Model

# ============================================================================

"""

# Train a model on your collected data

donkey training train \
 --car-path mycar \
 --data-dir mycar/data/session_001 \
 --model-name model_v1 \
 --epochs 100 \
 --batch-size 32

# Evaluate your trained model

donkey training evaluate \
 --car-path mycar \
 --model model_v1 \
 --data-dir mycar/data/session_001

# Convert model for mobile/edge deployment

donkey training convert \
 --model mycar/models/model_v1.h5 \
 --output mycar/models/model_v1.tflite \
 --quantize

# Deploy model to your car

donkey training deploy \
 --car-path mycar \
 --model model_v1

# Expected output:

# DonkeyCar Model Training

Configuration:
Car: /path/to/mycar
Data: /path/to/mycar/data/session_001
Model: model_v1
Epochs: 100
Batch size: 32
Augmentation: enabled

Training ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░ 45% |

✓ Training complete!
Model saved to: /path/to/mycar/models/model_v1.h5
"""

# ============================================================================

# SYSTEM SETUP - Environment and Hardware

# ============================================================================

"""

# Check your system environment

donkey system check

# Install DonkeyCar dependencies

donkey system install

# Calibrate hardware (joystick, camera, motor)

donkey system calibrate

# Get system information

donkey system info

# Update to latest version from GitHub

donkey system update

Expected output from 'donkey system check':
System Environment Check
============================================================

Python Version: 3.11.6 (main, Dec 3 2024, 10:35:31)
✓ Python 3.11+ detected

Installed Packages:
✓ donkeycar: 5.2.dev5
✓ tensorflow: 2.15.0
✓ numpy: 1.24.3
✓ opencv-python: 4.8.1
✓ click: 8.1.7
✓ pillow: 10.0.0

Expected output from 'donkey system update':
DonkeyCar Update
============================================================

Current Branch: main
Git Directory: .git

Update DonkeyCar from main branch? [Y/n]: y

Fetching latest changes...
Checking out main branch...
Pulling latest changes...
Reinstalling DonkeyCar...
✓ Update complete! Version: 5.2.dev5
"""

# ============================================================================

# MULTIPLE CARS - Managing Multiple Vehicles

# ============================================================================

"""

# Create multiple cars for different purposes

donkey car create --path car_red # Main racing car
donkey car create --path car_blue # Backup car
donkey car create --path car_test # Testing/experimentation

# Configure each separately

donkey car configure --car-path car_red
donkey car configure --car-path car_blue
donkey car configure --car-path car_test

# Collect data from each car

donkey data record --car-path car_red --name baseline
donkey data record --car-path car_blue --name baseline
donkey data record --car-path car_test --name experiment_001

# Train separate models

donkey training train --car-path car_red --data-dir car_red/data/baseline
donkey training train --car-path car_blue --data-dir car_blue/data/baseline
donkey training train --car-path car_test --data-dir car_test/data/experiment_001

# Deploy to each car

donkey training deploy --car-path car_red --model model_red_v1
donkey training deploy --car-path car_blue --model model_blue_v1
donkey training deploy --car-path car_test --model model_experimental
"""

# ============================================================================

# ORGANIZING DATASETS - Structured Data Management

# ============================================================================

"""

# Create organized dataset structure

mycar/data/
├── baseline/ # Baseline driving
│ ├── session_001/
│ ├── session_002/
│ └── session_003/
├── improved/ # Improved techniques
│ ├── smooth_001/
│ └── smooth_002/
├── edge_cases/ # Challenging scenarios
│ ├── tight_corners/
│ ├── intersections/
│ └── obstacles/
└── augmented/ # Synthetic data
└── augmented_v1/

# Record into organized structure

donkey data record --car-path mycar --name baseline/session_001
donkey data record --car-path mycar --name baseline/session_002
donkey data record --car-path mycar --name improved/smooth_001

# Train on specific datasets

donkey training train --car-path mycar --data-dir mycar/data/baseline --model baseline_v1
donkey training train --car-path mycar --data-dir mycar/data/improved --model improved_v1

# Combine datasets for better model

# (Future: donkey data merge)

"""

# ============================================================================

# QUICK COMMANDS REFERENCE

# ============================================================================

"""
┌─ HELP ─────────────────────────────────────────────────────────┐
│ donkey --help # Show all available commands │
│ donkey <group> --help # Show group commands │
│ donkey <group> <cmd> --help # Show command details │
└────────────────────────────────────────────────────────────────┘

┌─ CAR ──────────────────────────────────────────────────────────┐
│ donkey car create --path mycar │
│ donkey car configure --car-path mycar │
│ donkey car info --car-path mycar │
└────────────────────────────────────────────────────────────────┘

┌─ DATA ─────────────────────────────────────────────────────────┐
│ donkey data record --car-path mycar --duration 300 │
│ donkey data analyze --data-dir mycar/data/dataset │
│ donkey data visualize --data-dir mycar/data/dataset │
│ donkey data convert --source ... --format v2 │
└────────────────────────────────────────────────────────────────┘

┌─ TRAINING ─────────────────────────────────────────────────────┐
│ donkey training train --car-path mycar --data-dir ... │
│ donkey training evaluate --car-path mycar --model ... │
│ donkey training convert --model mycar/models/model.h5 │
│ donkey training deploy --car-path mycar --model ... │
└────────────────────────────────────────────────────────────────┘

┌─ SYSTEM ───────────────────────────────────────────────────────┐
│ donkey system check # Verify environment │
│ donkey system install # Install dependencies │
│ donkey system update # Update from GitHub │
│ donkey system calibrate # Calibrate hardware │
│ donkey system info # Show system info │
└────────────────────────────────────────────────────────────────┘
"""

# ============================================================================

# ENVIRONMENT VARIABLES - Customize Behavior

# ============================================================================

"""

# Set default car path

export DONKEY_CAR_PATH=$HOME/mycar
donkey data record # Uses DONKEY_CAR_PATH

# Set data directory (for large SSD)

export DONKEY_DATA_PATH=/media/ssd/donkeycar_data
donkey data record --car-path mycar # Saves to DONKEY_DATA_PATH

# Enable debug output

export DONKEY_DEBUG=1
donkey system check # Shows detailed debug info

# Set model directory

export DONKEY_MODELS_PATH=/models
donkey training train --car-path mycar --data-dir ...
"""

# ============================================================================

# AUTOMATION - Scripts Using CLI

# ============================================================================

"""

# Shell script for complete workflow

#!/bin/bash

CAR*NAME="mycar"
DATA_NAME="$(date +%Y%m%d*%H%M%S)"

# Create and configure car

donkey car create --path "$CAR_NAME"
donkey car configure --car-path "$CAR_NAME"

# Record multiple sessions

donkey data record --car-path "$CAR_NAME" --name "session_1" --duration 300
donkey data record --car-path "$CAR_NAME" --name "session_2" --duration 300
donkey data record --car-path "$CAR_NAME" --name "session_3" --duration 300

# Train and evaluate

for epoch in 50 100 150; do
MODEL_NAME="model_e${epoch}"

donkey training train \\
--car-path "$CAR_NAME" \\
    --data-dir "$CAR_NAME/data/session_1" \\
--model-name "$MODEL_NAME" \\
    --epochs "$epoch"

donkey training evaluate \\
--car-path "$CAR_NAME" \\
    --model "$MODEL_NAME" \\
--data-dir "$CAR_NAME/data/session_2"
done

# Deploy best model

donkey training deploy --car-path "$CAR_NAME" --model model_e100
"""

# ============================================================================

# TROUBLESHOOTING

# ============================================================================

"""
Q: Command not found: donkey
A: Install with: pip install donkeycar
Or run with: python -m donkeycar.cli --help

Q: Click not installed
A: Install with: pip install click>=8.0

Q: Permission denied (Linux/Mac)
A: Use: python -m donkeycar.cli <command>

Q: Environment variables not working
A: Make sure they're exported:
export DONKEY_CAR_PATH=$HOME/mycar

Q: Configuration not being read
A: Check myconfig.py exists:
donkey car info --car-path mycar
"""
