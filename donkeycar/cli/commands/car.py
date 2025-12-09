"""
Car management commands.

Handles:
- Creating new car projects
- Configuring car hardware (steering, throttle, buttons)
- Managing car configurations
- Running car applications
"""

import click
from pathlib import Path
import shutil
from datetime import datetime


def _backup_file(path: Path):
    """Backup a file with timestamp."""
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = path.with_name(f"{path.name}.{ts}.bak")
        path.rename(backup)
        return backup
    return None


@click.group()
def car():
    """
    Manage car instances and configurations.

    Create new cars, configure hardware, and manage car-specific settings.
    """
    pass


@car.command()
@click.option('--path', type=click.Path(), default='mycar',
              help='Path where car will be created (default: mycar)')
@click.option('--template', type=click.Choice(['basic', 'advanced']), default='basic',
              help='Car template to use')
def create(path, template):
    """
    Create a new car project.

    Sets up a new car directory with template configuration files.
    """
    car_path = Path(path).resolve()

    click.echo(f"Creating car project at: {car_path}")

    if car_path.exists():
        if click.confirm(f"{car_path} already exists. Overwrite?", default=False):
            shutil.rmtree(car_path)
        else:
            click.echo("Cancelled.")
            return

    # Create directory structure
    car_path.mkdir(parents=True, exist_ok=True)
    (car_path / 'config').mkdir(exist_ok=True)
    (car_path / 'models').mkdir(exist_ok=True)
    (car_path / 'data').mkdir(exist_ok=True)
    (car_path / 'logs').mkdir(exist_ok=True)

    # Create basic config files
    config_file = car_path / 'config' / 'car_config.py'
    if not config_file.exists():
        config_file.write_text(_default_car_config(template))
        click.echo(f"✓ Created config file: {config_file}")

    myconfig_file = car_path / 'myconfig.py'
    if not myconfig_file.exists():
        myconfig_file.write_text(_default_myconfig())
        click.echo(f"✓ Created myconfig file: {myconfig_file}")

    click.echo(f"\n✓ Car project created successfully!")
    click.echo(
        f"  Edit {car_path}/myconfig.py to configure your car settings.")


@car.command()
@click.option('--car-path', type=click.Path(exists=True), default='mycar',
              help='Path to car project (default: mycar)')
def configure(car_path):
    """
    Interactively configure car hardware.

    Sets up steering/throttle axes, buttons, and calibration values.
    """
    car_path = Path(car_path).resolve()

    click.echo(f"Configuring car at: {car_path}")
    click.echo("\nHardware Configuration:")

    # Steering configuration
    steering_axis = click.prompt("Steering axis code", type=int, default=0)
    steering_inverted = click.confirm("Invert steering?", default=False)

    # Throttle configuration
    throttle_axis = click.prompt("Throttle axis code", type=int, default=1)
    throttle_inverted = click.confirm("Invert throttle?", default=False)

    # Button configuration
    record_button = click.prompt(
        "Record button code (or -1 to skip)", type=int, default=-1)
    mode_button = click.prompt(
        "Mode button code (or -1 to skip)", type=int, default=-1)

    config = {
        'STEERING_AXIS': steering_axis,
        'STEERING_INVERTED': steering_inverted,
        'THROTTLE_AXIS': throttle_axis,
        'THROTTLE_INVERTED': throttle_inverted,
        'RECORD_BUTTON': record_button if record_button >= 0 else None,
        'MODE_BUTTON': mode_button if mode_button >= 0 else None,
    }

    # Write configuration
    myconfig_path = car_path / 'myconfig.py'
    _backup_file(myconfig_path)

    config_text = "# Auto-generated car configuration\n\n"
    for key, value in config.items():
        if value is not None:
            config_text += f"{key} = {repr(value)}\n"

    myconfig_path.write_text(config_text)
    click.echo(f"✓ Configuration saved to: {myconfig_path}")


@car.command()
@click.option('--car-path', type=click.Path(exists=True), default='mycar',
              help='Path to car project (default: mycar)')
def info(car_path):
    """
    Display car configuration information.

    Shows the current settings and status of a car project.
    """
    car_path = Path(car_path).resolve()

    click.echo(f"Car Configuration: {car_path}")
    click.echo("=" * 60)

    if not car_path.exists():
        click.echo(f"Error: Car directory not found: {car_path}", err=True)
        return

    # Show directory structure
    click.echo("\nDirectory Structure:")
    for subdir in sorted(car_path.iterdir()):
        if subdir.is_dir():
            file_count = len(list(subdir.glob('*')))
            click.echo(f"  📁 {subdir.name}/ ({file_count} items)")
        else:
            click.echo(f"  📄 {subdir.name}")

    # Show configuration
    myconfig = car_path / 'myconfig.py'
    if myconfig.exists():
        click.echo(f"\nConfiguration ({myconfig}):")
        click.echo(myconfig.read_text())
    else:
        click.echo(f"\nNo configuration found at {myconfig}")


def _default_car_config(template: str = 'basic') -> str:
    """Generate default car configuration."""
    return f"""# Car Configuration - {template.title()} Template
# Generated by 'donkey car create'

# Hardware Configuration
# Steering
STEERING_AXIS = 0
STEERING_INVERTED = False
STEERING_MIN_RAW = -32768
STEERING_MAX_RAW = 32767
STEERING_CENTER_RAW = 0
STEERING_DEADZONE = 0.05

# Throttle
THROTTLE_AXIS = 1
THROTTLE_INVERTED = False
THROTTLE_MIN_RAW = -32768
THROTTLE_MAX_RAW = 32767
THROTTLE_CENTER_RAW = 0
THROTTLE_DEADZONE = 0.05

# Buttons
RECORD_BUTTON = None  # Button code or None
MODE_BUTTON = None    # Button code or None

# Camera Configuration
CAMERA_TYPE = "WEBCAM"
CAMERA_WIDTH = 160
CAMERA_HEIGHT = 120
CAMERA_FRAMERATE = 20

# Vehicle Configuration
MAX_THROTTLE = 1.0
MIN_THROTTLE = -1.0

# Training Configuration
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 120
IMAGE_DEPTH = 3
"""


def _default_myconfig() -> str:
    """Generate default myconfig.py for new cars."""
    return """# myconfig.py
# Local configuration overrides
# Edit this file to customize your car's settings

# Import base configuration
from config.car_config import *

# Override any settings here
# Example:
# STEERING_INVERTED = True
# MAX_THROTTLE = 0.5
"""
