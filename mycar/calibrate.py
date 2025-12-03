#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car

Usage:
    manage.py (drive)


Options:
    -h --help          Show this screen.
"""

from socket import gethostname
from docopt import docopt
import donkeycar as dk
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle, PulseController
from donkeycar.parts.controller import LocalWebController
from donkeycar.parts.throttle_filter import ThrottleFilter
from donkeycar.parts import pins


def drive(config):
    """
    Construct a working robotic vehicle from many parts.
    Each part runs as a job in the Vehicle loop, calling either
    it's run or run_threaded method depending on the constructor flag `threaded`.
    All parts are updated one after another at the framerate given in
    config.DRIVE_LOOP_HZ assuming each part finishes processing in a timely manner.
    Parts may have named outputs and inputs. The framework handles passing named outputs
    to parts requesting the same named input.
    """

    # Initialize car
    vehicle = dk.vehicle.Vehicle()

    ctr = LocalWebController(port=config.WEB_CONTROL_PORT)
    vehicle.add(
        ctr,
        inputs=["cam/image_array", "tub/num_records"],
        outputs=["angle", "throttle", "user/mode", "recording"],
        threaded=True,
    )

    # this throttle filter will allow one tap back for esc reverse
    th_filter = ThrottleFilter()
    vehicle.add(th_filter, inputs=["throttle"], outputs=["throttle"])

    drive_train = None

    # Drive train setup
    if config.DONKEY_GYM or config.DRIVE_TRAIN_TYPE == "MOCK":
        pass  # no drive train for sim or mock mode

    elif config.DRIVE_TRAIN_TYPE == "PWM_STEERING_THROTTLE":
        #
        # drivetrain for RC car with servo and ESC.
        # using a PwmPin for steering (servo)
        # and as second PwmPin for throttle (ESC)
        #
        dt = config.PWM_STEERING_THROTTLE
        steering_controller = PulseController(
            pwm_pin=pins.pwm_pin_by_id(dt["PWM_STEERING_PIN"]),
            pwm_scale=dt["PWM_STEERING_SCALE"],
            pwm_inverted=dt["PWM_STEERING_INVERTED"],
        )
        steering = PWMSteering(
            controller=steering_controller,
            left_pulse=dt["STEERING_LEFT_PWM"],
            right_pulse=dt["STEERING_RIGHT_PWM"],
        )

        throttle_controller = PulseController(
            pwm_pin=pins.pwm_pin_by_id(dt["PWM_THROTTLE_PIN"]),
            pwm_scale=dt["PWM_THROTTLE_SCALE"],
            pwm_inverted=dt["PWM_THROTTLE_INVERTED"],
        )
        throttle = PWMThrottle(
            controller=throttle_controller,
            max_pulse=dt["THROTTLE_FORWARD_PWM"],
            zero_pulse=dt["THROTTLE_STOPPED_PWM"],
            min_pulse=dt["THROTTLE_REVERSE_PWM"],
        )

        drive_train = {}
        drive_train["steering"] = steering
        drive_train["throttle"] = throttle

        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)
    elif config.DRIVE_TRAIN_TYPE == "I2C_SERVO":
        steering_controller = PCA9685(
            config.STEERING_CHANNEL,
            config.PCA9685_I2C_ADDR,
            busnum=config.PCA9685_I2C_BUSNUM,
        )
        steering = PWMSteering(
            controller=steering_controller,
            left_pulse=config.STEERING_LEFT_PWM,
            right_pulse=config.STEERING_RIGHT_PWM,
        )

        throttle_controller = PCA9685(
            config.THROTTLE_CHANNEL,
            config.PCA9685_I2C_ADDR,
            busnum=config.PCA9685_I2C_BUSNUM,
        )
        throttle = PWMThrottle(
            controller=throttle_controller,
            max_pulse=config.THROTTLE_FORWARD_PWM,
            zero_pulse=config.THROTTLE_STOPPED_PWM,
            min_pulse=config.THROTTLE_REVERSE_PWM,
        )

        drive_train = {}
        drive_train["steering"] = steering
        drive_train["throttle"] = throttle
        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)

    elif config.DRIVE_TRAIN_TYPE == "MM1":
        from donkeycar.parts.robohat import RoboHATDriver

        drive_train = RoboHATDriver(config)
        vehicle.add(drive_train, inputs=["angle", "throttle"])

    # TODO: monkeypatching is bad!!!
    ctr.drive_train = drive_train
    ctr.drive_train_type = config.DRIVE_TRAIN_TYPE

    print(f"Go to http://{gethostname()}.local:{ctr.port}/calibrate to " f"calibrate ")

    vehicle.start(rate_hz=config.DRIVE_LOOP_HZ, max_loop_count=config.MAX_LOOPS)


if __name__ == "__main__":
    args = docopt(__doc__)
    cfg = dk.load_config()

    if args["drive"]:
        drive(cfg)
