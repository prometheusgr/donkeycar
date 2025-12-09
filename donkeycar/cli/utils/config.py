"""
Configuration utilities - handle configuration loading and validation.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sys


class ConfigLoader:
    """Load and validate configuration files."""

    @staticmethod
    def load_car_config(config_path: Path) -> Dict[str, Any]:
        """
        Load car configuration from Python file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary of configuration values
        """
        if not config_path.exists():
            return {}

        config = {}
        try:
            with open(config_path) as f:
                code = f.read()
                exec(code, config)
            # Remove special attributes
            config = {k: v for k, v in config.items() if not k.startswith('_')}
        except Exception as e:
            print(
                f"Error loading config from {config_path}: {e}", file=sys.stderr)

        return config

    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple config dictionaries.

        Later configs override earlier ones.
        """
        result = {}
        for config in configs:
            result.update(config)
        return result

    @staticmethod
    def validate_car_config(config: Dict[str, Any]) -> list:
        """
        Validate car configuration.

        Returns:
            List of validation error messages
        """
        errors = []

        required_keys = ['STEERING_AXIS', 'THROTTLE_AXIS']
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required config: {key}")

        if 'MAX_THROTTLE' in config and config['MAX_THROTTLE'] <= 0:
            errors.append("MAX_THROTTLE must be positive")

        return errors
