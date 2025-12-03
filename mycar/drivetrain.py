"""Drivetrain setup extracted from `mycar.manage`.

Contains `setup_drivetrain(cfg, vehicle)` which configures and adds the
appropriate actuator parts based on `cfg.DRIVE_TRAIN_TYPE`.
"""

# Quick lint mitigation: actuator/pins imports may be optional on CI
# and can produce import-error. Keep this module importable in tests.
# pylint: disable=import-error,too-many-lines

import logging
from typing import Any
from donkeycar.parts import actuator, pins

logger = logging.getLogger(__name__)


def setup_drivetrain(cfg: Any, vehicle: Any) -> None:
    """Configure and add drivetrain parts to `vehicle` based on `cfg`."""
    if cfg.DONKEY_GYM or cfg.DRIVE_TRAIN_TYPE == "MOCK":
        return

    if cfg.DRIVE_TRAIN_TYPE == "PWM_STEERING_THROTTLE":
        from donkeycar.parts.actuator import PWMSteering, PWMThrottle, PulseController

        dt = cfg.PWM_STEERING_THROTTLE
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
        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)

    elif cfg.DRIVE_TRAIN_TYPE == "I2C_SERVO":
        from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle

        steering_controller = PCA9685(
            cfg.STEERING_CHANNEL, cfg.PCA9685_I2C_ADDR, busnum=cfg.PCA9685_I2C_BUSNUM
        )
        steering = PWMSteering(
            controller=steering_controller,
            left_pulse=cfg.STEERING_LEFT_PWM,
            right_pulse=cfg.STEERING_RIGHT_PWM,
        )

        throttle_controller = PCA9685(
            cfg.THROTTLE_CHANNEL, cfg.PCA9685_I2C_ADDR, busnum=cfg.PCA9685_I2C_BUSNUM
        )
        throttle = PWMThrottle(
            controller=throttle_controller,
            max_pulse=cfg.THROTTLE_FORWARD_PWM,
            zero_pulse=cfg.THROTTLE_STOPPED_PWM,
            min_pulse=cfg.THROTTLE_REVERSE_PWM,
        )

        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)

    elif cfg.DRIVE_TRAIN_TYPE == "DC_STEER_THROTTLE":
        dt = cfg.DC_STEER_THROTTLE
        steering = actuator.L298N_HBridge_2pin(
            pins.pwm_pin_by_id(dt["LEFT_DUTY_PIN"]),
            pins.pwm_pin_by_id(dt["RIGHT_DUTY_PIN"]),
        )
        throttle = actuator.L298N_HBridge_2pin(
            pins.pwm_pin_by_id(dt["FWD_DUTY_PIN"]),
            pins.pwm_pin_by_id(dt["BWD_DUTY_PIN"]),
        )

        vehicle.add(steering, inputs=["angle"])
        vehicle.add(throttle, inputs=["throttle"])

    elif cfg.DRIVE_TRAIN_TYPE == "DC_TWO_WHEEL":
        dt = cfg.DC_TWO_WHEEL
        left_motor = actuator.L298N_HBridge_2pin(
            pins.pwm_pin_by_id(dt["LEFT_FWD_DUTY_PIN"]),
            pins.pwm_pin_by_id(dt["LEFT_BWD_DUTY_PIN"]),
        )
        right_motor = actuator.L298N_HBridge_2pin(
            pins.pwm_pin_by_id(dt["RIGHT_FWD_DUTY_PIN"]),
            pins.pwm_pin_by_id(dt["RIGHT_BWD_DUTY_PIN"]),
        )

        two_wheel_control = actuator.TwoWheelSteeringThrottle()

        vehicle.add(
            two_wheel_control,
            inputs=["throttle", "angle"],
            outputs=["left_motor_speed", "right_motor_speed"],
        )

        vehicle.add(left_motor, inputs=["left_motor_speed"])
        vehicle.add(right_motor, inputs=["right_motor_speed"])

    elif cfg.DRIVE_TRAIN_TYPE == "DC_TWO_WHEEL_L298N":
        dt = cfg.DC_TWO_WHEEL_L298N
        left_motor = actuator.L298N_HBridge_3pin(
            pins.output_pin_by_id(dt["LEFT_FWD_PIN"]),
            pins.output_pin_by_id(dt["LEFT_BWD_PIN"]),
            pins.pwm_pin_by_id(dt["LEFT_EN_DUTY_PIN"]),
        )
        right_motor = actuator.L298N_HBridge_3pin(
            pins.output_pin_by_id(dt["RIGHT_FWD_PIN"]),
            pins.output_pin_by_id(dt["RIGHT_BWD_PIN"]),
            pins.pwm_pin_by_id(dt["RIGHT_EN_DUTY_PIN"]),
        )

        two_wheel_control = actuator.TwoWheelSteeringThrottle()

        vehicle.add(
            two_wheel_control,
            inputs=["throttle", "angle"],
            outputs=["left_motor_speed", "right_motor_speed"],
        )

        vehicle.add(left_motor, inputs=["left_motor_speed"])
        vehicle.add(right_motor, inputs=["right_motor_speed"])

    elif cfg.DRIVE_TRAIN_TYPE == "SERVO_HBRIDGE_2PIN":
        from donkeycar.parts.actuator import PWMSteering, PWMThrottle, PulseController

        dt = cfg.SERVO_HBRIDGE_2PIN
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

        motor = actuator.L298N_HBridge_2pin(
            pins.pwm_pin_by_id(dt["FWD_DUTY_PIN"]),
            pins.pwm_pin_by_id(dt["BWD_DUTY_PIN"]),
        )

        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(motor, inputs=["throttle"])

    elif cfg.DRIVE_TRAIN_TYPE == "SERVO_HBRIDGE_3PIN":
        from donkeycar.parts.actuator import PWMSteering, PWMThrottle, PulseController

        dt = cfg.SERVO_HBRIDGE_3PIN
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

        motor = actuator.L298N_HBridge_3pin(
            pins.output_pin_by_id(dt["FWD_PIN"]),
            pins.output_pin_by_id(dt["BWD_PIN"]),
            pins.pwm_pin_by_id(dt["DUTY_PIN"]),
        )

        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(motor, inputs=["throttle"])

    elif cfg.DRIVE_TRAIN_TYPE == "SERVO_HBRIDGE_PWM":
        from donkeycar.parts.actuator import ServoBlaster, PWMSteering

        steering_controller = ServoBlaster(cfg.STEERING_CHANNEL)  # really pin
        # PWM pulse values should be in the range of 100 to 200
        if cfg.STEERING_LEFT_PWM > 200 or cfg.STEERING_RIGHT_PWM > 200:
            raise ValueError("STEERING PWM values should be <= 200")
        steering = PWMSteering(
            controller=steering_controller,
            left_pulse=cfg.STEERING_LEFT_PWM,
            right_pulse=cfg.STEERING_RIGHT_PWM,
        )

        from donkeycar.parts.actuator import Mini_HBridge_DC_Motor_PWM

        motor = Mini_HBridge_DC_Motor_PWM(
            cfg.HBRIDGE_PIN_FWD, cfg.HBRIDGE_PIN_BWD)

        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(motor, inputs=["throttle"])

    elif cfg.DRIVE_TRAIN_TYPE == "MM1":
        from donkeycar.parts.robohat import RoboHATDriver

        vehicle.add(RoboHATDriver(cfg), inputs=["angle", "throttle"])

    elif cfg.DRIVE_TRAIN_TYPE == "PIGPIO_PWM":
        from donkeycar.parts.actuator import PWMSteering, PWMThrottle, PiGPIO_PWM

        steering_controller = PiGPIO_PWM(
            cfg.STEERING_PWM_PIN,
            freq=cfg.STEERING_PWM_FREQ,
            inverted=cfg.STEERING_PWM_INVERTED,
        )
        steering = PWMSteering(
            controller=steering_controller,
            left_pulse=cfg.STEERING_LEFT_PWM,
            right_pulse=cfg.STEERING_RIGHT_PWM,
        )

        throttle_controller = PiGPIO_PWM(
            cfg.THROTTLE_PWM_PIN,
            freq=cfg.THROTTLE_PWM_FREQ,
            inverted=cfg.THROTTLE_PWM_INVERTED,
        )
        throttle = PWMThrottle(
            controller=throttle_controller,
            max_pulse=cfg.THROTTLE_FORWARD_PWM,
            zero_pulse=cfg.THROTTLE_STOPPED_PWM,
            min_pulse=cfg.THROTTLE_REVERSE_PWM,
        )
        vehicle.add(steering, inputs=["angle"], threaded=True)
        vehicle.add(throttle, inputs=["throttle"], threaded=True)

    elif cfg.DRIVE_TRAIN_TYPE == "VESC":
        from donkeycar.parts.actuator import VESC

        logger.info("Creating VESC at port %s", cfg.VESC_SERIAL_PORT)
        vesc = VESC(
            cfg.VESC_SERIAL_PORT,
            cfg.VESC_MAX_SPEED_PERCENT,
            cfg.VESC_HAS_SENSOR,
            cfg.VESC_START_HEARTBEAT,
            cfg.VESC_BAUDRATE,
            cfg.VESC_TIMEOUT,
            cfg.VESC_STEERING_SCALE,
            cfg.VESC_STEERING_OFFSET,
        )
        vehicle.add(vesc, inputs=["angle", "throttle"])
