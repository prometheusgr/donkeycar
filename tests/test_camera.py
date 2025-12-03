from types import SimpleNamespace

import pytest

from mycar.camera import setup_single_camera


def test_setup_single_camera_unknown_type_raises():
    cfg = SimpleNamespace(
        CAMERA_TYPE="FOOBAR",
        IMAGE_W=10,
        IMAGE_H=10,
        IMAGE_DEPTH=3,
        CAMERA_FRAMERATE=20,
        CAMERA_VFLIP=False,
        CAMERA_HFLIP=False,
        CAMERA_INDEX=0,
    )
    from mycar.camera import setup_single_camera

    with pytest.raises(ValueError):
        setup_single_camera(cfg, vehicle=SimpleNamespace(add=lambda *a, **k: None))
