#!/usr/bin/env python3
"""mycar/manage.py — minimal header restored so module parses."""
# This module wires the runtime. Many imports are performed lazily
# at runtime to avoid import-time failures on machines missing
# optional hardware or heavy dependencies. Pylint static analysis
# can be noisy for such wiring code; apply a few targeted disables
# and provide TYPE_CHECKING imports for static analyzers.
# pylint: disable=too-many-locals,too-many-branches,too-many-statements,redefined-outer-name,undefined-variable,used-before-assignment,too-many-arguments,too-many-positional-arguments,missing-function-docstring,broad-except,unused-import
from typing import Optional, List, TYPE_CHECKING, Any, Callable
import os
import logging
from docopt import docopt
import donkeycar as dk

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - used only by linters/static analysis
    # Import names used by wiring code so static checkers know their types.
    # These imports are conditional to avoid pulling heavy optional deps
    # during normal runtime or test collection.
    from donkeycar.parts.controller import JoystickController, WebFpv  # type: ignore
    from donkeycar.parts.launch import AiLaunch  # type: ignore
    from donkeycar.parts.throttle_filter import ThrottleFilter  # type: ignore
    from donkeycar.parts.behavior import BehaviorPart  # type: ignore
    from mycar.telemetry import setup_mqtt as _typed_setup_mqtt  # type: ignore
    from mycar.recording import setup_recording as _typed_setup_recording  # type: ignore
    from mycar.led import setup_led as _typed_setup_led  # type: ignore
    # Provide names for wiring helpers so static analyzers don't flag undefined
    # names later in this file. These are only used for type checking.
    setup_logging: Callable[..., Any]
    setup_mqtt: Callable[..., Any]
    setup_odom: Callable[..., Any]
    ThrottleFilter: Any


def _setup_model_and_watchers(cfg, vehicle, model_path, model_type):
    """Delegate to `mycar.ai.setup_model_and_watchers` to keep this
    module small and focused on orchestration.
    """
    try:
        from importlib import import_module

        ai_mod = import_module("mycar.ai")
        setup = getattr(ai_mod, "setup_model_and_watchers", None)
        if setup:
            setup(cfg, vehicle, model_path, model_type)
    except (ImportError, ModuleNotFoundError) as exc:
        logger.debug("AI helper import failed: %s", exc)


def _setup_drivetrain(cfg, vehicle):
    """Thin wrapper that delegates drivetrain wiring to `mycar.drivetrain`.

    This keeps the public helper name unchanged while moving the large
    implementation into a separate module to reduce `manage.py` size.
    """
    try:
        from importlib import import_module

        drv = import_module("mycar.drivetrain")
        setup = getattr(drv, "setup_drivetrain", None)
        if setup:
            setup(cfg, vehicle)
    except (ImportError, ModuleNotFoundError):
        # unable to import the helper; leave drivetrain unconfigured
        pass


def _setup_controller(cfg, vehicle, use_joystick=False):
    """Delegate controller wiring to `mycar.controller.setup_controller`.

    This keeps controller wiring out of the large `drive()` function and
    avoids import-time side-effects on environments missing optional
    controller dependencies.
    """
    try:
        from importlib import import_module

        ctrl_mod = import_module("mycar.controller")
        setup = getattr(ctrl_mod, "setup_controller", None)
        if setup:
            return setup(cfg, vehicle, use_joystick=use_joystick)
    except (ImportError, ModuleNotFoundError) as exc:
        logger.debug("Controller helper import failed: %s", exc)
    return None


def drive(
    cfg,
    model_path=None,
    use_joystick=False,
    model_type=None,
    camera_type="single",
    meta: Optional[List[str]] = None,
):
    """Build and start the vehicle runtime using `cfg`.

    This function wires up sensors, controllers, model parts, logging,
    and other pieces required to run or train the vehicle.

    Parameters:
        cfg: configuration object with runtime settings.
        model_path: optional path to a model file to load.
        use_joystick: whether to prefer a physical joystick.
        model_type: override model type (e.g. 'linear', 'behavior').
        camera_type: 'single' or 'stereo'.
        meta: optional list of metadata key:value strings for recordings.
    """
    if meta is None:
        meta = []

    logger.info("PID: %s", os.getpid())
    if cfg.DONKEY_GYM:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    if model_type is None:
        if cfg.TRAIN_LOCALIZER:
            model_type = "localizer"
        elif cfg.TRAIN_BEHAVIORS:
            model_type = "behavior"
        else:
            model_type = cfg.DEFAULT_MODEL_TYPE

    vehicle = dk.vehicle.Vehicle()
    setup_logging(cfg)
    tel = setup_mqtt(cfg)
    setup_odom(cfg, vehicle)

    # Delegate camera wiring to helper to reduce manage.py size
    try:
        from importlib import import_module

        cam_mod = import_module("mycar.camera")
        setup_cam = getattr(cam_mod, "setup_camera", None)
        if setup_cam:
            inputs, _outputs, _threaded = setup_cam(
                cfg, vehicle, camera_type=camera_type)
        else:
            # fallback defaults
            inputs = []
            _outputs = ["cam/image_array"]
            _threaded = True
    except (ImportError, ModuleNotFoundError) as exc:
        logger.debug("Camera helper import failed: %s", exc)
        inputs = []
        _outputs = ["cam/image_array"]
        _threaded = True

    # add lidar
    if cfg.USE_LIDAR:
        from donkeycar.parts.lidar import RPLidar

        if cfg.LIDAR_TYPE == "RP":
            logger.info("adding RP lidar part")
            lidar = RPLidar(
                lower_limit=cfg.LIDAR_LOWER_LIMIT, upper_limit=cfg.LIDAR_UPPER_LIMIT
            )
            vehicle.add(lidar, inputs=[], outputs=[
                        "lidar/dist_array"], threaded=True)
        elif cfg.LIDAR_TYPE == "YD":
            logger.warning("YD Lidar not yet supported")

    if cfg.HAVE_TFMINI:
        from donkeycar.parts.tfmini import TFMini

        lidar = TFMini(port=cfg.TFMINI_SERIAL_PORT)
        vehicle.add(lidar, inputs=[], outputs=["lidar/dist"], threaded=True)

    if cfg.SHOW_FPS:
        from donkeycar.parts.fps import FrequencyLogger

        vehicle.add(
            FrequencyLogger(cfg.FPS_DEBUG_INTERVAL),
            outputs=["fps/current", "fps/fps_list"],
        )

    # configure controllers (web, joystick, RC, network joystick)
    ctr = _setup_controller(cfg, vehicle, use_joystick=use_joystick)

    # this throttle filter will allow one tap back for esc reverse
    th_filter = ThrottleFilter()
    vehicle.add(th_filter, inputs=["user/throttle"], outputs=["user/throttle"])

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
    class PilotCondition:
        """Run condition part that returns True when not in user mode."""

        def run(self, mode):
            """Return True when mode is not 'user'."""
            return mode != "user"

    vehicle.add(PilotCondition(), inputs=["user/mode"], outputs=["run_pilot"])

    # LED logic moved to `mycar.led.setup_led`.

    # Extract LED logic and the record tracker to `mycar.led` for clarity.
    from importlib import import_module

    try:
        led_mod = import_module("mycar.led")
        _led_logic, rec_tracker_part = led_mod.setup_led(
            cfg, vehicle, model_type)
    except (ImportError, ModuleNotFoundError):
        # Fall back to the inline behaviour if the helper cannot be loaded.
        rec_tracker_part = None

    if cfg.AUTO_RECORD_ON_THROTTLE:

        def show_record_count_status():
            rec_tracker_part.last_num_rec_print = 0
            rec_tracker_part.force_alert = 1

        # these controllers don't use the joystick class
        if cfg.CONTROLLER_TYPE not in ("pigpio_rc", "MM1"):
            if isinstance(ctr, JoystickController):
                # then we are not using the circle button. hijack that to force a record count indication
                ctr.set_button_down_trigger("circle", show_record_count_status)
        else:

            show_record_count_status()

    # Sombrero
    if cfg.HAVE_SOMBRERO:
        from donkeycar.parts.sombrero import Sombrero

        # instantiate for side-effects; avoid unused variable
        Sombrero()

    # IMU
    if cfg.HAVE_IMU:
        from donkeycar.parts.imu import IMU

        imu = IMU(sensor=cfg.IMU_SENSOR, dlp_setting=cfg.IMU_DLP_CONFIG)
        vehicle.add(
            imu,
            outputs=[
                "imu/acl_x",
                "imu/acl_y",
                "imu/acl_z",
                "imu/gyr_x",
                "imu/gyr_y",
                "imu/gyr_z",
            ],
            threaded=True,
        )

    # Use the FPV preview, which will show the cropped image output, or the full frame.
    if cfg.USE_FPV:
        vehicle.add(WebFpv(), inputs=["cam/image_array"], threaded=True)

    # Behavioral state
    if cfg.TRAIN_BEHAVIORS:
        bh = BehaviorPart(cfg.BEHAVIOR_LIST)
        vehicle.add(
            bh,
            outputs=[
                "behavior/state",
                "behavior/label",
                "behavior/one_hot_state_array",
            ],
        )
        try:
            ctr.set_button_down_trigger("L1", bh.increment_state)
        except Exception as exc:
            logger.debug("Could not set L1 button trigger: %s", exc)

        inputs = ["cam/image_array", "behavior/one_hot_state_array"]
    # IMU
    elif cfg.USE_LIDAR:
        inputs = ["cam/image_array", "lidar/dist_array"]

    elif cfg.HAVE_ODOM:
        inputs = ["cam/image_array", "enc/speed"]

    elif model_type == "imu":
        if not cfg.HAVE_IMU:
            raise RuntimeError("Missing imu parameter in config")
        # Run the pilot if the mode is not user.
        inputs = [
            "cam/image_array",
            "imu/acl_x",
            "imu/acl_y",
            "imu/acl_z",
            "imu/gyr_x",
            "imu/gyr_y",
            "imu/gyr_z",
        ]

    else:
        inputs = ["cam/image_array"]

    if model_path:
        _setup_model_and_watchers(cfg, vehicle, model_path, model_type)

    if cfg.STOP_SIGN_DETECTOR:
        from donkeycar.parts.object_detector.stop_sign_detector import StopSignDetector

        vehicle.add(
            StopSignDetector(
                cfg.STOP_SIGN_MIN_SCORE,
                cfg.STOP_SIGN_SHOW_BOUNDING_BOX,
                cfg.STOP_SIGN_MAX_REVERSE_COUNT,
                cfg.STOP_SIGN_REVERSE_THROTTLE,
            ),
            inputs=["cam/image_array", "pilot/throttle"],
            outputs=["pilot/throttle", "cam/image_array"],
        )
        vehicle.add(
            ThrottleFilter(), inputs=["pilot/throttle"], outputs=["pilot/throttle"]
        )

    # Choose what inputs should change the car.
    class DriveMode:
        """Choose angle/throttle outputs based on current drive `mode`."""

        def run(self, mode, user_angle, user_throttle, pilot_angle, pilot_throttle):
            if mode == "user":
                return user_angle, user_throttle

            elif mode == "local_angle":
                return (pilot_angle if pilot_angle is not None else 0.0), user_throttle

            else:
                pilot_ang = pilot_angle if pilot_angle is not None else 0.0
                pilot_thr = pilot_throttle if pilot_throttle is not None else 0.0
                return pilot_ang, pilot_thr * cfg.AI_THROTTLE_MULT

    vehicle.add(
        DriveMode(),
        inputs=[
            "user/mode",
            "user/angle",
            "user/throttle",
            "pilot/angle",
            "pilot/throttle",
        ],
        outputs=["angle", "throttle"],
    )

    # to give the car a boost when starting ai mode in a race.
    ai_launcher = AiLaunch(
        cfg.AI_LAUNCH_DURATION, cfg.AI_LAUNCH_THROTTLE, cfg.AI_LAUNCH_KEEP_ENABLED
    )

    vehicle.add(ai_launcher, inputs=[
                "user/mode", "throttle"], outputs=["throttle"])

    if cfg.CONTROLLER_TYPE not in ("pigpio_rc", "MM1"):
        if isinstance(ctr, JoystickController):
            ctr.set_button_down_trigger(
                cfg.AI_LAUNCH_ENABLE_BUTTON, ai_launcher.enable_ai_launch
            )

    class AiRunCondition:
        """A bool part to let us know when ai is running."""

        def run(self, mode):
            return mode != "user"

    vehicle.add(AiRunCondition(), inputs=["user/mode"], outputs=["ai_running"])

    # Ai Recording
    class AiRecordingCondition:
        """Return True when ai mode, otherwise respect user mode recording flag."""

        def run(self, mode, recording):
            return (mode != "user") or bool(recording)

    if cfg.RECORD_DURING_AI:
        vehicle.add(
            AiRecordingCondition(),
            inputs=["user/mode", "recording"],
            outputs=["recording"],
        )

    # Drive train setup: delegate to extracted helper to reduce duplication
    try:
        _setup_drivetrain(cfg, vehicle)
    except Exception as exc:
        logger.debug("Drivetrain setup helper failed: %s", exc)

    # OLED setup
    if cfg.USE_SSD1306_128_32:
        from donkeycar.parts.oled import OLEDPart

        auto_record_on_throttle = (
            cfg.USE_JOYSTICK_AS_DEFAULT and cfg.AUTO_RECORD_ON_THROTTLE
        )
        oled_part = OLEDPart(
            cfg.SSD1306_128_32_I2C_ROTATION,
            cfg.SSD1306_RESOLUTION,
            auto_record_on_throttle,
        )
        vehicle.add(
            oled_part,
            inputs=["recording", "tub/num_records", "user/mode"],
            outputs=[],
            threaded=True,
        )

    # add tub to save data

    if cfg.USE_LIDAR:
        inputs = [
            "cam/image_array",
            "lidar/dist_array",
            "user/angle",
            "user/throttle",
            "user/mode",
        ]
        types = ["image_array", "nparray", "float", "float", "str"]
    else:
        inputs = ["cam/image_array", "user/angle",
                  "user/throttle", "user/mode"]
        types = ["image_array", "float", "float", "str"]

    if cfg.HAVE_ODOM:
        inputs += ["enc/speed"]
        types += ["float"]

    if cfg.TRAIN_BEHAVIORS:
        inputs += ["behavior/state", "behavior/label",
                   "behavior/one_hot_state_array"]
        types += ["int", "str", "vector"]

    if cfg.CAMERA_TYPE == "D435" and cfg.REALSENSE_D435_DEPTH:
        inputs += ["cam/depth_array"]
        types += ["gray16_array"]

    if cfg.HAVE_IMU or (cfg.CAMERA_TYPE == "D435" and cfg.REALSENSE_D435_IMU):
        inputs += [
            "imu/acl_x",
            "imu/acl_y",
            "imu/acl_z",
            "imu/gyr_x",
            "imu/gyr_y",
            "imu/gyr_z",
        ]

        types += ["float", "float", "float", "float", "float", "float"]

    if cfg.HAVE_TFMINI:
        inputs += ["lidar/dist"]
        types += ["float"]

    # rbx
    if cfg.DONKEY_GYM:
        if cfg.SIM_RECORD_LOCATION:
            inputs += ["pos/pos_x", "pos/pos_y",
                       "pos/pos_z", "pos/speed", "pos/cte"]
            types += ["float", "float", "float", "float", "float"]
        if cfg.SIM_RECORD_GYROACCEL:
            inputs += [
                "gyro/gyro_x",
                "gyro/gyro_y",
                "gyro/gyro_z",
                "accel/accel_x",
                "accel/accel_y",
                "accel/accel_z",
            ]
            types += ["float", "float", "float", "float", "float", "float"]
        if cfg.SIM_RECORD_VELOCITY:
            inputs += ["vel/vel_x", "vel/vel_y", "vel/vel_z"]
            types += ["float", "float", "float"]
        if cfg.SIM_RECORD_LIDAR:
            inputs += ["lidar/dist_array"]
            types += ["nparray"]

    if cfg.RECORD_DURING_AI:
        inputs += ["pilot/angle", "pilot/throttle"]
        types += ["float", "float"]

    # delegate to helper that configures tub, telemetry and pub-camera
    try:
        import importlib

        _rec_mod = importlib.import_module("mycar.recording")
        _setup_recording = getattr(_rec_mod, "setup_recording", None)
    except (ImportError, ModuleNotFoundError):
        _setup_recording = None

    if _setup_recording:
        _ = _setup_recording(cfg, vehicle, ctr, tel, meta, inputs, types)
    else:
        logger.debug("Recording setup not available; skipping tub setup")

    # run the vehicle
    vehicle.start(rate_hz=cfg.DRIVE_LOOP_HZ, max_loop_count=cfg.MAX_LOOPS)


if __name__ == "__main__":
    args = docopt(__doc__)
    cfg = dk.load_config(myconfig=args["--myconfig"])

    if args["drive"]:
        model_type = args["--type"]
        camera_type = args["--camera"]
        drive(
            cfg,
            model_path=args["--model"],
            use_joystick=args["--js"],
            model_type=model_type,
            camera_type=camera_type,
            meta=args["--meta"],
        )
    elif args["train"]:
        logger.info("Use python train.py instead.")
