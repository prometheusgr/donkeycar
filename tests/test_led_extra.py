from types import SimpleNamespace

from mycar.led import LedConditionLogic, get_record_alert_color


def make_cfg():
    cfg = SimpleNamespace()
    cfg.LOC_COLORS = [(9, 8, 7)]
    cfg.MODEL_RELOADED_LED_R = 10
    cfg.MODEL_RELOADED_LED_G = 11
    cfg.MODEL_RELOADED_LED_B = 12
    cfg.LED_R = 1
    cfg.LED_G = 2
    cfg.LED_B = 3
    cfg.REC_COUNT_ALERT_BLINK_RATE = 0.42
    cfg.BEHAVIOR_LED_COLORS = [(2, 3, 4)]
    cfg.RECORD_ALERT_COLOR_ARR = [(0, (1, 1, 1)), (1000, (5, 5, 5))]
    return cfg


class FakeLed:
    def __init__(self):
        self.calls = []

    def set_rgb(self, r, g, b):
        self.calls.append((r, g, b))


def test_model_file_changed_sets_led_and_returns_rate():
    cfg = make_cfg()
    logic = LedConditionLogic(cfg)
    fake = FakeLed()
    logic.led = fake

    rate = logic.run("user", False, 0, None, True, None)
    assert rate == 0.1
    assert fake.calls[-1] == (
        cfg.MODEL_RELOADED_LED_R,
        cfg.MODEL_RELOADED_LED_G,
        cfg.MODEL_RELOADED_LED_B,
    )


def test_track_loc_sets_led_color_and_returns_solid():
    cfg = make_cfg()
    logic = LedConditionLogic(cfg)
    fake = FakeLed()
    logic.led = fake

    rate = logic.run("user", False, 0, None, False, 0)
    assert rate == -1
    assert fake.calls[-1] == cfg.LOC_COLORS[0]


def test_recording_alert_uses_alert_color_and_rate():
    cfg = make_cfg()
    logic = LedConditionLogic(cfg)
    fake = FakeLed()
    logic.led = fake

    alert = (7, 7, 7)
    rate = logic.run("user", False, alert, None, False, None)
    assert rate == cfg.REC_COUNT_ALERT_BLINK_RATE
    assert fake.calls[-1] == alert


def test_behavior_state_with_model_type_behavior_sets_color_and_solid():
    cfg = make_cfg()
    logic = LedConditionLogic(cfg)
    logic.model_type = "behavior"
    fake = FakeLed()
    logic.led = fake

    rate = logic.run("user", False, 0, 0, False, None)
    assert rate == -1
    assert fake.calls[-1] == cfg.BEHAVIOR_LED_COLORS[0]
