import sys
from types import SimpleNamespace

import importlib

from mycar.recording import setup_recording


class FakeVehicle:
    def __init__(self):
        self.add_calls = []

    def add(self, part, **kwargs):
        self.add_calls.append((part, kwargs))


def test_setup_recording_basic(monkeypatch):
    # Provide fake TubHandler and TubWriter so setup_recording doesn't import heavy deps
    class FakeTubHandler:
        def __init__(self, path=None):
            self.path = path

        def create_tub_path(self):
            return "fake_tub"

    class FakeTubWriter:
        def __init__(self, path, inputs=None, types=None, metadata=None):
            self.path = path
            self.inputs = inputs
            self.types = types
            self.metadata = metadata
            self.tub = "tubobj"

    fake_datastore = SimpleNamespace(TubHandler=FakeTubHandler)
    fake_tubmod = SimpleNamespace(TubWriter=FakeTubWriter)

    sys_modules_backup = dict(sys.modules)
    try:
        sys.modules["donkeycar.parts.datastore"] = fake_datastore
        sys.modules["donkeycar.parts.tub_v2"] = fake_tubmod

        cfg = SimpleNamespace(
            HAVE_PERFMON=False,
            AUTO_CREATE_NEW_TUB=False,
            DATA_PATH="data",
            METADATA=[],
            HAVE_MQTT_TELEMETRY=False,
            PUB_CAMERA_IMAGES=False,
            CONTROLLER_TYPE="xbox",
            WEB_CONTROL_PORT=8887,
            DONKEY_GYM=False,
        )

        vehicle = FakeVehicle()
        ctr = SimpleNamespace()
        tel = None
        meta = []
        inputs = ["cam/image_array"]
        types = ["image_array"]

        tw = setup_recording(cfg, vehicle, ctr, tel, meta, inputs, types)
        assert isinstance(tw, FakeTubWriter)
        # verify vehicle.add was called for the tub writer
        assert any(isinstance(call[0], FakeTubWriter) for call in vehicle.add_calls)
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)
