"""
System setup and utility commands.

Handles:
- Environment setup and validation
- Dependency installation
- Hardware calibration (joystick, camera)
- System diagnostics
"""

import click
from pathlib import Path
import subprocess
import sys


@click.group()
def system():
    """
    System setup and utilities.
    
    Install dependencies, validate environment, calibrate hardware.
    """
    pass


@system.command()
def check():
    """
    Check system environment and dependencies.
    
    Validates Python version, installed packages, and system capabilities.
    """
    click.echo("System Environment Check")
    click.echo("=" * 60)
    
    # Python version
    click.echo(f"\nPython Version: {sys.version}")
    
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    
    if (py_major, py_minor) >= (3, 11):
        click.secho("✓ Python 3.11+ detected", fg='green')
    else:
        click.secho(f"✗ Python {py_major}.{py_minor} - 3.11+ required", fg='red')
    
    # Check key packages
    click.echo("\nInstalled Packages:")
    packages = [
        'donkeycar',
        'tensorflow',
        'numpy',
        'opencv-python',
        'click',
        'pillow',
    ]
    
    for pkg in packages:
        try:
            mod = __import__(pkg.replace('-', '_'))
            version = getattr(mod, '__version__', 'unknown')
            click.secho(f"✓ {pkg}: {version}", fg='green')
        except ImportError:
            click.secho(f"✗ {pkg}: not installed", fg='yellow')


@system.command()
def install():
    """
    Install or update DonkeyCar dependencies.
    
    Sets up required Python packages and system utilities.
    """
    click.echo("Installing DonkeyCar Dependencies")
    click.echo("=" * 60)
    
    # Check for requirements file
    requirements_file = Path('requirements.txt')
    
    if requirements_file.exists():
        click.echo(f"\nUsing: {requirements_file}")
        
        if click.confirm("Install from requirements.txt?"):
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                    check=True
                )
                click.secho("✓ Installation complete", fg='green')
            except subprocess.CalledProcessError as e:
                click.secho(f"✗ Installation failed: {e}", fg='red')
    else:
        click.echo("No requirements.txt found in current directory")
        click.echo("Run this from the project root directory")


@system.command()
def calibrate():
    """
    Calibrate hardware devices.
    
    Interactive calibration for joystick, camera, steering, and throttle.
    """
    click.echo("Hardware Calibration")
    click.echo("=" * 60)
    
    device_type = click.prompt(
        "Select device to calibrate",
        type=click.Choice(['joystick', 'camera', 'motor']),
        default='joystick'
    )
    
    if device_type == 'joystick':
        click.echo("\nJoystick Calibration")
        click.echo("Connect your joystick and press Enter to start...")
        click.pause()
        
        click.echo("\n[Joystick calibration routine would run here]")
        click.echo("Please perform the following actions:")
        click.echo("  1. Move steering stick left and right")
        click.echo("  2. Move throttle stick forward and backward")
        click.echo("  3. Press each button")
        
    elif device_type == 'camera':
        click.echo("\nCamera Calibration")
        click.echo("This will help improve image quality and alignment.")
        
        click.echo("\n[Camera calibration routine would run here]")
        click.echo("Checking camera feed...")
        
    elif device_type == 'motor':
        click.echo("\nMotor/Throttle Calibration")
        click.echo("This will set throttle neutral point and range.")
        
        click.echo("\n[Motor calibration routine would run here]")


@system.command()
def info():
    """
    Display system and project information.
    
    Shows DonkeyCar version, environment, and project structure.
    """
    from donkeycar import __version__
    
    click.echo("DonkeyCar System Information")
    click.echo("=" * 60)
    
    click.echo(f"\nDonkeyCar Version: {__version__}")
    click.echo(f"Python Version: {sys.version.split()[0]}")
    
    # Find cars in current directory
    click.echo("\nLocal Cars Found:")
    for car_path in sorted(Path('.').glob('*/myconfig.py')):
        car_dir = car_path.parent
        click.echo(f"  - {car_dir}")
    
    # Find data directories
    click.echo("\nData Sets Found:")
    for data_path in sorted(Path('.').glob('*/data/*')):
        if data_path.is_dir():
            frame_count = len(list(data_path.glob('*/image*.jpg')))
            click.echo(f"  - {data_path.name}: {frame_count} frames")


@system.command()
@click.option('--format', type=click.Choice(['bash', 'powershell']), 
              default='bash', help='Shell completion format')
def completion(format):
    """
    Generate shell completion script.
    
    Creates completion for bash or PowerShell.
    """
    if format == 'bash':
        click.echo("""# Add to ~/.bashrc or ~/.bash_profile:
eval "$(_DONKEY_COMPLETE=bash_source donkey)"
""")
    elif format == 'powershell':
        click.echo("""# Add to PowerShell profile:
Invoke-Expression (&{ (python -m donkeycar.cli --help) })
""")
