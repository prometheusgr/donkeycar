"""Controller wiring helper for `mycar.manage.drive`.

This module centralizes controller selection and wiring so that
`manage.py` remains small and easier to lint. Imports that may require
optional dependencies are performed lazily inside the function.
# Pylint: some of these helper modules are imported lazily and certain
# broad-except catches are intentional in wiring code that must be
# resilient to missing hardware. Suppress the related warning here.
# pylint: disable=broad-except
"""
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def setup_controller(cfg: Any, vehicle: Any, use_joystick: bool = False) -> Optional[object]:
    """Configure and add controller parts to `vehicle`.

    Returns the controller instance (or ``None`` if unavailable).
    """
    ctr = None
    try:
        # import the common controller classes; these imports may fail on
        # minimal environments so catch broadly and fall back to None.
        from donkeycar.parts.controller import (
            LocalWebController,
            JoystickController,
        )
    except ImportError as exc:
        logger.debug("Controller parts not available: %s", exc)
        LocalWebController = JoystickController = object

    # Prefer an attached joystick if requested and available
    if use_joystick:
        try:
            # Many joystick implementations accept different constructor
            # arguments; create with no-args and let them autodetect.
            ctr = JoystickController()
            vehicle.add(
                ctr,
                outputs=["user/angle", "user/throttle",
                         "user/mode", "recording"],
                threaded=True,
            )
            return ctr
        except (RuntimeError, OSError, ValueError, TypeError) as exc:
            logger.debug("Joystick controller not available: %s", exc)
            ctr = None

    # If configuration requests an RC controller type, prefer that first
    try:
        if getattr(cfg, "CONTROLLER_TYPE", "").lower() in ("pigpio_rc", "rc"):
            from donkeycar.parts.controller import RCReceiver

            rc = RCReceiver(cfg)
            vehicle.add(
                rc,
                outputs=["user/angle", "user/throttle",
                         "user/mode", "recording"],
                threaded=True,
            )
            return rc
    except (ImportError, RuntimeError, OSError, ValueError, TypeError) as exc:
        logger.debug("RC controller not available: %s", exc)

    # Otherwise try local web controller as the default
    try:
        ctr = LocalWebController(
            port=getattr(cfg, "WEB_CONTROL_PORT", 8887),
            mode=getattr(cfg, "WEB_INIT_MODE", None),
        )
        vehicle.add(
            ctr,
            outputs=["user/angle", "user/throttle", "user/mode", "recording"],
            threaded=True,
        )
        return ctr
    except (RuntimeError, OSError, ValueError, TypeError) as exc:
        logger.debug("Local web controller not available: %s", exc)

    return None
