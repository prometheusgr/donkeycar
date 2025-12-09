"""
Data management commands.

Handles:
- Recording training data
- Converting data formats (TUB v1 to v2, to TFLite, etc.)
- Analyzing and visualizing data
- Managing data splits (train/val/test)
"""

import click
from pathlib import Path


@click.group()
def data():
    """
    Manage training data.
    
    Capture, convert, process, and analyze training datasets.
    """
    pass


@data.command()
@click.option('--car-path', type=click.Path(exists=True), default='mycar',
              help='Path to car project (default: mycar)')
@click.option('--duration', type=int, default=300,
              help='Recording duration in seconds (default: 300)')
@click.option('--name', type=str, default=None,
              help='Dataset name (default: auto-generated)')
def record(car_path, duration, name):
    """
    Start recording training data from the car.
    
    Records camera frames and control inputs to a dataset.
    """
    car_path = Path(car_path).resolve()
    
    if not car_path.exists():
        click.echo(f"Error: Car directory not found: {car_path}", err=True)
        return
    
    data_dir = car_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if name:
        dataset = data_dir / name
    else:
        import datetime
        dataset = data_dir / f"dataset_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    click.echo(f"Recording to: {dataset}")
    click.echo(f"Duration: {duration} seconds")
    click.echo("Press Ctrl+C to stop recording")
    
    click.echo("\n[Recording functionality would integrate with car's recording module]")
    click.echo(f"Data would be saved to: {dataset}")


@data.command()
@click.option('--source', type=click.Path(exists=True), required=True,
              help='Source data directory')
@click.option('--format', type=click.Choice(['v2', 'tflite', 'csv']), default='v2',
              help='Output format (default: v2)')
@click.option('--output', type=click.Path(), default=None,
              help='Output directory (default: auto-generated)')
def convert(source, format, output):
    """
    Convert training data to different formats.
    
    Supports: TUB v2, TFLite, CSV
    """
    source_path = Path(source).resolve()
    
    if output is None:
        output = source_path.parent / f"{source_path.name}_converted_{format}"
    else:
        output = Path(output).resolve()
    
    click.echo(f"Converting from: {source_path}")
    click.echo(f"Format: {format}")
    click.echo(f"Output to: {output}")
    
    click.echo("\n[Conversion functionality would integrate with TUB conversion tools]")


@data.command()
@click.option('--data-dir', type=click.Path(exists=True), required=True,
              help='Data directory to analyze')
def analyze(data_dir):
    """
    Analyze training dataset statistics.
    
    Shows frame count, steering/throttle distributions, etc.
    """
    data_path = Path(data_dir).resolve()
    
    click.echo(f"Analyzing: {data_path}")
    click.echo("\nDataset Statistics:")
    
    # Count files
    images = list(data_path.glob('*/image*.jpg'))
    click.echo(f"  Total frames: {len(images)}")
    
    click.echo("\n[Detailed analysis would show steering/throttle distributions]")


@data.command()
@click.option('--data-dir', type=click.Path(exists=True), required=True,
              help='Data directory to visualize')
@click.option('--sample', type=int, default=0,
              help='Frame number to visualize (default: first)')
def visualize(data_dir, sample):
    """
    Visualize training data samples.
    
    Display images and corresponding control inputs.
    """
    data_path = Path(data_dir).resolve()
    
    click.echo(f"Visualizing: {data_path}")
    click.echo(f"Sample frame: {sample}")
    
    click.echo("\n[Visualization would display image with steering/throttle values]")
