# DonkeyCar CLI - Developer Guide

This guide explains the CLI architecture and how to extend it with new commands.

## Architecture Overview

```
donkeycar/cli/
├── __init__.py          # Package exports
├── __main__.py          # Standalone entry point
├── core.py              # Main CLI app (Click)
├── README.md            # User documentation
├── commands/
│   ├── __init__.py
│   ├── car.py           # Car management commands
│   ├── data.py          # Data management commands
│   ├── training.py      # Training commands
│   └── system.py        # System utilities
└── utils/
    ├── __init__.py
    ├── project.py       # Project discovery and management
    ├── config.py        # Configuration loading
    └── data.py          # Data/TUB utilities
```

## Key Technologies

- **Click** (v8.0+) - Command-line interface framework
- **Python 3.11+** - Minimum Python version
- **pathlib** - Modern path handling

## Core Architecture

### Entry Points

1. **Installed Command** (recommended)
   ```bash
   donkey --help
   ```
   Configured in `setup.cfg` as console script entry point.

2. **Python Module**
   ```bash
   python -m donkeycar.cli --help
   ```
   Uses `donkeycar/cli/__main__.py`

3. **Direct Script**
   ```python
   from donkeycar.cli import main
   main()
   ```

### Command Groups

The CLI uses Click's command groups to organize commands:

```python
@click.group()
def car():
    """Car management commands."""
    pass

@car.command()
def create():
    """Create a new car."""
    pass

# Usage: donkey car create --help
```

## Adding New Commands

### 1. Create a New Command Module

Create `donkeycar/cli/commands/myfeature.py`:

```python
"""My feature commands."""

import click
from pathlib import Path


@click.group()
def myfeature():
    """
    Manage my feature.
    
    Brief description of what this group does.
    """
    pass


@myfeature.command()
@click.option('--name', required=True, help='Name of the thing')
@click.option('--verbose', is_flag=True, help='Verbose output')
def dothething(name, verbose):
    """
    Do the thing with the name.
    
    Longer description of what this command does.
    """
    click.echo(f"Doing thing: {name}")
    
    if verbose:
        click.echo("Details here...")
```

### 2. Register in Core

Edit `donkeycar/cli/core.py`:

```python
# Add import
from .commands import myfeature

# Add to CLI
cli.add_command(myfeature.myfeature)
```

### 3. Test the Command

```bash
python -m donkeycar.cli myfeature --help
python -m donkeycar.cli myfeature dothething --name test --verbose
```

## Click Command Patterns

### Basic Options

```python
@click.command()
@click.option('--name', default='World', help='Name to greet')
@click.argument('count', type=int, default=1)
def hello(name, count):
    """Greet someone."""
    for _ in range(count):
        click.echo(f"Hello {name}!")
```

### Path Arguments

```python
@click.command()
@click.option('--path', type=click.Path(exists=True), required=True)
@click.option('--output', type=click.Path())
def process(path, output):
    """Process a file."""
    input_path = Path(path)
    if output:
        output_path = Path(output)
```

### Confirmations and Input

```python
@click.command()
def create():
    """Create something."""
    if click.confirm("Are you sure?"):
        click.echo("Creating...")
    else:
        click.echo("Cancelled")
    
    name = click.prompt("Enter name", default="default")
    choice = click.prompt("Choose", type=click.Choice(['a', 'b']))
```

### Progress and Feedback

```python
@click.command()
def process():
    """Process items."""
    items = range(100)
    
    # Progress bar
    with click.progressbar(items, label='Processing') as bar:
        for item in bar:
            time.sleep(0.1)
    
    # Colored output
    click.secho("Success!", fg='green')
    click.secho("Warning", fg='yellow')
    click.secho("Error", fg='red')
    
    # Styled text
    click.echo(click.style("Bold", bold=True))
    click.echo(click.style("Underline", underline=True))
```

## Utility Modules

### Project Management

```python
from donkeycar.cli.utils.project import ProjectManager

pm = ProjectManager()
cars = pm.find_cars()           # Find all cars
datasets = pm.find_datasets()   # Find all datasets
models = pm.find_models()       # Find all models

pm.validate_car(Path('mycar'))  # Check if valid car
```

### Configuration

```python
from donkeycar.cli.utils.config import ConfigLoader

config = ConfigLoader.load_car_config(Path('mycar/myconfig.py'))
merged = ConfigLoader.merge_configs(config1, config2)
errors = ConfigLoader.validate_car_config(config)
```

### Data Management

```python
from donkeycar.cli.utils.data import TubManager

metadata = TubManager.get_tub_metadata(Path('mycar/data/dataset_001'))
tubs = TubManager.list_tubs(Path('mycar/data'))
TubManager.merge_tubs([tub1, tub2], output)
```

## Testing Commands

### Unit Tests

Create `tests/cli/test_commands.py`:

```python
import pytest
from click.testing import CliRunner
from donkeycar.cli.commands.car import car


def test_car_create():
    """Test car create command."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        result = runner.invoke(car, ['create', '--path', 'testcar'])
        assert result.exit_code == 0
        assert 'Car project created' in result.output


def test_car_create_exists():
    """Test creating when car already exists."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        # Create first
        runner.invoke(car, ['create', '--path', 'testcar'])
        
        # Try creating again with --force
        result = runner.invoke(car, ['create', '--path', 'testcar', '--force'])
        assert result.exit_code == 0
```

### Integration Tests

```python
def test_full_workflow():
    """Test complete car setup workflow."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        # Create car
        result = runner.invoke(car, ['create', '--path', 'testcar'])
        assert result.exit_code == 0
        
        # Configure
        result = runner.invoke(car, [
            'configure', '--car-path', 'testcar',
            '--steering', '0', '--throttle', '1'
        ])
        assert result.exit_code == 0
        
        # Verify
        result = runner.invoke(car, ['info', '--car-path', 'testcar'])
        assert 'testcar' in result.output
```

## Best Practices

### 1. Consistent Error Handling

```python
@click.command()
@click.option('--path', type=click.Path(exists=True))
def process(path):
    """Process something."""
    try:
        path_obj = Path(path)
        # Do work
    except FileNotFoundError:
        click.secho("Error: File not found", fg='red', err=True)
        raise SystemExit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg='red', err=True)
        raise SystemExit(1)
```

### 2. User-Friendly Output

```python
@click.command()
def process():
    """Show clear progress."""
    # Use emoji and symbols for clarity
    click.echo("✓ Step 1 complete")
    click.echo("⏳ Step 2 in progress...")
    click.echo("✗ Step 3 failed")
    
    # Use colors for emphasis
    click.secho("Success!", fg='green', bold=True)
    
    # Use indentation for hierarchy
    click.echo("Configuration:")
    click.echo("  • Steering: 0")
    click.echo("  • Throttle: 1")
```

### 3. Help Text Quality

```python
@click.command()
@click.option('--epochs', type=int, default=100,
              help='Number of training epochs (default: 100)')
@click.argument('data-dir', type=click.Path(exists=True))
def train(epochs, data_dir):
    """
    Train a model on data.
    
    Trains a neural network using the provided dataset.
    
    \b
    Example:
      donkey training train --epochs 50 /path/to/data
    
    \b
    For more information:
      https://docs.donkeycar.com/training
    """
    pass
```

### 4. Context and State

```python
@click.pass_context
def cli(ctx):
    """Main CLI with context."""
    # Store shared state
    ctx.ensure_object(dict)
    ctx.obj['project_root'] = Path.cwd()


@click.command()
@click.pass_context
def subcommand(ctx):
    """Subcommand with access to context."""
    project_root = ctx.obj['project_root']
```

## Performance Considerations

### Lazy Imports

Avoid importing heavy modules at module level:

```python
@click.command()
def train():
    """Train a model."""
    # Import here, not at module level
    import tensorflow as tf
    # Now use tf
```

### Async Operations

For long operations, provide feedback:

```python
@click.command()
def process():
    """Process data."""
    items = get_items()
    
    with click.progressbar(items) as bar:
        for item in bar:
            process_item(item)
            # Update progress automatically
```

## Documentation

Each command should have:

1. **Brief description** - First line
2. **Detailed description** - Multi-line docstring
3. **Examples** - Usage examples
4. **References** - Links to docs

```python
@click.command()
@click.option('--name', help='Name of the car')
def create(name):
    """
    Create a new car project.
    
    This creates a new directory with the car template files,
    including configuration, data directory, and models folder.
    
    \b
    Example:
      donkey car create --path mycar
    
    You can then configure your car with:
      donkey car configure --car-path mycar
    
    \b
    See also:
      - donkey car configure
      - donkey car info
      - https://docs.donkeycar.com
    """
    pass
```

## Extending with Plugins

Future versions may support plugin architecture:

```python
# donkeycar/cli/plugins/custom.py
class CustomCommand:
    name = "custom"
    help = "My custom command"
    
    def create_command(self):
        @click.command()
        def cmd():
            click.echo("Custom!")
        return cmd
```

## Troubleshooting Development

### Click not installed

```bash
pip install click>=8.0
```

### Changes not reflected

```bash
# Reinstall in development mode
pip install -e /path/to/donkeycar
```

### Import errors

```bash
# Check Python path
python -c "import donkeycar.cli; print(donkeycar.cli.__file__)"

# Verify installation
donkey --version
```

## Resources

- **Click Documentation**: https://click.palletsprojects.com/
- **DonkeyCar Docs**: https://docs.donkeycar.com
- **GitHub Issues**: Report bugs or request features
