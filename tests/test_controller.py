import sys
import importlib
from types import SimpleNamespace

from types import ModuleType


class FakeVehicle:
    def __init__(self):
        self.add_calls = []

    def add(self, part, **kwargs):
        self.add_calls.append((part, kwargs))


def _make_fake_controller_module():
    class FakeJoystick:
        def __init__(self, *args, **kwargs):
            self.name = "fake_joystick"

    class FakeLocalWeb:
        def __init__(self, port=8887, mode=None):
            self.port = port
            self.mode = mode

    class FakeWebFpv:
        pass

    class FakeRCReceiver:
        def __init__(self, cfg):
            self.cfg = cfg

    mod = ModuleType("donkeycar.parts.controller")
    mod.JoystickController = FakeJoystick
    mod.LocalWebController = FakeLocalWeb
    mod.WebFpv = FakeWebFpv
    mod.RCReceiver = FakeRCReceiver
    return mod, FakeJoystick, FakeLocalWeb, FakeRCReceiver


def test_setup_controller_prefers_joystick_when_requested():
    mod, FakeJoystick, *_ = _make_fake_controller_module()
    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.controller"] = mod
        import mycar.controller as controller
        importlib.reload(controller)

        cfg = SimpleNamespace(WEB_CONTROL_PORT=8887,
                              WEB_INIT_MODE=None, CONTROLLER_TYPE="xbox")
        v = FakeVehicle()
        ctr = controller.setup_controller(cfg, v, use_joystick=True)

        assert isinstance(ctr, FakeJoystick)
        assert len(v.add_calls) == 1
        # ensure outputs include user channels
        assert "outputs" in v.add_calls[0][1]
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)


def test_setup_controller_falls_back_to_local_web():
    mod, _, FakeLocalWeb, _ = _make_fake_controller_module()
    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.controller"] = mod
        import mycar.controller as controller
        importlib.reload(controller)

        cfg = SimpleNamespace(WEB_CONTROL_PORT=9999,
                              WEB_INIT_MODE="init", CONTROLLER_TYPE="xbox")
        v = FakeVehicle()
        ctr = controller.setup_controller(cfg, v, use_joystick=False)

        assert isinstance(ctr, FakeLocalWeb)
        assert ctr.port == 9999
        assert len(v.add_calls) == 1
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)


def test_setup_controller_rc_receiver_selected_for_rc_type():
    mod, _, _, FakeRCReceiver = _make_fake_controller_module()
    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.controller"] = mod
        import mycar.controller as controller
        importlib.reload(controller)

        cfg = SimpleNamespace(CONTROLLER_TYPE="pigpio_rc")
        v = FakeVehicle()
        ctr = controller.setup_controller(cfg, v, use_joystick=False)

        assert isinstance(ctr, FakeRCReceiver)
        assert len(v.add_calls) == 1
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)
