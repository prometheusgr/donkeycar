"""Recording and tub helpers used by `mycar.manage.drive`."""

# Some exceptions are broad intentionally during wiring to allow the
# runtime to proceed on systems missing optional hardware or libraries.
# Keep broad-except here for wiring-time resilience.
# pylint: disable=broad-except
from typing import List, Any, Optional, TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:  # pragma: no cover - typing only
    from donkeycar.parts.controller import LocalWebController, JoystickController  # type: ignore


# The function accepts several wiring parameters; keep a local pylint
# disable for the argument count since this is orchestration code.
def setup_recording(  # pylint: disable=too-many-arguments
    cfg: Any,
    vehicle: Any,
    ctr: Any,
    tel: Any,
    meta: List[str],
    inputs: list,
    types: list,
) -> Optional[object]:
    """Configure data recording (TubWriter), telemetry and related parts.

    Returns the created TubWriter or ``None`` on failure. The function
    keeps import-time side-effects local to avoid requiring optional
    hardware modules at module import time.
    """
    # Perf monitor
    if getattr(cfg, "HAVE_PERFMON", False):
        try:
            from donkeycar.parts.perfmon import PerfMonitor

            mon = PerfMonitor(cfg)
            perfmon_outputs = ["perf/cpu", "perf/mem", "perf/freq"]
            inputs += perfmon_outputs
            types += ["float", "float", "float"]
            vehicle.add(mon, inputs=[], outputs=perfmon_outputs, threaded=True)
        except Exception as exc:
            logger.debug("PerfMonitor not available: %s", exc)

    # create or reuse tub path
    from donkeycar.parts.datastore import TubHandler
    from donkeycar.parts.tub_v2 import TubWriter

    tub_path = (
        TubHandler(path=cfg.DATA_PATH).create_tub_path()
        if getattr(cfg, "AUTO_CREATE_NEW_TUB", False)
        else cfg.DATA_PATH
    )
    meta += getattr(cfg, "METADATA", [])
    tub_writer = TubWriter(tub_path, inputs=inputs, types=types, metadata=meta)
    vehicle.add(
        tub_writer,
        inputs=inputs,
        outputs=["tub/num_records"],
        run_condition="recording",
    )

    # telemetry wiring (add queue size publisher)
    if getattr(cfg, "HAVE_MQTT_TELEMETRY", False) and tel is not None:
        try:
            telem_inputs, _ = tel.add_step_inputs(inputs, types)
            vehicle.add(
                tel, inputs=telem_inputs, outputs=["tub/queue_size"], threaded=True
            )
        except Exception as exc:
            logger.debug("Failed to add telemetry part: %s", exc)

    # publish camera images over network if requested
    if getattr(cfg, "PUB_CAMERA_IMAGES", False):
        try:
            from donkeycar.parts.network import TCPServeValue
            from donkeycar.parts.image import ImgArrToJpg

            pub = TCPServeValue("camera")
            vehicle.add(ImgArrToJpg(), inputs=[
                        "cam/image_array"], outputs=["jpg/bin"])
            vehicle.add(pub, inputs=["jpg/bin"])
        except Exception as exc:
            logger.debug("Pub camera images disabled: %s", exc)

    # controller user-facing messages and joystick tub wiring
    try:
        from donkeycar.parts.controller import LocalWebController, JoystickController
    except Exception:
        LocalWebController = JoystickController = object

    if isinstance(ctr, LocalWebController):
        if getattr(cfg, "DONKEY_GYM", False):
            logger.info(
                "You can now go to http://localhost:%d to drive your car.",
                cfg.WEB_CONTROL_PORT,
            )
        else:
            logger.info(
                "You can now go to <your hostname.local>:%d to drive your car.",
                cfg.WEB_CONTROL_PORT,
            )
    elif getattr(cfg, "CONTROLLER_TYPE", None) not in ("pigpio_rc", "MM1"):
        if isinstance(ctr, JoystickController):
            logger.info("You can now move your joystick to drive your car.")
            try:
                ctr.set_tub(tub_writer.tub)
            except Exception:
                logger.debug("joystick controller does not support set_tub")
            try:
                ctr.print_controls()
            except Exception:
                logger.debug(
                    "joystick controller does not support print_controls")

    return tub_writer
