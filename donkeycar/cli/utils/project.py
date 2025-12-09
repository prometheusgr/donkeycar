"""
Project utilities - handle project discovery and management.
"""

from pathlib import Path
from typing import List, Optional


class ProjectManager:
    """Manage DonkeyCar projects."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize project manager.

        Args:
            root_dir: Root directory to search for projects (default: current dir)
        """
        self.root_dir = root_dir or Path.cwd()

    def find_cars(self) -> List[Path]:
        """Find all car directories in project."""
        cars = []
        for path in self.root_dir.iterdir():
            if path.is_dir():
                # Check for car markers
                if (path / 'myconfig.py').exists() or (path / 'config' / 'car_config.py').exists():
                    cars.append(path)
        return sorted(cars)

    def find_datasets(self, car_dir: Optional[Path] = None) -> List[Path]:
        """Find all datasets in a car or globally."""
        if car_dir:
            data_dir = car_dir / 'data'
            if not data_dir.exists():
                return []
            datasets = [d for d in data_dir.iterdir() if d.is_dir()]
        else:
            datasets = []
            for path in self.root_dir.rglob('data'):
                if path.is_dir():
                    datasets.extend([d for d in path.iterdir() if d.is_dir()])

        return sorted(datasets)

    def find_models(self, car_dir: Optional[Path] = None) -> List[Path]:
        """Find all models in a car or globally."""
        if car_dir:
            model_dir = car_dir / 'models'
            if not model_dir.exists():
                return []
            models = [m for m in model_dir.iterdir() if m.is_file()]
        else:
            models = []
            for path in self.root_dir.rglob('models'):
                if path.is_dir():
                    models.extend([m for m in path.iterdir() if m.is_file()])

        return sorted(models)

    def validate_car(self, car_dir: Path) -> bool:
        """Check if a directory is a valid car project."""
        return (
            car_dir.exists() and
            car_dir.is_dir() and
            (
                (car_dir / 'myconfig.py').exists() or
                (car_dir / 'config' / 'car_config.py').exists()
            )
        )
