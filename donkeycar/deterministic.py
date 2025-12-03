"""Determinism helpers for tests and reproducible runs.

Provide a single entrypoint `enable_determinism(seed=1234)` which attempts
to make runs reproducible by setting seeds for Python `random`, `numpy`,
TensorFlow and PyTorch where available, and toggling common env vars.

Note: `PYTHONHASHSEED` must ideally be set before the Python process starts
to get full reproducibility across runs; we set it here for subprocesses
launched from this process and for consistency within the running process.
"""
from __future__ import annotations

import os
import random
from typing import Optional


def enable_determinism(seed: int = 1234) -> None:
    """Enable deterministic behaviour where possible.

    This is best-effort and will not guarantee 100% reproducibility across
    platforms, Python versions, or binary library versions, but it reduces
    variability by seeding RNGs and toggling common deterministic flags.

    Args:
        seed: integer seed used for all RNGs.
    """
    # Set PYTHONHASHSEED for child processes and consistent hashing
    os.environ.setdefault("PYTHONHASHSEED", str(seed))

    # Python built-in
    random.seed(seed)

    # Numpy
    try:
        import numpy as _np

        _np.random.seed(seed)
    except ImportError:
        pass

    # TensorFlow
    try:
        # Prefer lazy import pattern; TF may be heavy and optional
        import tensorflow as _tf

        try:
            _tf.random.set_seed(seed)
        except ImportError:
            # older TF versions
            try:
                _tf.set_random_seed(seed)  # type: ignore[attr-defined]
            except AttributeError:
                pass

        # Environment variables that help reproducibility on TF when possible
        os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
        os.environ.setdefault("TF_CUDNN_DETERMINISTIC", "1")
    except ImportError:
        pass

    # PyTorch
    try:
        import torch as _torch

        try:
            _torch.manual_seed(seed)
            if _torch.cuda.is_available():
                _torch.cuda.manual_seed_all(seed)
        except Exception:
            pass

        try:
            # Newer PyTorch: enforce deterministic algorithms
            _torch.use_deterministic_algorithms(True)
        except Exception:
            # Fallback for older versions
            try:
                _torch.backends.cudnn.deterministic = True
                _torch.backends.cudnn.benchmark = False
            except Exception:
                pass

        # Helpful env var for cuBLAS/cuDNN reproducibility when CUDA is used
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    except Exception:
        pass


__all__ = ["enable_determinism"]
