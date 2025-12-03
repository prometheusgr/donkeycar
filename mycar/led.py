"""LED and record-tracker helpers extracted from `manage.py`.

Provides `setup_led(cfg, vehicle, model_type=None)` which wires the
RGB LED logic and a small record-tracker part that emits alert colors.
"""

# Quick, localized lint mitigations for optional hardware imports and
# larger wiring modules. These are deliberate to keep the module import
# safe on CI/dev machines without hardware deps.
# pylint: disable=import-error,too-many-lines

from typing import Any, Tuple


def get_record_alert_color(cfg: Any, num_records: int) -> Tuple[int, int, int] | int:
    """Return the alert color tuple for the given recorded count."""
    col = (0, 0, 0)
    for count, color in cfg.RECORD_ALERT_COLOR_ARR:
        if num_records >= count:
            col = color
    return col


class RecordTracker:
    """Track recorded count changes and produce alert colors/durations."""

    def __init__(self, cfg: Any) -> None:
        """Initialize record tracker counters and capture `cfg`."""
        self.cfg = cfg
        self.last_num_rec_print = 0
        self.dur_alert = 0
        self.force_alert = 0

    def run(self, num_records: int):
        """Update internal counters and return alert color or 0."""
        if num_records is None:
            return 0

        if self.last_num_rec_print != num_records or self.force_alert:
            self.last_num_rec_print = num_records

            if num_records % 10 == 0:
                # logging should happen in parts; avoid depending on external logger
                pass

            if num_records % self.cfg.REC_COUNT_ALERT == 0 or self.force_alert:
                self.dur_alert = (
                    num_records
                    // self.cfg.REC_COUNT_ALERT
                    * self.cfg.REC_COUNT_ALERT_CYC
                )
                self.force_alert = 0

        if self.dur_alert > 0:
            self.dur_alert -= 1

        if self.dur_alert != 0:
            return get_record_alert_color(self.cfg, num_records)

        return 0


class LedConditionLogic:
    """Determine LED blink behavior based on mode, recording, and model state.

    This class returns a blink rate (0 off, -1 solid on, >0 blink rate).
    """

    def __init__(self, cfg: Any) -> None:
        """Initialize LED logic with configuration."""
        self.cfg = cfg
        self.led = None
        self.model_type = None

    def run(
        self,
        mode,
        recording,
        recording_alert,
        behavior_state,
        model_file_changed,
        track_loc,
    ):
        """Return blink rate (0=off, -1=solid, >0 blink rate)."""

        if track_loc is not None:
            if self.led is not None:
                self.led.set_rgb(*self.cfg.LOC_COLORS[track_loc])
            return -1

        if model_file_changed:
            if self.led is not None:
                self.led.set_rgb(
                    self.cfg.MODEL_RELOADED_LED_R,
                    self.cfg.MODEL_RELOADED_LED_G,
                    self.cfg.MODEL_RELOADED_LED_B,
                )
            return 0.1
        if self.led is not None:
            self.led.set_rgb(self.cfg.LED_R, self.cfg.LED_G, self.cfg.LED_B)

        if recording_alert:
            if self.led is not None:
                self.led.set_rgb(*recording_alert)
            return self.cfg.REC_COUNT_ALERT_BLINK_RATE
        if self.led is not None:
            self.led.set_rgb(self.cfg.LED_R, self.cfg.LED_G, self.cfg.LED_B)

        if behavior_state is not None and self.model_type == "behavior":
            r, g, b = self.cfg.BEHAVIOR_LED_COLORS[behavior_state]
            if self.led is not None:
                self.led.set_rgb(r, g, b)
            return -1  # solid on

        if recording:
            return -1  # solid on
        elif mode == "user":
            return 1
        elif mode == "local_angle":
            return 0.5
        elif mode == "local":
            return 0.1
        return 0


def setup_led(cfg: Any, vehicle: Any, model_type: str | None = None):
    """Wire up LED parts and the record tracker on `vehicle`.

    Returns a tuple `(led_logic, rec_tracker_part)` so callers can interact
    with the created parts (for example hooking up a button trigger).
    """
    led = None

    if getattr(cfg, "HAVE_RGB_LED", False) and not getattr(cfg, "DONKEY_GYM", False):
        from donkeycar.parts.led_status import RGB_LED

        led = RGB_LED(cfg.LED_PIN_R, cfg.LED_PIN_G,
                      cfg.LED_PIN_B, cfg.LED_INVERT)
        led.set_rgb(cfg.LED_R, cfg.LED_G, cfg.LED_B)

    led_logic = LedConditionLogic(cfg)

    vehicle.add(
        led_logic,
        inputs=[
            "user/mode",
            "recording",
            "records/alert",
            "behavior/state",
            "modelfile/modified",
            "pilot/loc",
        ],
        outputs=["led/blink_rate"],
    )

    if led is not None:
        led_logic.led = led
        vehicle.add(led, inputs=["led/blink_rate"])

    rec_tracker_part = RecordTracker(cfg)
    vehicle.add(rec_tracker_part, inputs=[
                "tub/num_records"], outputs=["records/alert"])

    if model_type is not None:
        led_logic.model_type = model_type

    return led_logic, rec_tracker_part
