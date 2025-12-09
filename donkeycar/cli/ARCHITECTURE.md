# DonkeyCar CLI - Architecture & Organization

## Project Organization Overview

The new organized CLI structure divides the DonkeyCar project into three main categories plus system utilities:

```
donkeycar/
├── cli/                          # ← NEW: Unified CLI interface
│   ├── commands/                 # Command implementations
│   │   ├── car.py               # Car management
│   │   ├── data.py              # Data management
│   │   ├── training.py          # Model training
│   │   └── system.py            # System utilities
│   ├── utils/                    # Shared utilities
│   │   ├── project.py           # Project discovery
│   │   ├── config.py            # Configuration management
│   │   └── data.py              # Data utilities
│   ├── core.py                  # CLI framework
│   ├── __init__.py              # Package exports
│   ├── __main__.py              # Module entry point
│   ├── README.md                # User guide
│   └── DEVELOPMENT.md           # Developer guide
│
├── [legacy modules]             # Existing DonkeyCar code
├── templates/                   # Car templates
├── parts/                       # Vehicle components
├── management/                  # Existing management tools
└── ...
```

## Three Main Categories

### 1. CAR 🚗

**Purpose:** Create and manage car instances and hardware configurations

**Commands:**

- `donkey car create` - Create new car project
- `donkey car configure` - Configure hardware (steering, throttle, buttons)
- `donkey car info` - Display car configuration

**What It Does:**

```
Create:     Generates project structure with config directories
Configure:  Interactive hardware calibration wizard
Info:       Shows current settings and project structure
```

**Example Project Structure:**

```
mycar/
├── config/
│   └── car_config.py       # Base hardware config
├── myconfig.py             # Local overrides
├── models/                 # Trained models
├── data/                   # Training datasets
└── logs/                   # Training logs
```

---

### 2. DATA 📊

**Purpose:** Record, manage, and process training datasets

**Commands:**

- `donkey data record` - Start recording training data
- `donkey data analyze` - Show dataset statistics
- `donkey data visualize` - View sample frames
- `donkey data convert` - Convert between formats (TUB v2, TFLite, CSV)

**What It Does:**

```
Record:    Captures camera frames and control inputs
Analyze:   Shows frame counts and distributions
Visualize: Displays images with control values
Convert:   Transforms between data formats
```

**Data Organization:**

```
mycar/data/
├── session_001/
│   ├── manifest.json
│   ├── 0/
│   │   ├── image_array.npy
│   │   ├── image.jpg
│   │   └── ...
│   └── ...
├── session_002/
└── ...
```

---

### 3. TRAINING 🤖

**Purpose:** Train, evaluate, and deploy machine learning models

**Commands:**

- `donkey training train` - Train neural network model
- `donkey training evaluate` - Evaluate model performance
- `donkey training convert` - Convert to TFLite format
- `donkey training deploy` - Deploy model to car

**What It Does:**

```
Train:     Builds model from training data with augmentation
Evaluate:  Tests model on validation data
Convert:   Optimizes for mobile/edge deployment
Deploy:    Copies model to car's model directory
```

**Model Pipeline:**

```
Training Data
    ↓
  Train (TensorFlow/Keras)
    ↓
model_v1.h5 (250MB)
    ↓
  Convert (TFLite Quantization)
    ↓
model_v1.tflite (10MB)
    ↓
  Deploy
    ↓
Car Ready for Inference
```

---

### 4. SYSTEM ⚙️

**Purpose:** Environment setup, validation, and hardware calibration

**Commands:**

- `donkey system check` - Verify Python and dependencies
- `donkey system install` - Install required packages
- `donkey system calibrate` - Interactive hardware calibration
- `donkey system info` - Display system information

**What It Does:**

```
Check:     Validates Python version and packages
Install:   Sets up dependencies from requirements.txt
Calibrate: Guides through joystick/camera/motor setup
Info:      Shows DonkeyCar version and environment
```

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                  User CLI Interface                     │
│  donkey car create | donkey data record | ...           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Command Groups (Click)                     │
│  car.py | data.py | training.py | system.py           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           Utility Layer (Shared Logic)                  │
│  project.py | config.py | data.py                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│         DonkeyCar Core & Dependencies                   │
│  Vehicle | Parts | Training | Utils                    │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Creating and Training a Car

```
┌──────────────────────────────────────────────────────────┐
│ 1. CREATE CAR                                            │
│    donkey car create --path mycar                        │
│    └→ Creates directory structure                        │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 2. CONFIGURE HARDWARE                                    │
│    donkey car configure --car-path mycar                 │
│    └→ Sets STEERING_AXIS, THROTTLE_AXIS, etc.          │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 3. RECORD DATA                                           │
│    donkey data record --car-path mycar                   │
│    └→ Saves images + telemetry to mycar/data/           │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 4. ANALYZE DATA                                          │
│    donkey data analyze --data-dir mycar/data/session_001 │
│    └→ Shows statistics: frame count, distributions      │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 5. TRAIN MODEL                                           │
│    donkey training train --car-path mycar ...            │
│    └→ Uses TensorFlow/Keras with augmentation           │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 6. EVALUATE MODEL                                        │
│    donkey training evaluate --car-path mycar ...         │
│    └→ Tests on validation set, shows metrics            │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ 7. CONVERT & DEPLOY                                      │
│    donkey training convert --model mycar/models/...      │
│    donkey training deploy --car-path mycar ...           │
│    └→ Model ready on car for inference                  │
└──────────────────────────────────────────────────────────┘
```

## Key Features

### Organized by Workflow

- **Car**: Setup and configuration
- **Data**: Collection and management
- **Training**: Model development
- **System**: Infrastructure

### Project Discovery

The CLI auto-discovers:

- Car directories (with `myconfig.py` or `config/car_config.py`)
- Dataset directories (in `mycar/data/`)
- Model files (in `mycar/models/`)

### Configuration Layers

```
Environment Variables
        ↓
Project Configuration Files
        ↓
Command-Line Arguments
        ↓
Defaults
```

### Cross-Platform

- Works on Linux, macOS, Windows
- Uses pathlib for path handling
- Click for portable CLI

---

## Integration Points

The CLI integrates with existing DonkeyCar components:

```
CLI Commands          Existing Modules
────────────────────────────────────────
car create      →     templates/
car configure   →     parts/joystick
data record     →     parts/camera, vehicle
data convert    →     utilities/tub
training train  →     pipeline/training
system check    →     management/utils
```

---

## Extensibility

### Adding New Command Categories

Example: Add "simulation" commands

```python
# donkeycar/cli/commands/simulation.py
@click.group()
def simulation():
    """Simulation and testing commands."""
    pass

@simulation.command()
def create_sim():
    """Create simulation environment."""
    pass

# Register in core.py
from .commands import simulation
cli.add_command(simulation.simulation)

# Usage: donkey simulation create-sim
```

### Plugin Architecture (Future)

```python
# Load external commands
for plugin in discover_plugins():
    cli.add_command(plugin.get_command())
```

---

## Performance & Scalability

### Local Performance

- Fast command startup (lazy imports)
- Efficient project discovery
- Concurrent data processing

### Scalability Features

- Multiple car management
- Large dataset handling (with proper TUB format)
- Distributed training support (via TensorFlow)

---

## Backward Compatibility

The CLI is **additive** - existing workflows continue to work:

```bash
# Old way still works
python scripts/setup_mycar.py
python mycar/manage.py drive
python mycar/train.py

# New way
donkey car create --path mycar
donkey data record --car-path mycar
donkey training train --car-path mycar ...
```

The old `donkey` command is renamed to `donkey-legacy`:

```bash
donkey-legacy --help  # Old management interface
donkey --help         # New organized CLI
```

---

## Documentation

- **User Guide**: `donkeycar/cli/README.md`
- **Developer Guide**: `donkeycar/cli/DEVELOPMENT.md`
- **Migration Guide**: `MIGRATION.md`
- **Examples**: `EXAMPLES.md`

---

## Summary

The organized CLI structure provides:

✅ **Clear Organization** - Three main categories + system utilities
✅ **Easy to Use** - Intuitive command hierarchy
✅ **Extensible** - Add new commands easily
✅ **Documented** - Comprehensive guides and examples
✅ **Backward Compatible** - Existing workflows still work
✅ **Cross-Platform** - Works on all major OSs
✅ **Discoverable** - Auto-finds cars, datasets, models
✅ **Professional** - Click-based with rich output

This design makes DonkeyCar more approachable for new users while remaining powerful for advanced users.
