'''
Docstring for donkeycar.
'''
import os
import sys
import importlib
from typing import TYPE_CHECKING
"""Donkeycar package.

Keep this module lightweight: avoid heavy imports or printing at
import time so tests and static analysis can import the package
without side effects.
"""

__version__ = "5.2.dev5"
__all__ = ["Vehicle", "load_config", "Config"]

if TYPE_CHECKING:
    # Expose names to type checkers and linters without importing heavy modules.
    from .vehicle import Vehicle  # noqa: F401
    from .config import load_config, Config  # noqa: F401


def __getattr__(name: str):
    """Lazily import and expose commonly used attributes.

    This keeps the package import lightweight while preserving the
    public API expected by tests and external callers.
    """
    if name == "Vehicle":
        from .vehicle import Vehicle

        return Vehicle

    if name == "load_config":
        from .config import load_config

        return load_config

    if name == "Config":
        from .config import Config

        return Config

    # As a convenience, allow lazy access to submodules like `donkeycar.vehicle`
    # by importing and returning the submodule when requested.
    try:
        return importlib.import_module(f"{__name__}.{name}")
    except ImportError:
        # Module not available; fall through to raising AttributeError
        pass

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
