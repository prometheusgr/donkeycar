import sys

from types import SimpleNamespace

import importlib

from mycar.telemetry import setup_mqtt


def test_setup_mqtt_disabled():
    cfg = SimpleNamespace(HAVE_MQTT_TELEMETRY=False)
    assert setup_mqtt(cfg) is None


def test_setup_mqtt_with_fake_module(monkeypatch):
    # ensure our fake telemetry class is used when the module exists
    fake_module = SimpleNamespace()

    class FakeMqtt:
        def __init__(self, cfg):
            self.cfg = cfg

    fake_module.MqttTelemetry = FakeMqtt

    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.telemetry"] = fake_module
        cfg = SimpleNamespace(HAVE_MQTT_TELEMETRY=True)
        tel = setup_mqtt(cfg)
        assert isinstance(tel, FakeMqtt)
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)
