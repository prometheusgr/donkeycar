"""Camera setup helper for mycar.drive

This module centralizes camera selection and wiring so `mycar.manage`
can remain smaller. The `setup_camera` function will add camera parts
to the provided `vehicle` and return `(inputs, outputs, threaded)`
values used by the rest of the wiring.
"""

# Quick lint mitigation: camera parts are optional and import-time heavy
# (hardware deps). Silence import-error and keep this module safe on CI.
# pylint: disable=import-error,too-many-lines

from typing import Tuple, Any, List
import logging

logger = logging.getLogger(__name__)


def setup_stereo_camera(cfg: Any, vehicle: Any) -> Tuple[List[str], List[str], bool]:
    """Configure two-camera (stereo) setups and attach parts to vehicle.

    Returns (inputs, outputs, threaded). Raises ValueError on unsupported
    stereo camera types.
    """
    if cfg.CAMERA_TYPE == "WEBCAM":
        from donkeycar.parts.camera import Webcam

        cam_a = Webcam(
            image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH, iCam=0
        )
        cam_b = Webcam(
            image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH, iCam=1
        )

    elif cfg.CAMERA_TYPE == "CVCAM":
        from donkeycar.parts.cv import CvCam

        cam_a = CvCam(
            image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH, iCam=0
        )
        cam_b = CvCam(
            image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH, iCam=1
        )
    else:
        raise ValueError(
            f"Unsupported camera type for stereo: {cfg.CAMERA_TYPE}")

    vehicle.add(cam_a, outputs=["cam/image_array_a"], threaded=True)
    vehicle.add(cam_b, outputs=["cam/image_array_b"], threaded=True)

    from donkeycar.parts.image import StereoPair

    vehicle.add(
        StereoPair(),
        inputs=["cam/image_array_a", "cam/image_array_b"],
        outputs=["cam/image_array"],
    )
    return [], ["cam/image_array"], True


def setup_dgym_camera(cfg: Any, vehicle: Any) -> Tuple[List[str], List[str], bool]:
    """Configure DonkeyGym camera and attach to vehicle."""
    from donkeycar.parts.dgym import DonkeyGymEnv

    cam = DonkeyGymEnv(
        cfg.DONKEY_SIM_PATH,
        host=cfg.SIM_HOST,
        env_name=cfg.DONKEY_GYM_ENV_NAME,
        conf=cfg.GYM_CONF,
        record_location=cfg.SIM_RECORD_LOCATION,
        record_gyroaccel=cfg.SIM_RECORD_GYROACCEL,
        record_velocity=cfg.SIM_RECORD_VELOCITY,
        record_lidar=cfg.SIM_RECORD_LIDAR,
        delay=cfg.SIM_ARTIFICIAL_LATENCY,
    )
    vehicle.add(
        cam, inputs=["angle", "throttle"], outputs=["cam/image_array"], threaded=True
    )
    return ["angle", "throttle"], ["cam/image_array"], True


def setup_single_camera(cfg: Any, vehicle: Any) -> Tuple[List[str], List[str], bool]:
    """Configure a single camera variant and attach to vehicle."""
    inputs: List[str] = []
    outputs: List[str] = ["cam/image_array"]
    threaded = True

    if cfg.CAMERA_TYPE == "PICAM":
        from donkeycar.parts.camera import PiCamera

        cam = PiCamera(
            image_w=cfg.IMAGE_W,
            image_h=cfg.IMAGE_H,
            image_d=cfg.IMAGE_DEPTH,
            framerate=cfg.CAMERA_FRAMERATE,
            vflip=cfg.CAMERA_VFLIP,
            hflip=cfg.CAMERA_HFLIP,
        )

    elif cfg.CAMERA_TYPE == "WEBCAM":
        from donkeycar.parts.camera import Webcam

        cam = Webcam(
            image_w=cfg.IMAGE_W,
            image_h=cfg.IMAGE_H,
            image_d=cfg.IMAGE_DEPTH,
            camera_index=cfg.CAMERA_INDEX,
        )

    elif cfg.CAMERA_TYPE == "CVCAM":
        from donkeycar.parts.cv import CvCam

        cam = CvCam(
            image_w=cfg.IMAGE_W,
            image_h=cfg.IMAGE_H,
            image_d=cfg.IMAGE_DEPTH,
            iCam=cfg.CAMERA_INDEX,
        )

    elif cfg.CAMERA_TYPE == "CSIC":
        from donkeycar.parts.camera import CSICamera

        cam = CSICamera(
            image_w=cfg.IMAGE_W,
            image_h=cfg.IMAGE_H,
            image_d=cfg.IMAGE_DEPTH,
            framerate=cfg.CAMERA_FRAMERATE,
            capture_width=cfg.IMAGE_W,
            capture_height=cfg.IMAGE_H,
            gstreamer_flip=cfg.CSIC_CAM_GSTREAMER_FLIP_PARM,
        )

    elif cfg.CAMERA_TYPE == "V4L":
        from donkeycar.parts.camera import V4LCamera

        cam = V4LCamera(
            image_w=cfg.IMAGE_W,
            image_h=cfg.IMAGE_H,
            image_d=cfg.IMAGE_DEPTH,
            framerate=cfg.CAMERA_FRAMERATE,
        )

    elif cfg.CAMERA_TYPE == "MOCK":
        from donkeycar.parts.camera import MockCamera

        cam = MockCamera(
            image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH
        )

    elif cfg.CAMERA_TYPE == "IMAGE_LIST":
        from donkeycar.parts.camera import ImageListCamera

        cam = ImageListCamera(path_mask=cfg.PATH_MASK)

    elif cfg.CAMERA_TYPE == "LEOPARD":
        from donkeycar.parts.leopard_imaging import LICamera

        cam = LICamera(width=cfg.IMAGE_W, height=cfg.IMAGE_H,
                       fps=cfg.CAMERA_FRAMERATE)

    else:
        raise ValueError(f"Unknown camera type: {cfg.CAMERA_TYPE}")

    # Donkey gym augmentation of outputs is handled by the DGym helper
    # when used; here we just attach the camera instance.
    vehicle.add(cam, inputs=inputs, outputs=outputs, threaded=threaded)

    return inputs, outputs, threaded


def setup_camera(
    cfg: Any, vehicle: Any, camera_type: str = "single"
) -> Tuple[List[str], List[str], bool]:
    """High-level camera setup delegating to smaller helpers.

    This keeps branching and local variable counts lower for each helper
    so linters and readers can reason about smaller functions.
    """
    logger.info("cfg.CAMERA_TYPE %s", cfg.CAMERA_TYPE)

    if camera_type == "stereo":
        return setup_stereo_camera(cfg, vehicle)

    if cfg.DONKEY_GYM:
        return setup_dgym_camera(cfg, vehicle)

    return setup_single_camera(cfg, vehicle)
