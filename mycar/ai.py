"""AI / model loading helpers extracted from `manage.py`.

Provides `setup_model_and_watchers(cfg, vehicle, model_path, model_type)` which
creates the model part, loads the model/weights and wires file watchers that
trigger safe reloads while AI is running.
"""

# Quick lint mitigation: some imports (tensorflow, file_watcher) are optional
# and can trigger import errors on CI/dev machines. Keep the module safe.
# pylint: disable=import-error,too-many-lines

from typing import Any
import time
import logging

import donkeycar as dk

logger = logging.getLogger(__name__)


def setup_model_and_watchers(cfg: Any, vehicle: Any, model_path: str, model_type: str) -> None:
    """Set up model part and filesystem watchers for reloads.

    This is a direct extraction of the logic previously embedded in
    `mycar.manage._setup_model_and_watchers`.
    """

    def load_model(kl, model_path_inner):
        start = time.time()
        logger.info("loading model %s", model_path_inner)
        kl.load(model_path_inner)
        logger.info("finished loading in %.3f sec.", (time.time() - start))

    def load_weights(kl, weights_path):
        start = time.time()
        try:
            logger.info("loading model weights %s", weights_path)
            kl.model.load_weights(weights_path)
            logger.info("finished loading in %.3f sec.", (time.time() - start))
        except (OSError, ValueError, ImportError, TypeError) as exc:
            logger.exception(
                "ERR>> problems loading weights %s: %s", weights_path, exc)

    def load_model_json(kl, json_fnm):
        start = time.time()
        logger.info("loading model json %s", json_fnm)
        from tensorflow.python import keras

        try:
            with open(json_fnm, "r", encoding="utf-8") as handle:
                contents = handle.read()
                kl.model = keras.models.model_from_json(contents)
            logger.info("finished loading json in %.3f sec.",
                        (time.time() - start))
        except (OSError, ValueError, ImportError, TypeError) as exc:
            logger.exception(
                "ERR>> problems loading model json %s: %s", json_fnm, exc)

    # When we have a model, first create an appropriate Keras part
    kl = dk.utils.get_model_by_type(model_type, cfg)

    model_reload_cb = None

    mp = model_path.lower()
    if mp.endswith((".h5", ".trt", ".tflite", ".savedmodel", ".pth")):
        # load the whole model with weights, etc
        load_model(kl, model_path)

        def reload_model(filename):
            load_model(kl, filename)

        model_reload_cb = reload_model

    elif model_path.lower().endswith(".json"):
        # load the model from there and look for a matching .weights file
        load_model_json(kl, model_path)
        weights_path = model_path.replace(".json", ".weights")
        load_weights(kl, weights_path)

        def reload_weights(filename):
            weights_path_inner = filename.replace(".json", ".weights")
            load_weights(kl, weights_path_inner)

        model_reload_cb = reload_weights

    else:
        logger.error(
            "ERR>> Unknown extension type on model file: %s", model_path)
        return

    # Lazy import of parts that may have optional/hardware deps
    from donkeycar.parts.file_watcher import FileWatcher
    from donkeycar.parts.transform import DelayedTrigger, TriggeredCallback

    # this part will signal visual LED, if connected
    vehicle.add(FileWatcher(model_path, verbose=True),
                outputs=["modelfile/modified"])

    # these parts will reload the model file, but only when ai is running
    # so we don't interrupt user driving
    vehicle.add(FileWatcher(model_path), outputs=[
                "modelfile/dirty"], run_condition="ai_running")
    vehicle.add(DelayedTrigger(100), inputs=[
                "modelfile/dirty"], outputs=["modelfile/reload"], run_condition="ai_running")
    vehicle.add(TriggeredCallback(model_path, model_reload_cb), inputs=[
                "modelfile/reload"], run_condition="ai_running")

    outputs = ["pilot/angle", "pilot/throttle"]
    if getattr(cfg, "TRAIN_LOCALIZER", False):
        outputs.append("pilot/loc")

    # Add image transformations like crop or trapezoidal mask
    if hasattr(cfg, "TRANSFORMATIONS") and cfg.TRANSFORMATIONS:
        from donkeycar.pipeline.augmentations import ImageAugmentation

        vehicle.add(
            ImageAugmentation(cfg, "TRANSFORMATIONS"),
            inputs=["cam/image_array"],
            outputs=["cam/image_array_trans"],
        )
        _inputs = ["cam/image_array_trans"] + ["cam/image_array"][1:]

    vehicle.add(kl, inputs=["cam/image_array"],
                outputs=outputs, run_condition="run_pilot")
