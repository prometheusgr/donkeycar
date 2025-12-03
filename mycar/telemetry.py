"""Telemetry helpers for mycar.

This module centralizes telemetry part creation so `manage.py` can be
smaller and import-light. It provides `setup_mqtt(cfg)` which returns
an MQTT telemetry part instance or `None`.
"""

# Quick lint mitigations: optional runtime imports (MQTT) can fail on
# test/CI environments. Silence import-error and keep the module safe.
# pylint: disable=import-error,too-many-lines

from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


def setup_mqtt(cfg: Any) -> Optional[object]:
    """Return an MQTT telemetry part when enabled, otherwise None.

    This mirrors the previous inline logic but is extracted so that
    `mycar.manage` can remain focused on wiring.
    """
    if getattr(cfg, "HAVE_MQTT_TELEMETRY", False):
        try:
            # runtime import, may not be present in test/CI environments
            from donkeycar.parts.telemetry import MqttTelemetry
        except Exception as exc:  # ImportError or missing deps
            logger.debug("Could not create MqttTelemetry: %s", exc)
            return None
        return MqttTelemetry(cfg)
    return None
