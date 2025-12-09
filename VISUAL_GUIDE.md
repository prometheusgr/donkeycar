# DonkeyCar CLI - Visual Guide

## Organization Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DONKEYCAR CLI                                 │
│                    (unified command interface)                       │
└────────────────┬──────────────────────────────────┬──────────────────┘
                 │                                  │
        ┌────────▼─────────┐          ┌────────────▼────────────┐
        │   CAR COMMANDS   │          │  TRAINING COMMANDS      │
        ├──────────────────┤          ├─────────────────────────┤
        │ • car create     │          │ • training train        │
        │ • car configure  │          │ • training evaluate     │
        │ • car info       │          │ • training convert      │
        └────────┬─────────┘          │ • training deploy       │
                 │                    └──────────┬──────────────┘
        ┌────────▼──────────┐                    │
        │  DATA COMMANDS    │                    │
        ├───────────────────┤                    │
        │ • data record     │                    │
        │ • data analyze    │         ┌──────────▼──────────┐
        │ • data visualize  │         │ SYSTEM COMMANDS     │
        │ • data convert    │         ├─────────────────────┤
        └────────┬──────────┘         │ • system check      │
                 │                    │ • system install    │
                 │                    │ • system calibrate  │
                 │                    │ • system info       │
                 │                    └────────┬────────────┘
                 │                             │
                 └─────────────┬───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Shared Utilities   │
                    ├────────────────────┤
                    │ • Project discovery │
                    │ • Configuration    │
                    │ • Data management  │
                    └────────────────────┘
```

## Workflow Diagram

```
┌─────────────┐
│ START HERE  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ 1. CREATE CAR            │
│ donkey car create        │
│ --path mycar             │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 2. CONFIGURE HARDWARE    │
│ donkey car configure     │
│ --car-path mycar         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 3. RECORD DATA           │
│ donkey data record       │
│ --car-path mycar         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 4. ANALYZE DATA          │
│ donkey data analyze      │
│ --data-dir ...           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 5. TRAIN MODEL           │
│ donkey training train    │
│ --car-path mycar --...   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 6. EVALUATE MODEL        │
│ donkey training evaluate │
│ --car-path mycar --...   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 7. CONVERT & DEPLOY      │
│ donkey training convert  │
│ donkey training deploy   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ READY FOR TESTING        │
│ Deploy to car & drive    │
└──────────────────────────┘
```

## Car Project Structure

```
mycar/                          ← Your car project
│
├── config/                     ← Configuration directory
│   └── car_config.py          ← Base hardware config
│                                 (created by CLI)
│
├── myconfig.py                 ← Your local settings
│                                 (edit this to customize)
│
├── models/                     ← Trained models
│   ├── model_v1.h5
│   ├── model_v1.tflite
│   └── ...
│
├── data/                       ← Training data
│   ├── session_001/            ← Dataset 1
│   │   ├── manifest.json
│   │   ├── 0/
│   │   │   ├── image_array.npy
│   │   │   └── image.jpg
│   │   ├── 1/
│   │   └── ...
│   ├── session_002/            ← Dataset 2
│   └── ...
│
└── logs/                       ← Training logs
    ├── training_v1.log
    └── ...
```

## Command Categories

### 🚗 CAR - Create & Configure

```
donkey car create
├─ Creates directory structure
├─ Generates configuration templates
└─ Sets up config/ folder

donkey car configure
├─ Asks about steering axis
├─ Asks about throttle axis
├─ Asks about buttons
└─ Writes myconfig.py

donkey car info
├─ Shows directory structure
├─ Shows file counts
└─ Displays current config
```

### 📊 DATA - Record & Analyze

```
donkey data record
├─ Records camera frames
├─ Records steering inputs
├─ Records throttle inputs
└─ Saves to mycar/data/

donkey data analyze
├─ Counts frames
├─ Shows distributions
└─ Generates statistics

donkey data visualize
├─ Displays images
├─ Shows control values
└─ Allows frame browsing

donkey data convert
├─ TUB v1 → v2
├─ TensorFlow → TFLite
└─ → CSV export
```

### 🤖 TRAINING - Learn & Deploy

```
donkey training train
├─ Loads training data
├─ Applies augmentation
├─ Trains neural network
└─ Saves model.h5

donkey training evaluate
├─ Loads trained model
├─ Tests on new data
├─ Shows accuracy metrics
└─ Generates plots

donkey training convert
├─ Reads TensorFlow model
├─ Applies quantization
└─ Saves model.tflite

donkey training deploy
├─ Copies model to car
├─ Updates car config
└─ Ready for inference
```

### ⚙️ SYSTEM - Setup & Validate

```
donkey system check
├─ Verifies Python version
├─ Checks installed packages
├─ Validates dependencies
└─ Shows environment info

donkey system install
├─ Reads requirements.txt
├─ Installs packages
└─ Updates existing packages

donkey system calibrate
├─ Joystick setup
├─ Camera alignment
├─ Motor calibration
└─ Steering/throttle range

donkey system info
├─ Shows DonkeyCar version
├─ Lists local cars
├─ Lists datasets
└─ Shows Python version
```

## Command Options Reference

```
┌─ Common Options ─────────────────────────┐
│ --help              Show command help    │
│ --version           Show CLI version     │
│ --verbose           More detailed output │
│ --quiet             Less output          │
└──────────────────────────────────────────┘

┌─ Car Options ────────────────────────────┐
│ --path              Car location         │
│ --car-path          Car location         │
│ --template          Car template         │
└──────────────────────────────────────────┘

┌─ Data Options ───────────────────────────┐
│ --data-dir          Dataset location     │
│ --duration          Recording time (sec) │
│ --name              Dataset name         │
│ --format            Output format        │
│ --output            Output location      │
└──────────────────────────────────────────┘

┌─ Training Options ───────────────────────┐
│ --model-name        Model name           │
│ --model             Model file/name      │
│ --epochs            Training iterations  │
│ --batch-size        Batch size           │
│ --augment           Enable augmentation  │
│ --quantize          Enable quantization  │
└──────────────────────────────────────────┘

┌─ System Options ─────────────────────────┐
│ --device            Device to calibrate  │
│ --format            Completion format    │
└──────────────────────────────────────────┘
```

## File Organization During Development

```
donkeycar/                          Project root
│
├── donkeycar/cli/                 ← CLI MODULE (NEW!)
│   ├── __init__.py                ← Package entry
│   ├── core.py                    ← Main CLI app
│   ├── commands/
│   │   ├── car.py                 ← Car commands
│   │   ├── data.py                ← Data commands
│   │   ├── training.py            ← Training commands
│   │   └── system.py              ← System commands
│   ├── utils/
│   │   ├── project.py             ← Project discovery
│   │   ├── config.py              ← Config loading
│   │   └── data.py                ← Data utilities
│   ├── README.md                  ← User guide
│   ├── DEVELOPMENT.md             ← Dev guide
│   └── ARCHITECTURE.md            ← Architecture
│
├── setup.cfg                       ← Updated: entry points
├── README.md                       ← Updated: CLI reference
├── QUICKSTART.md                  ← NEW: Quick start
├── EXAMPLES.md                    ← NEW: Examples
├── MIGRATION.md                   ← NEW: Migration guide
└── CLI_SUMMARY.md                 ← NEW: This summary
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ DONKEYCAR CLI QUICK REFERENCE                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ CREATE CAR                                              │
│ $ donkey car create --path mycar                        │
│                                                         │
│ CONFIGURE                                               │
│ $ donkey car configure --car-path mycar                 │
│                                                         │
│ RECORD DATA                                             │
│ $ donkey data record --car-path mycar                   │
│                                                         │
│ ANALYZE DATA                                            │
│ $ donkey data analyze --data-dir mycar/data/session_001 │
│                                                         │
│ TRAIN MODEL                                             │
│ $ donkey training train --car-path mycar \              │
│   --data-dir mycar/data/session_001 --epochs 100        │
│                                                         │
│ EVALUATE MODEL                                          │
│ $ donkey training evaluate --car-path mycar \           │
│   --model model_v1 --data-dir mycar/data/session_001    │
│                                                         │
│ DEPLOY TO CAR                                           │
│ $ donkey training deploy --car-path mycar \             │
│   --model model_v1                                      │
│                                                         │
│ HELP                                                    │
│ $ donkey --help                    (all commands)       │
│ $ donkey car --help                (car commands)       │
│ $ donkey car create --help         (create help)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting Decision Tree

```
Problem: Command not found
├─ Is Click installed?
│  └─ pip install click>=8.0
│
└─ Is DonkeyCar installed?
   └─ pip install -e /path/to/donkeycar

Problem: Configuration error
├─ Did you run car configure?
│  └─ donkey car configure --car-path mycar
│
└─ Check myconfig.py syntax
   └─ donkey car info --car-path mycar

Problem: Data not found
├─ Did you record data?
│  └─ donkey data record --car-path mycar
│
└─ Check data directory
   └─ donkey data analyze --data-dir mycar/data

Problem: Training failed
├─ Do you have training data?
│  └─ donkey data record --car-path mycar
│
├─ Are dependencies installed?
│  └─ donkey system check
│
└─ Check command syntax
   └─ donkey training train --help
```

## Next Steps

1. **Quick Start (5 min)**
   ```
   cat QUICKSTART.md
   ```

2. **Full Guide (30 min)**
   ```
   cat donkeycar/cli/README.md
   ```

3. **Examples (15 min)**
   ```
   cat EXAMPLES.md
   ```

4. **Start Using**
   ```
   donkey car create --path mycar
   ```

---

**Print this page or save as reference!**
