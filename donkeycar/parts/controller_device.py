"""Low-level joystick and device helpers extracted from `controller.py`.

This module contains hardware/device-specific classes (joystick adapters,
RC receiver) so the main controller implementation can be split into
smaller, more focused modules.
"""

from __future__ import annotations

import os
import array
import struct
import logging

logger = logging.getLogger(__name__)


# Provide a lightweight pigpio fallback when the real module isn't available,
# so RCReceiver can be imported on non-Raspberry Pi systems for testing.
try:
    import pigpio  # type: ignore
except ImportError:
    logger.warning('pigpio module not available; using fallback stub')

    class _FakeCB:
        def cancel(self):
            return None

    class _FakePi:
        def set_mode(self, _pin, _mode):
            return None

        def callback(self, _pin, _edge, _func):
            # Return a fake callback object with cancel()
            return _FakeCB()

    class _FakePigpioModule:
        INPUT = 0
        EITHER_EDGE = 1

        def pi(self):
            return _FakePi()

        @staticmethod
        def tick_diff(high, tick):
            if high is None or tick is None:
                return 0
            try:
                return high - tick
            except (TypeError, ValueError):
                return 0

    pigpio = _FakePigpioModule()


class Joystick:
    '''
    An interface to a physical joystick.
    '''

    def __init__(self, dev_fn: str = '/dev/input/js0') -> None:
        self.axis_states = {}
        self.button_states = {}
        self.axis_names = {}
        self.button_names = {}
        self.axis_map = []
        self.button_map = []
        self.jsdev = None
        self.dev_fn = dev_fn
        self.num_axes = 0
        self.num_buttons = 0
        self.js_name = ''

    def init(self) -> bool:
        try:
            from fcntl import ioctl
        except ModuleNotFoundError:
            logger.warning(
                "no support for fnctl module. joystick not enabled.")
            return False

        if not os.path.exists(self.dev_fn):
            logger.warning("%s is missing", self.dev_fn)
            return False

        logger.info("Opening %s...", self.dev_fn)
        self.jsdev = open(self.dev_fn, 'rb')

        buf = array.array('B', [0] * 64)
        ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf)
        self.js_name = buf.tobytes().decode('utf-8')
        logger.info("Device name: %s", self.js_name)

        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a11, buf)  # JSIOCGAXES
        self.num_axes = buf[0]

        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a12, buf)  # JSIOCGBUTTONS
        self.num_buttons = buf[0]

        buf = array.array('B', [0] * 0x40)
        ioctl(self.jsdev, 0x80406a32, buf)  # JSIOCGAXMAP

        for axis in buf[: self.num_axes]:
            axis_name = self.axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        buf = array.array('H', [0] * 200)
        ioctl(self.jsdev, 0x80406a34, buf)  # JSIOCGBTNMAP

        for btn in buf[: self.num_buttons]:
            btn_name = self.button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

        return True

    def show_map(self) -> None:
        print('%d axes found: %s' % (self.num_axes, ', '.join(self.axis_map)))
        print('%d buttons found: %s' %
              (self.num_buttons, ', '.join(self.button_map)))

    def poll(self):
        button = None
        button_state = None
        axis = None
        axis_val = None

        if self.jsdev is None:
            return button, button_state, axis, axis_val

        evbuf = self.jsdev.read(8)

        if evbuf:
            _tval, value, typev, number = struct.unpack('IhBB', evbuf)

            if typev & 0x80:
                return button, button_state, axis, axis_val

            if typev & 0x01:
                button = self.button_map[number]
                if button:
                    self.button_states[button] = value
                    button_state = value
                    logger.info("button: %s state: %d", button, value)

            if typev & 0x02:
                axis = self.axis_map[number]
                if axis:
                    fvalue = value / 32767.0
                    self.axis_states[axis] = fvalue
                    axis_val = fvalue
                    logger.debug("axis: %s val: %f", axis, fvalue)

        return button, button_state, axis, axis_val


class PyGameJoystick:
    def __init__(
        self,
        poll_delay=0.0,
        throttle_scale=1.0,
        steering_scale=1.0,
        throttle_dir=-1.0,
        dev_fn='/dev/input/js0',
        auto_record_on_throttle=True,
        which_js=0,
    ) -> None:
        """
        Initialize PyGameJoystick.

        Parameters
        ----------
        poll_delay : float
            Polling delay (kept for API compatibility, not currently used)
        throttle_scale : float
            Throttle scale (kept for API compatibility, not currently used)
        steering_scale : float
            Steering scale (kept for API compatibility, not currently used)
        throttle_dir : float
            Throttle direction (kept for API compatibility, not currently used)
        dev_fn : str
            Device file path (kept for API compatibility, not currently used)
        auto_record_on_throttle : bool
            Auto record flag (kept for API compatibility, not currently used)
        which_js : int
            Which joystick index to use
        """
        # Suppress unused variable warnings - these parameters are kept for API compatibility
        _poll_delay = poll_delay
        _throttle_scale = throttle_scale
        _steering_scale = steering_scale
        _throttle_dir = throttle_dir
        _dev_fn = dev_fn
        _auto_record_on_throttle = auto_record_on_throttle

        try:
            import pygame  # type: ignore

            pygame.init()
            pygame.joystick.init()

            self.joystick = pygame.joystick.Joystick(which_js)
            self.joystick.init()
            name = self.joystick.get_name()
            logger.info("detected joystick device: %s", name)
        except ModuleNotFoundError:
            logger.warning('pygame not available; PyGameJoystick disabled')
            self.joystick = None
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.exception('pygame joystick initialization failed: %s', e)
            self.joystick = None

        if self.joystick is not None:
            self.axis_states = [0.0 for _ in range(
                self.joystick.get_numaxes())]
            self.button_states = [
                0 for _ in range(self.joystick.get_numbuttons() + self.joystick.get_numhats() * 4)
            ]
        else:
            self.axis_states = []
            self.button_states = []

        self.axis_names = {}
        self.button_names = {}
        self.dead_zone = 0.07
        for i in range(self.joystick.get_numaxes() if self.joystick else 0):
            self.axis_names[i] = i
        for i in range(self.joystick.get_numbuttons() + self.joystick.get_numhats() * 4 if self.joystick else 0):
            self.button_names[i] = i

    def _poll_axes(self):
        """Poll joystick axes and return axis info if changed."""
        axis = None
        axis_val = None
        for i in range(self.joystick.get_numaxes()):
            val = self.joystick.get_axis(i)
            if abs(val) < self.dead_zone:
                val = 0.0
            if self.axis_states[i] != val and i in self.axis_names:
                axis = self.axis_names[i]
                axis_val = val
                self.axis_states[i] = val
                logger.debug("axis: %s val: %f", axis, val)
        return axis, axis_val

    def _poll_buttons(self):
        """Poll joystick buttons and return button info if changed."""
        button = None
        button_state = None
        for i in range(self.joystick.get_numbuttons()):
            state = self.joystick.get_button(i)
            if self.button_states[i] != state:
                if i not in self.button_names:
                    logger.info("button: %d", i)
                    continue
                button = self.button_names[i]
                button_state = state
                self.button_states[i] = state
                logger.info("button: %s state: %d", button, state)
        return button, button_state

    def _poll_hats(self):
        """Poll joystick hats and return button info if changed."""
        button = None
        button_state = None
        for i in range(self.joystick.get_numhats()):
            hat = self.joystick.get_hat(i)
            horz, vert = hat
            i_btn = self.joystick.get_numbuttons() + (i * 4)
            states = (horz == -1, horz == 1, vert == -1, vert == 1)
            for state in states:
                state = int(state)
                if self.button_states[i_btn] != state:
                    if i_btn not in self.button_names:
                        logger.info("button: %d", i_btn)
                        continue
                    button = self.button_names[i_btn]
                    button_state = state
                    self.button_states[i_btn] = state
        return button, button_state

    def poll(self):
        try:
            import pygame  # type: ignore
        except ModuleNotFoundError:
            pygame = None

        button = None
        button_state = None
        axis = None
        axis_val = None

        if pygame is None or self.joystick is None:
            return button, button_state, axis, axis_val

        pygame.event.get()

        axis, axis_val = self._poll_axes()
        button, button_state = self._poll_buttons()
        hat_button, hat_button_state = self._poll_hats()
        if hat_button is not None:
            button = hat_button
            button_state = hat_button_state

        return button, button_state, axis, axis_val


# Simple device helpers
class Channel:
    def __init__(self, pin):
        self.pin = pin
        self.tick = None
        self.high_tick = None


class RCReceiver:
    MIN_OUT = -1
    MAX_OUT = 1

    def __init__(self, cfg, debug=False):
        self.pi = pigpio.pi()
        self.channels = [
            Channel(cfg.STEERING_RC_GPIO),
            Channel(cfg.THROTTLE_RC_GPIO),
            Channel(cfg.DATA_WIPER_RC_GPIO),
        ]
        self.min_pwm = 1000
        self.max_pwm = 2000
        self.oldtime = 0
        self.STEERING_MID = cfg.PIGPIO_STEERING_MID
        self.MAX_FORWARD = cfg.PIGPIO_MAX_FORWARD
        self.STOPPED_PWM = cfg.PIGPIO_STOPPED_PWM
        self.MAX_REVERSE = cfg.PIGPIO_MAX_REVERSE
        self.RECORD = cfg.AUTO_RECORD_ON_THROTTLE
        self.debug = debug
        self.mode = 'user'
        self.is_action = False
        self.invert = cfg.PIGPIO_INVERT
        self.jitter = cfg.PIGPIO_JITTER
        self.factor = (self.MAX_OUT - self.MIN_OUT) / \
            (self.max_pwm - self.min_pwm)
        self.cbs = []
        self.signals = [0, 0, 0]
        for channel in self.channels:
            self.pi.set_mode(channel.pin, pigpio.INPUT)
            self.cbs.append(self.pi.callback(
                channel.pin, pigpio.EITHER_EDGE, self.cbf))
            if self.debug:
                logger.info("RCReceiver gpio %d created", channel.pin)

    def cbf(self, gpio, level, tick):
        for channel in self.channels:
            if gpio == channel.pin:
                if level == 1:
                    channel.high_tick = tick
                elif level == 0:
                    if channel.high_tick is not None:
                        channel.tick = pigpio.tick_diff(
                            channel.high_tick, tick)

    def pulse_width(self, high):
        if high is not None:
            return high
        return 0.0

    def run(self, mode=None, recording=None):
        i = 0
        for channel in self.channels:
            self.signals[i] = (self.pulse_width(
                channel.tick) - self.min_pwm) * self.factor
            if self.invert:
                self.signals[i] = -self.signals[i] + self.MAX_OUT
            else:
                self.signals[i] += self.MIN_OUT
            i += 1
        if self.debug:
            logger.info(
                "RC CH1 signal:%s, RC CH2 signal:%s, RC CH3 signal:%s",
                round(self.signals[0], 3),
                round(self.signals[1], 3),
                round(self.signals[2], 3)
            )

        if (self.signals[2] - self.jitter) > 0:
            self.mode = 'local'
        else:
            self.mode = mode if mode is not None else 'user'

        if ((self.signals[1] - self.jitter) > 0) and self.RECORD:
            is_action = True
        else:
            is_action = recording if recording is not None else False
        return self.signals[0], self.signals[1], self.mode, is_action

    def shutdown(self):
        for cb in self.cbs:
            try:
                cb.cancel()
            except (AttributeError, RuntimeError) as e:
                logger.exception("Failed to cancel pigpio callback: %s", e)
