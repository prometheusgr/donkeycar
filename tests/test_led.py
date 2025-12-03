import types

from mycar.led import get_record_alert_color, LedConditionLogic


class Cfg:
    REC_COUNT_ALERT = 100
    REC_COUNT_ALERT_BLINK_RATE = 0.4
    RECORD_ALERT_COLOR_ARR = [(0, (1, 1, 1)), (1000, (5, 5, 5))]
    MODEL_RELOADED_LED_R = 10
    MODEL_RELOADED_LED_G = 20
    MODEL_RELOADED_LED_B = 30
    LED_R = 0
    LED_G = 0
    LED_B = 0
    BEHAVIOR_LED_COLORS = [(2, 3, 4)]


def test_get_record_alert_color_basic():
    cfg = Cfg()
    # below first threshold => first color
    assert get_record_alert_color(cfg, 0) == (1, 1, 1)
    # above second threshold => second color
    assert get_record_alert_color(cfg, 2000) == (5, 5, 5)


def test_led_condition_logic_returns_expected_rates():
    cfg = Cfg()
    logic = LedConditionLogic(cfg)

    # default, no recording and mode=user => blink rate 1
    assert logic.run("user", False, 0, None, False, None) == 1

    # local_angle
    assert logic.run("local_angle", False, 0, None, False, None) == 0.5

    # local
    assert logic.run("local", False, 0, None, False, None) == 0.1

    # recording should be solid on
    assert logic.run("user", True, 0, None, False, None) == -1

    # behavior_state with model_type='behavior' -> solid on
    logic.model_type = "behavior"
    assert logic.run("user", False, 0, 0, False, None) == -1
