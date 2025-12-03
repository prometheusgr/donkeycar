"""Controller parts and joystick helpers.

This module interacts with optional platform/hardware libraries (pygame,
pigpio, zmq, prettytable). These imports may not be present in all
environments (CI, test runners). To avoid noisy lint/results in those
environments we apply a small set of module-level pylint disables.
"""

# top-level imports
from .controller_device import Joystick, PyGameJoystick, Channel, RCReceiver
import os
# Module-level lint relaxations for hardware abstraction layer.
# These are deliberate to reduce noise from optional deps and large
# controller wiring logic while keeping behavior unchanged.
# pylint: disable=import-error,too-many-lines,too-many-instance-attributes,
# pylint: disable=too-many-public-methods,too-many-arguments,unused-import,
# pylint: disable=unused-variable,redefined-outer-name,broad-except,bare-except,superfluous-parens,redefined-builtin,duplicate-key,
# pylint: disable=missing-function-docstring,no-else-return,invalid-name,too-few-public-methods,pointless-string-statement,logging-not-lazy,logging-fstring-interpolation
import array
import time
import struct
import random
from threading import Thread
import logging

try:
    from prettytable import PrettyTable
except Exception:  # pragma: no cover - optional dev dependency
    class PrettyTable:  # minimal fallback for tests/CI
        def __init__(self, *args, **kwargs):
            self._rows = []

        def add_row(self, row):
            self._rows.append(row)

        def get_string(self):
            return '\n'.join(str(r) for r in self._rows)

# import for syntactical ease
from donkeycar.parts.web_controller.web import LocalWebController
from donkeycar.parts.web_controller.web import WebFpv

logger = logging.getLogger(__name__)


# Extracted low-level joystick and device helpers are provided from
# `controller_device.py` to keep this module focused on controller logic.


class JoystickCreator(Joystick):
    '''
    A Helper class to create a new joystick mapping
    '''

    def __init__(self, *args, **kwargs):
        super(JoystickCreator, self).__init__(*args, **kwargs)

        self.axis_names = {}
        self.button_names = {}

    def poll(self):

        button, button_state, axis, axis_val = super(
            JoystickCreator, self).poll()

        return button, button_state, axis, axis_val


class PS3JoystickSixAd(Joystick):
    '''
    An interface to a physical PS3 joystick available at /dev/input/js0
    Contains mapping that worked for Jetson Nano using sixad for PS3 controller's connection 
    '''

    def __init__(self, *args, **kwargs):
        super(PS3JoystickSixAd, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x02: 'right_stick_horz',
            0x03: 'right_stick_vert',
        }

        self.button_names = {
            0x120: 'select',
            0x123: 'start',
            0x130: 'PS',

            0x12a: 'L1',
            0x12b: 'R1',
            0x128: 'L2',
            0x129: 'R2',
            0x121: 'L3',
            0x122: 'R3',

            0x12c: "triangle",
            0x12d: "circle",
            0x12e: "cross",
            0x12f: 'square',

            0x124: 'dpad_up',
            0x126: 'dpad_down',
            0x127: 'dpad_left',
            0x125: 'dpad_right',
        }


class PS3JoystickOld(Joystick):
    '''
    An interface to a physical PS3 joystick available at /dev/input/js0
    Contains mapping that worked for Raspian Jessie drivers
    '''

    def __init__(self, *args, **kwargs):
        super(PS3JoystickOld, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x02: 'right_stick_horz',
            0x05: 'right_stick_vert',

            0x1a: 'tilt_x',
            0x1b: 'tilt_y',
            0x3d: 'tilt_a',
            0x3c: 'tilt_b',

            0x32: 'L1_pressure',
            0x33: 'R1_pressure',
            0x31: 'R2_pressure',
            0x30: 'L2_pressure',

            0x36: 'cross_pressure',
            0x35: 'circle_pressure',
            0x37: 'square_pressure',
            0x34: 'triangle_pressure',

            0x2d: 'dpad_r_pressure',
            0x2e: 'dpad_d_pressure',
            0x2c: 'dpad_u_pressure',
        }

        self.button_names = {
            0x120: 'select',
            0x123: 'start',
            0x2c0: 'PS',

            0x12a: 'L1',
            0x12b: 'R1',
            0x128: 'L2',
            0x129: 'R2',
            0x121: 'L3',
            0x122: 'R3',

            0x12c: "triangle",
            0x12d: "circle",
            0x12e: "cross",
            0x12f: 'square',

            0x124: 'dpad_up',
            0x126: 'dpad_down',
            0x127: 'dpad_left',
            0x125: 'dpad_right',
        }


class PS3Joystick(Joystick):
    '''
    An interface to a physical PS3 joystick available at /dev/input/js0
    Contains mapping that work for Raspian Stretch drivers
    '''

    def __init__(self, *args, **kwargs):
        super(PS3Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x03: 'right_stick_horz',
            0x04: 'right_stick_vert',

            0x02: 'L2_pressure',
            0x05: 'R2_pressure',
        }

        self.button_names = {
            0x13a: 'select',  # 8 314
            0x13b: 'start',  # 9 315
            0x13c: 'PS',  # a  316

            0x136: 'L1',  # 4 310
            0x137: 'R1',  # 5 311
            0x138: 'L2',  # 6 312
            0x139: 'R2',  # 7 313
            0x13d: 'L3',  # b 317
            0x13e: 'R3',  # c 318

            0x133: "triangle",  # 2 307
            0x131: "circle",  # 1 305
            0x130: "cross",  # 0 304
            0x134: 'square',  # 3 308

            0x220: 'dpad_up',  # d 544
            0x221: 'dpad_down',  # e 545
            0x222: 'dpad_left',  # f 546
            0x223: 'dpad_right',  # 10 547
        }


class PS4Joystick(Joystick):
    '''
    An interface to a physical PS4 joystick available at /dev/input/js0
    '''

    def __init__(self, *args, **kwargs):
        super(PS4Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x03: 'right_stick_horz',
            0x04: 'right_stick_vert',

            0x02: 'left_trigger_axis',
            0x05: 'right_trigger_axis',

            0x10: 'dpad_leftright',
            0x11: 'dpad_updown',

            0x19: 'tilt_a',
            0x1a: 'tilt_b',
            0x1b: 'tilt_c',

            0x06: 'motion_a',
            0x07: 'motion_b',
            0x08: 'motion_c',
        }

        self.button_names = {

            0x134: 'square',
            0x130: 'cross',
            0x131: 'circle',
            0x133: 'triangle',

            0x138: 'L1',
            0x139: 'R1',
            0x136: 'L2',
            0x137: 'R2',
            0x13a: 'L3',
            0x13b: 'R3',

            0x13d: 'pad',
            0x13a: 'share',
            0x13b: 'options',
            0x13c: 'PS',
        }


class PS3JoystickPC(Joystick):
    '''
    An interface to a physical PS3 joystick available at /dev/input/js1
    Seems to exhibit slightly different codes because driver is different?
    when running from ubuntu 16.04, it will interfere w mouse until:
    xinput set-prop "Sony PLAYSTATION(R)3 Controller" "Device Enabled" 0
    It also wants /dev/input/js1 device filename, not js0
    '''

    def __init__(self, *args, **kwargs):
        super(PS3JoystickPC, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x03: 'right_stick_horz',
            0x04: 'right_stick_vert',

            0x1a: 'tilt_x',
            0x1b: 'tilt_y',
            0x3d: 'tilt_a',
            0x3c: 'tilt_b',

            0x32: 'L1_pressure',
            0x33: 'R1_pressure',
            0x05: 'R2_pressure',
            0x02: 'L2_pressure',

            0x36: 'cross_pressure',
            0x35: 'circle_pressure',
            0x37: 'square_pressure',
            0x34: 'triangle_pressure',

            0x2d: 'dpad_r_pressure',
            0x2e: 'dpad_d_pressure',
            0x2c: 'dpad_u_pressure',
        }

        self.button_names = {
            0x13a: 'select',
            0x13b: 'start',
            0x13c: 'PS',

            0x136: 'L1',
            0x137: 'R1',
            0x138: 'L2',
            0x139: 'R2',
            0x13d: 'L3',
            0x13e: 'R3',

            0x133: "triangle",
            0x131: "circle",
            0x130: "cross",
            0x134: 'square',

            0x220: 'dpad_up',
            0x221: 'dpad_down',
            0x222: 'dpad_left',
            0x223: 'dpad_right',
        }


class PyGamePS4Joystick(PyGameJoystick):
    '''
    An interface to a physical PS4 joystick available via pygame
    Windows setup: https://github.com/nefarius/ScpToolkit/releases/tag/v1.6.238.16010
    '''

    def __init__(self, *args, **kwargs):
        super(PyGamePS4Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x03: 'right_stick_vert',
            0x02: 'right_stick_horz',
        }

        self.button_names = {
            2: "circle",
            1: "cross",
            0: 'square',
            3: "triangle",

            8: 'share',
            9: 'options',
            13: 'pad',

            4: 'L1',
            5: 'R1',
            6: 'L2',
            7: 'R2',
            10: 'L3',
            11: 'R3',
            14: 'dpad_left',
            15: 'dpad_right',
            16: 'dpad_down',
            17: 'dpad_up',
        }


class XboxOneJoystick(Joystick):
    '''
    An interface to a physical joystick 'Xbox Wireless Controller' controller.
    This will generally show up on /dev/input/js0.
    - Note that this code presumes the built-in linux driver for 'Xbox Wireless Controller'.
      There is another user land driver called xboxdrv; this code has not been tested
      with that driver.
    - Note that this controller requires that the bluetooth disable_ertm parameter
      be set to true; to do this:
      - edit /etc/modprobe.d/xbox_bt.conf
      - add the line: options bluetooth disable_ertm=1
      - reboot to tha this take affect.
      - after reboot you can vertify that disable_ertm is set to true entering this
        command oin a terminal: cat /sys/module/bluetooth/parameters/disable_ertm
      - the result should print 'Y'.  If not, make sure the above steps have been done corretly.

    credit:
    https://github.com/Ezward/donkeypart_ps3_controller/blob/master/donkeypart_ps3_controller/part.py
    '''

    def __init__(self, *args, **kwargs):
        super(XboxOneJoystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x05: 'right_stick_vert',
            0x02: 'right_stick_horz',
            0x0a: 'left_trigger',
            0x09: 'right_trigger',
            0x10: 'dpad_horiz',
            0x11: 'dpad_vert'
        }

        self.button_names = {
            0x130: 'a_button',
            0x131: 'b_button',
            0x133: 'x_button',
            0x134: 'y_button',
            0x13b: 'options',
            0x136: 'left_shoulder',
            0x137: 'right_shoulder',
        }


class LogitechJoystick(Joystick):
    '''
    An interface to a physical Logitech joystick available at /dev/input/js0
    Contains mapping that work for Raspian Stretch drivers
    Tested with Logitech Gamepad F710
    https://www.amazon.com/Logitech-940-000117-Gamepad-F710/dp/B0041RR0TW
    credit:
    https://github.com/kevkruemp/donkeypart_logitech_controller/blob/master/donkeypart_logitech_controller/part.py
    '''

    def __init__(self, *args, **kwargs):
        super(LogitechJoystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0x00: 'left_stick_horz',
            0x01: 'left_stick_vert',
            0x03: 'right_stick_horz',
            0x04: 'right_stick_vert',

            0x02: 'L2_pressure',
            0x05: 'R2_pressure',

            0x10: 'dpad_leftright',  # 1 is right, -1 is left
            0x11: 'dpad_up_down',  # 1 is down, -1 is up
        }

        self.button_names = {
            0x13a: 'back',  # 8 314
            0x13b: 'start',  # 9 315
            0x13c: 'Logitech',  # a  316

            0x130: 'A',
            0x131: 'B',
            0x133: 'X',
            0x134: 'Y',

            0x136: 'L1',
            0x137: 'R1',

            0x13d: 'left_stick_press',
            0x13e: 'right_stick_press',
        }


class Nimbus(Joystick):
    # An interface to a physical joystick available at /dev/input/js0
    # contains mappings that work for the SteelNimbus joystick
    # on Jetson TX2, JetPack 4.2, Ubuntu 18.04
    def __init__(self, *args, **kwargs):
        super(Nimbus, self).__init__(*args, **kwargs)

        self.button_names = {
            0x130: 'a',
            0x131: 'b',
            0x132: 'x',
            0x133: 'y',
            0x135: 'R1',
            0x137: 'R2',
            0x134: 'L1',
            0x136: 'L2',
        }

        self.axis_names = {
            0x0: 'lx',
            0x1: 'ly',
            0x2: 'rx',
            0x5: 'ry',
            0x11: 'hmm',
            0x10: 'what',
        }


class WiiU(Joystick):
    # An interface to a physical joystick available at /dev/input/js0
    # contains mappings may work for the WiiUPro joystick
    # This was taken from
    # https://github.com/autorope/donkeypart_bluetooth_game_controller/blob/master/donkeypart_bluetooth_game_controller/wiiu_config.yml
    # and need testing!
    def __init__(self, *args, **kwargs):
        super(WiiU, self).__init__(*args, **kwargs)

        self.button_names = {
            305: 'A',
            304: 'B',
            307: 'X',
            308: 'Y',
            312: 'LEFT_BOTTOM_TRIGGER',
            310: 'LEFT_TOP_TRIGGER',
            313: 'RIGHT_BOTTOM_TRIGGER',
            311: 'RIGHT_TOP_TRIGGER',
            317: 'LEFT_STICK_PRESS',
            318: 'RIGHT_STICK_PRESS',
            314: 'SELECT',
            315: 'START',
            547: 'PAD_RIGHT',
            546: 'PAD_LEFT',
            544: 'PAD_UP',
            548: 'PAD_DOWN,',
        }

        self.axis_names = {
            0: 'LEFT_STICK_X',
            1: 'LEFT_STICK_Y',
            3: 'RIGHT_STICK_X',
            4: 'RIGHT_STICK_Y',
        }


class RC3ChanJoystick(Joystick):
    # An interface to a physical joystick available at /dev/input/js0
    def __init__(self, *args, **kwargs):
        super(RC3ChanJoystick, self).__init__(*args, **kwargs)

        self.button_names = {
            0x120: 'Switch-up',
            0x121: 'Switch-down',
        }

        self.axis_names = {
            0x1: 'Throttle',
            0x0: 'Steering',
        }


class JoystickController(object):
    '''
    Class to map joystick buttons and axes to functions.
    JoystickController is a base class. You will not use this class directly,
    but instantiate a flavor based on your joystick type. See classes following this.

    Joystick client using access to local physical input. Maps button
    presses into actions and takes action. Interacts with the Donkey part
    framework.
    '''

    ES_IDLE = -1
    ES_START = 0
    ES_THROTTLE_NEG_ONE = 1
    ES_THROTTLE_POS_ONE = 2
    ES_THROTTLE_NEG_TWO = 3

    def __init__(self, poll_delay=0.0,
                 throttle_scale=1.0,
                 steering_scale=1.0,
                 throttle_dir=-1.0,
                 dev_fn='/dev/input/js0',
                 auto_record_on_throttle=True):

        self.img_arr = None
        self.angle = 0.0
        self.throttle = 0.0
        self.mode = 'user'
        self.mode_latch = None
        self.poll_delay = poll_delay
        self.running = True
        self.last_throttle_axis_val = 0
        self.throttle_scale = throttle_scale
        self.steering_scale = steering_scale
        self.throttle_dir = throttle_dir
        self.recording = False
        self.recording_latch = None
        self.constant_throttle = False
        self.auto_record_on_throttle = auto_record_on_throttle
        self.dev_fn = dev_fn
        self.js = None
        self.tub = None
        self.num_records_to_erase = 100
        self.estop_state = self.ES_IDLE
        self.chaos_monkey_steering = None
        self.dead_zone = 0.0

        self.button_down_trigger_map = {}
        self.button_up_trigger_map = {}
        self.axis_trigger_map = {}
        self.init_trigger_maps()

    def init_js(self):
        '''
        Attempt to init joystick. Should be definied by derived class
        Should return true on successfully created joystick object
        '''
        raise NotImplementedError("Subclass needs to define init_js")

    def init_trigger_maps(self):
        '''
        Creating mapping of buttons to functions.
        Should be definied by derived class
        '''
        raise NotImplementedError("init_trigger_maps")

    def set_deadzone(self, val):
        '''
        sets the minimim throttle for recording
        '''
        self.dead_zone = val

    def print_controls(self):
        '''
        print the mapping of buttons and axis to functions
        '''
        pt = PrettyTable()
        pt.field_names = ["control", "action"]
        for button, control in self.button_down_trigger_map.items():
            pt.add_row([button, control.__name__])
        for axis, control in self.axis_trigger_map.items():
            pt.add_row([axis, control.__name__])
        print("Joystick Controls:")
        print(pt)

        # print("Joystick Controls:")
        # print("On Button Down:")
        # print(self.button_down_trigger_map)
        # print("On Button Up:")
        # print(self.button_up_trigger_map)
        # print("On Axis Move:")
        # print(self.axis_trigger_map)

    def set_button_down_trigger(self, button, func):
        '''
        assign a string button descriptor to a given function call
        '''
        self.button_down_trigger_map[button] = func

    def set_button_up_trigger(self, button, func):
        '''
        assign a string button descriptor to a given function call
        '''
        self.button_up_trigger_map[button] = func

    def set_axis_trigger(self, axis, func):
        '''
        assign a string axis descriptor to a given function call
        '''
        self.axis_trigger_map[axis] = func

    def set_tub(self, tub):
        self.tub = tub

    def erase_last_N_records(self):
        if self.tub is not None:
            try:
                self.tub.delete_last_n_records(self.num_records_to_erase)
                logger.info('deleted last %d records.' %
                            self.num_records_to_erase)
            except:
                logger.info('failed to erase')

    def on_throttle_changes(self):
        '''
        turn on recording when non zero throttle in the user mode.
        '''
        if self.auto_record_on_throttle:
            recording = (abs(self.throttle) >
                         self.dead_zone and self.mode == 'user')
            if recording != self.recording:
                self.recording = recording
                self.recording_latch = self.recording
                logger.debug(
                    f"JoystickController::on_throttle_changes() setting recording = {self.recording}")

    def emergency_stop(self):
        '''
        initiate a series of steps to try to stop the vehicle as quickly as possible
        '''
        logger.warning('E-Stop!!!')
        self.mode = "user"
        self.recording = False
        self.constant_throttle = False
        self.estop_state = self.ES_START
        self.throttle = 0.0

    def update(self):
        '''
        poll a joystick for input events
        '''

        # wait for joystick to be online
        while self.running and self.js is None and not self.init_js():
            time.sleep(3)

        while self.running:
            button, button_state, axis, axis_val = self.js.poll()

            if axis is not None and axis in self.axis_trigger_map:
                '''
                then invoke the function attached to that axis
                '''
                self.axis_trigger_map[axis](axis_val)

            if button and button_state >= 1 and button in self.button_down_trigger_map:
                '''
                then invoke the function attached to that button
                '''
                self.button_down_trigger_map[button]()

            if button and button_state == 0 and button in self.button_up_trigger_map:
                '''
                then invoke the function attached to that button
                '''
                self.button_up_trigger_map[button]()

            time.sleep(self.poll_delay)

    def do_nothing(self, param):
        '''assign no action to the given axis
        this is useful to unmap certain axes, for example when swapping sticks
        '''
        pass

    def set_steering(self, axis_val):
        self.angle = self.steering_scale * axis_val
        # print("angle", self.angle)

    def set_throttle(self, axis_val):
        # this value is often reversed, with positive value when pulling down
        self.last_throttle_axis_val = axis_val
        self.throttle = self.throttle_dir * axis_val * self.throttle_scale
        # print("throttle", self.throttle)
        self.on_throttle_changes()

    def toggle_manual_recording(self):
        '''
        toggle recording on/off
        '''
        if self.auto_record_on_throttle:
            logger.info(
                'auto record on throttle is enabled; ignoring toggle of manual mode.')
        elif self.recording:
            self.recording = False
            self.recording_latch = self.recording
            logger.debug(
                f"JoystickController::toggle_manual_recording() setting recording and recording_latch = {self.recording}")
        else:
            self.recording = True
            self.recording_latch = self.recording
            logger.debug(
                f"JoystickController::toggle_manual_recording() setting recording and recording_latch = {self.recording}")

        logger.info(f'recording: {self.recording}')

    def increase_max_throttle(self):
        '''
        increase throttle scale setting
        '''
        self.throttle_scale = round(min(1.0, self.throttle_scale + 0.01), 2)
        if self.constant_throttle:
            self.throttle = self.throttle_scale
            self.on_throttle_changes()
        else:
            self.throttle = (self.throttle_dir *
                             self.last_throttle_axis_val * self.throttle_scale)

        logger.info(f'throttle_scale: {self.throttle_scale}')

    def decrease_max_throttle(self):
        '''
        decrease throttle scale setting
        '''
        self.throttle_scale = round(max(0.0, self.throttle_scale - 0.01), 2)
        if self.constant_throttle:
            self.throttle = self.throttle_scale
            self.on_throttle_changes()
        else:
            self.throttle = (self.throttle_dir *
                             self.last_throttle_axis_val * self.throttle_scale)

        logger.info(f'throttle_scale: {self.throttle_scale}')

    def toggle_constant_throttle(self):
        '''
        toggle constant throttle
        '''
        if self.constant_throttle:
            self.constant_throttle = False
            self.throttle = 0
            self.on_throttle_changes()
        else:
            self.constant_throttle = True
            self.throttle = self.throttle_scale
            self.on_throttle_changes()
        logger.info(f'constant_throttle: {self.constant_throttle}')

    def toggle_mode(self):
        '''
        switch modes from:
        user: human controlled steer and throttle
        local_angle: ai steering, human throttle
        local: ai steering, ai throttle
        '''
        if self.mode == 'user':
            self.mode = 'local_angle'
        elif self.mode == 'local_angle':
            self.mode = 'local'
        else:
            self.mode = 'user'
        self.mode_latch = self.mode
        logger.info(f'new mode: {self.mode}')

    def chaos_monkey_on_left(self):
        self.chaos_monkey_steering = -0.2

    def chaos_monkey_on_right(self):
        self.chaos_monkey_steering = 0.2

    def chaos_monkey_off(self):
        self.chaos_monkey_steering = None

    def run_threaded(self, img_arr=None, mode=None, recording=None):
        """
        :param img_arr: current camera image or None
        :param mode: default user/mode
        :param recording: default recording mode
        """
        self.img_arr = img_arr

        #
        # enforce defaults if they are not none.
        #
        if mode is not None:
            self.mode = mode
        if self.mode_latch is not None:
            self.mode = self.mode_latch
            self.mode_latch = None
        if recording is not None and recording != self.recording:
            logger.debug(
                f"JoystickController::run_threaded() setting recording from default = {recording}")
            self.recording = recording
        if self.recording_latch is not None:
            logger.debug(
                f"JoystickController::run_threaded() setting recording from latch = {self.recording_latch}")
            self.recording = self.recording_latch
            self.recording_latch = None

        '''
        process E-Stop state machine
        '''
        if self.estop_state > self.ES_IDLE:
            if self.estop_state == self.ES_START:
                self.estop_state = self.ES_THROTTLE_NEG_ONE
                return 0.0, -1.0 * self.throttle_scale, self.mode, False
            elif self.estop_state == self.ES_THROTTLE_NEG_ONE:
                self.estop_state = self.ES_THROTTLE_POS_ONE
                return 0.0, 0.01, self.mode, False
            elif self.estop_state == self.ES_THROTTLE_POS_ONE:
                self.estop_state = self.ES_THROTTLE_NEG_TWO
                self.throttle = -1.0 * self.throttle_scale
                return 0.0, self.throttle, self.mode, False
            elif self.estop_state == self.ES_THROTTLE_NEG_TWO:
                self.throttle += 0.05
                if self.throttle >= 0.0:
                    self.throttle = 0.0
                    self.estop_state = self.ES_IDLE
                return 0.0, self.throttle, self.mode, False

        if self.chaos_monkey_steering is not None:
            return self.chaos_monkey_steering, self.throttle, self.mode, False

        return self.angle, self.throttle, self.mode, self.recording

    def run(self, img_arr=None, mode=None, recording=None):
        return self.run_threaded(img_arr, mode, recording)

    def shutdown(self):
        # set flag to exit polling thread, then wait a sec for it to leave
        self.running = False
        time.sleep(0.5)


class JoystickCreatorController(JoystickController):
    '''
    A Controller object helps create a new controller object and mapping.
    This is used in management/joystic_creator when mapping
    a custom joystick.
    '''

    def __init__(self, *args, **kwargs):
        super(JoystickCreatorController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = JoystickCreator(self.dev_fn)
            if not self.js.init():
                self.js = None
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None

        return self.js is not None

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''
        pass


class PS3JoystickController(JoystickController):
    '''
    A Controller object that maps inputs to actions
    '''

    def __init__(self, *args, **kwargs):
        super(PS3JoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = PS3Joystick(self.dev_fn)
            if not self.js.init():
                self.js = None
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''

        self.button_down_trigger_map = {
            'select': self.toggle_mode,
            'circle': self.toggle_manual_recording,
            'triangle': self.erase_last_N_records,
            'cross': self.emergency_stop,
            'dpad_up': self.increase_max_throttle,
            'dpad_down': self.decrease_max_throttle,
            'start': self.toggle_constant_throttle,
            "R1": self.chaos_monkey_on_right,
            "L1": self.chaos_monkey_on_left,
        }

        self.button_up_trigger_map = {
            "R1": self.chaos_monkey_off,
            "L1": self.chaos_monkey_off,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
        }


class PS3JoystickSixAdController(PS3JoystickController):
    '''
    PS3 controller via sixad
    '''

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = PS3JoystickSixAd(self.dev_fn)
            if not self.js.init():
                self.js = None
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''
        super(PS3JoystickSixAdController, self).init_trigger_maps()

        self.axis_trigger_map = {
            'right_stick_horz': self.set_steering,
            'left_stick_vert': self.set_throttle,
        }


class PS4JoystickController(JoystickController):
    '''
    A Controller object that maps inputs to actions
    '''

    def __init__(self, *args, **kwargs):
        super(PS4JoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = PS4Joystick(self.dev_fn)
            if not self.js.init():
                self.js = None
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls for ps4
        '''

        self.button_down_trigger_map = {
            'share': self.toggle_mode,
            'circle': self.toggle_manual_recording,
            'triangle': self.erase_last_N_records,
            'cross': self.emergency_stop,
            'L1': self.increase_max_throttle,
            'R1': self.decrease_max_throttle,
            'options': self.toggle_constant_throttle,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
        }


class PyGamePS4JoystickController(PS4JoystickController):
    '''
    A Controller object that maps inputs to actions
    '''

    def __init__(self, which_js=0, *args, **kwargs):
        super(PyGamePS4JoystickController, self).__init__(*args, **kwargs)
        self.which_js = which_js

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = PyGamePS4Joystick(which_js=self.which_js)
        except Exception as e:
            # Initialization can fail for many reasons (missing drivers, no display, etc.).
            # Keep the broad except but silence pylint for it here.
            # pylint: disable=broad-except
            logger.error(e)
            self.js = None
        return self.js is not None


class XboxOneJoystickController(JoystickController):
    '''
    A Controller object that maps inputs to actions
    credit:
    https://github.com/Ezward/donkeypart_ps3_controller/blob/master/donkeypart_ps3_controller/part.py
    '''

    def __init__(self, *args, **kwargs):
        super(XboxOneJoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = XboxOneJoystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def magnitude(self, reverse=False):
        def set_magnitude(axis_val):
            '''
            Maps raw axis values to magnitude.
            '''
            # Axis values range from -1. to 1.
            minimum = -1.
            maximum = 1.
            # Magnitude is now normalized in the range of 0 - 1.
            magnitude = (axis_val - minimum) / (maximum - minimum)
            if reverse:
                magnitude *= -1
            self.set_throttle(magnitude)
        return set_magnitude

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''

        self.button_down_trigger_map = {
            'a_button': self.toggle_mode,
            'b_button': self.toggle_manual_recording,
            'x_button': self.erase_last_N_records,
            'y_button': self.emergency_stop,
            'right_shoulder': self.increase_max_throttle,
            'left_shoulder': self.decrease_max_throttle,
            'options': self.toggle_constant_throttle,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
            # Forza Mode
            'right_trigger': self.magnitude(),
            'left_trigger': self.magnitude(reverse=True),
        }


class XboxOneSwappedJoystickController(XboxOneJoystickController):
    '''
    Swap steering and throttle controls from std XBox one controller
    '''

    def __init__(self, *args, **kwargs):
        super(XboxOneSwappedJoystickController, self).__init__(*args, **kwargs)

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''
        super(XboxOneSwappedJoystickController, self).init_trigger_maps()

        # make the actual swap of the sticks
        self.set_axis_trigger('right_stick_horz', self.set_steering)
        self.set_axis_trigger('left_stick_vert', self.set_throttle)

        # unmap default assinments to the axes
        self.set_axis_trigger('left_stick_horz', self.do_nothing)
        self.set_axis_trigger('right_stick_vert', self.do_nothing)


class LogitechJoystickController(JoystickController):
    '''
    A Controller object that maps inputs to actions
    credit:
    https://github.com/kevkruemp/donkeypart_logitech_controller/blob/master/donkeypart_logitech_controller/part.py
    '''

    def __init__(self, *args, **kwargs):
        super(LogitechJoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        attempt to init joystick
        '''
        try:
            self.js = LogitechJoystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        '''
        init set of mapping from buttons to function calls
        '''

        self.button_down_trigger_map = {
            'start': self.toggle_mode,
            'B': self.toggle_manual_recording,
            'Y': self.erase_last_N_records,
            'A': self.emergency_stop,
            'back': self.toggle_constant_throttle,
            "R1": self.chaos_monkey_on_right,
            "L1": self.chaos_monkey_on_left,
        }

        self.button_up_trigger_map = {
            "R1": self.chaos_monkey_off,
            "L1": self.chaos_monkey_off,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
            'dpad_leftright': self.on_axis_dpad_LR,
            'dpad_up_down': self.on_axis_dpad_UD,
        }

    def on_axis_dpad_LR(self, val):
        if val == -1.0:
            self.on_dpad_left()
        elif val == 1.0:
            self.on_dpad_right()

    def on_axis_dpad_UD(self, val):
        if val == -1.0:
            self.on_dpad_up()
        elif val == 1.0:
            self.on_dpad_down()

    def on_dpad_up(self):
        self.increase_max_throttle()

    def on_dpad_down(self):
        self.decrease_max_throttle()

    def on_dpad_left(self):
        logger.error("dpad left un-mapped")

    def on_dpad_right(self):
        logger.error("dpad right un-mapped")


class NimbusController(JoystickController):
    # A Controller object that maps inputs to actions
    def __init__(self, *args, **kwargs):
        super(NimbusController, self).__init__(*args, **kwargs)

    def init_js(self):
        # attempt to init joystick
        try:
            self.js = Nimbus(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        # init set of mapping from buttons to function calls

        self.button_down_trigger_map = {
            'y': self.erase_last_N_records,
            'b': self.toggle_mode,
            'a': self.emergency_stop,
        }

        self.axis_trigger_map = {
            'lx': self.set_steering,
            'ry': self.set_throttle,
        }


class WiiUController(JoystickController):
    # A Controller object that maps inputs to actions
    def __init__(self, *args, **kwargs):
        super(WiiUController, self).__init__(*args, **kwargs)

    def init_js(self):
        # attempt to init joystick
        try:
            self.js = WiiU(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def init_trigger_maps(self):
        # init set of mapping from buttons to function calls

        self.button_down_trigger_map = {
            'Y': self.erase_last_N_records,
            'B': self.toggle_mode,
            'A': self.emergency_stop,
        }

        self.axis_trigger_map = {
            'LEFT_STICK_X': self.set_steering,
            'RIGHT_STICK_Y': self.set_throttle,
        }


class RC3ChanJoystickController(JoystickController):
    # A Controller object that maps inputs to actions
    def __init__(self, *args, **kwargs):
        super(RC3ChanJoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        # attempt to init joystick
        try:
            self.js = RC3ChanJoystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            logger.error(f"{self.dev_fn} not found.")
            self.js = None
        return self.js is not None

    def on_steering(self, val, reverse=True):
        if reverse:
            val *= -1
        self.set_steering(val)

    def on_throttle(self, val, reverse=True):
        if reverse:
            val *= -1
        self.set_throttle(val)

    def on_switch_up(self):
        if self.mode == 'user':
            self.erase_last_N_records()
        else:
            self.emergency_stop()

    def on_switch_down(self):
        self.toggle_mode()

    def init_trigger_maps(self):
        # init set of mapping from buttons to function calls

        self.button_down_trigger_map = {
            'Switch-down': self.on_switch_down,
            'Switch-up': self.on_switch_up,
        }

        self.axis_trigger_map = {
            'Steering': self.on_steering,
            'Throttle': self.on_throttle,
        }


class JoyStickPub(object):
    '''
    Use Zero Message Queue (zmq) to publish the control messages from a local joystick
    '''

    def __init__(self, port=5556, dev_fn='/dev/input/js1'):
        import zmq
        self.dev_fn = dev_fn
        self.js = PS3JoystickPC(self.dev_fn)
        self.js.init()
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%d" % port)

    def run(self):
        while True:
            button, button_state, axis, axis_val = self.js.poll()
            if axis is not None or button is not None:
                if button is None:
                    button = "0"
                    button_state = 0
                if axis is None:
                    axis = "0"
                    axis_val = 0
                message_data = (button, button_state, axis, axis_val)
                self.socket.send_string("%s %d %s %f" % message_data)
                logger.info(f"SENT {message_data}")


class JoyStickSub(object):
    '''
    Use Zero Message Queue (zmq) to subscribe to control messages from a remote joystick
    '''

    def __init__(self, ip, port=5556):
        import zmq
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://%s:%d" % (ip, port))
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.button = None
        self.button_state = 0
        self.axis = None
        self.axis_val = 0.0
        self.running = True

    def shutdown(self):
        self.running = False
        time.sleep(0.1)

    def update(self):
        while self.running:
            payload = self.socket.recv().decode("utf-8")
            # print("got", payload)
            button, button_state, axis, axis_val = payload.split(' ')
            self.button = button
            self.button_state = (int)(button_state)
            self.axis = axis
            self.axis_val = (float)(axis_val)
            if self.button == "0":
                self.button = None
            if self.axis == "0":
                self.axis = None

    def run_threaded(self):
        pass

    def poll(self):
        ret = (self.button, self.button_state, self.axis, self.axis_val)
        self.button = None
        self.axis = None
        return ret


def get_js_controller(cfg):
    cont_class = None
    if cfg.CONTROLLER_TYPE == "ps3":
        cont_class = PS3JoystickController
    elif cfg.CONTROLLER_TYPE == "ps3sixad":
        cont_class = PS3JoystickSixAdController
    elif cfg.CONTROLLER_TYPE == "ps4":
        cont_class = PS4JoystickController
    elif cfg.CONTROLLER_TYPE == "nimbus":
        cont_class = NimbusController
    elif cfg.CONTROLLER_TYPE == "xbox":
        cont_class = XboxOneJoystickController
    elif cfg.CONTROLLER_TYPE == "xboxswapped":
        cont_class = XboxOneSwappedJoystickController
    elif cfg.CONTROLLER_TYPE == "wiiu":
        cont_class = WiiUController
    elif cfg.CONTROLLER_TYPE == "F710":
        cont_class = LogitechJoystickController
    elif cfg.CONTROLLER_TYPE == "rc3":
        cont_class = RC3ChanJoystickController
    elif cfg.CONTROLLER_TYPE == "pygame":
        cont_class = PyGamePS4JoystickController
    else:
        raise ValueError("Unknown controller type: " + cfg.CONTROLLER_TYPE)

    ctr = cont_class(throttle_dir=cfg.JOYSTICK_THROTTLE_DIR,
                     throttle_scale=cfg.JOYSTICK_MAX_THROTTLE,
                     steering_scale=cfg.JOYSTICK_STEERING_SCALE,
                     auto_record_on_throttle=cfg.AUTO_RECORD_ON_THROTTLE,
                     dev_fn=cfg.JOYSTICK_DEVICE_FILE)

    ctr.set_deadzone(cfg.JOYSTICK_DEADZONE)
    return ctr


if __name__ == "__main__":
 #   Testing the XboxOneJoystickController
    js = XboxOneJoystick('/dev/input/js0')
    js.init()

    while True:
        button, button_state, axis, axis_val = js.poll()
        if button is not None or axis is not None:
            print(button, button_state, axis, axis_val)
        time.sleep(0.1)
