from mycar import drivetrain, camera
import sys
from types import SimpleNamespace, ModuleType

# Provide lightweight fake donkeycar package modules to avoid importing
# optional heavy deps (PIL, hardware libs) during tests. Insert minimal
# ModuleType entries into `sys.modules` before importing `mycar` so that
# import-time references to `donkeycar` do not pull in heavy dependencies.
_inserted = []
if "donkeycar" not in sys.modules:
    pkg = ModuleType("donkeycar")
    pkg.__path__ = []
    sys.modules["donkeycar"] = pkg
    _inserted.append("donkeycar")
if "donkeycar.parts" not in sys.modules:
    parts_pkg = ModuleType("donkeycar.parts")
    parts_pkg.__path__ = []
    sys.modules["donkeycar.parts"] = parts_pkg
    _inserted.append("donkeycar.parts")
# lightweight actuator/pins modules (used only at import-time)
if "donkeycar.parts.actuator" not in sys.modules:
    sys.modules["donkeycar.parts.actuator"] = ModuleType(
        "donkeycar.parts.actuator")
    _inserted.append("donkeycar.parts.actuator")
if "donkeycar.parts.pins" not in sys.modules:
    sys.modules["donkeycar.parts.pins"] = ModuleType("donkeycar.parts.pins")
    _inserted.append("donkeycar.parts.pins")

# Now import the modules under test; they will see the lightweight
# `donkeycar` placeholders instead of attempting to import Pillow.


class FakeVehicle:
    def __init__(self):
        self.add_calls = []

    def add(self, part, **kwargs):
        self.add_calls.append((part, kwargs))


def test_setup_drivetrain_noop_in_sim_or_mock():
    v = FakeVehicle()
    cfg = SimpleNamespace(
        DONKEY_GYM=True, DRIVE_TRAIN_TYPE="PWM_STEERING_THROTTLE"
    )
    # should be a no-op (return early) and not add parts
    drivetrain.setup_drivetrain(cfg, v)
    assert v.add_calls == []

    v2 = FakeVehicle()
    cfg2 = SimpleNamespace(DONKEY_GYM=False, DRIVE_TRAIN_TYPE="MOCK")
    drivetrain.setup_drivetrain(cfg2, v2)
    assert v2.add_calls == []


def test_setup_camera_delegates_to_dgym(monkeypatch):
    # Provide a fake DonkeyGymEnv so we don't import the real simulator
    class FakeDGym:
        def __init__(self, *args, **kwargs):
            pass

    fake_module = SimpleNamespace(DonkeyGymEnv=FakeDGym)
    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.dgym"] = fake_module

        cfg = SimpleNamespace(
            DONKEY_GYM=True,
            CAMERA_TYPE="MOCK",
            DONKEY_SIM_PATH="sim",
            SIM_HOST="127.0.0.1",
            DONKEY_GYM_ENV_NAME="env",
            GYM_CONF={},
            SIM_RECORD_LOCATION=False,
            SIM_RECORD_GYROACCEL=False,
            SIM_RECORD_VELOCITY=False,
            SIM_RECORD_LIDAR=False,
            SIM_ARTIFICIAL_LATENCY=0,
        )

        v = FakeVehicle()
        inputs, outputs, threaded = camera.setup_camera(
            cfg, v, camera_type="single")

        # DonkeyGym camera expects angle/throttle inputs and cam output
        assert "angle" in inputs and "throttle" in inputs
        assert "cam/image_array" in outputs
    finally:
        # restore sys.modules to previous state
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)


# remove the lightweight placeholders we inserted at module import time
for _k in _inserted:
    try:
        del sys.modules[_k]
    except KeyError:
        pass
