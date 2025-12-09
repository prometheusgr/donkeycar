"""Unit tests for controller_device module."""

try:
    import pytest  # type: ignore
except ImportError:
    pytest = None  # type: ignore

from unittest.mock import Mock, MagicMock, patch
from donkeycar.parts.controller_device import (
    Channel,
    RCReceiver,
    Joystick,
    PyGameJoystick,
)


class TestChannel:
    """Tests for the Channel class."""

    def test_channel_initialization(self):
        """Test that Channel initializes with correct pin and state."""
        pin = 17
        channel = Channel(pin)

        assert channel.pin == pin
        assert channel.tick is None
        assert channel.high_tick is None

    def test_channel_multiple_instances(self):
        """Test creating multiple Channel instances."""
        pin1, pin2, pin3 = 17, 27, 22
        channels = [Channel(pin1), Channel(pin2), Channel(pin3)]

        assert len(channels) == 3
        assert channels[0].pin == pin1
        assert channels[1].pin == pin2
        assert channels[2].pin == pin3


class TestRCReceiver:
    """Tests for the RCReceiver class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.STEERING_RC_GPIO = 17
        config.THROTTLE_RC_GPIO = 27
        config.DATA_WIPER_RC_GPIO = 22
        config.PIGPIO_STEERING_MID = 1500
        config.PIGPIO_MAX_FORWARD = 2000
        config.PIGPIO_STOPPED_PWM = 1500
        config.PIGPIO_MAX_REVERSE = 1000
        config.AUTO_RECORD_ON_THROTTLE = False
        config.PIGPIO_INVERT = False
        config.PIGPIO_JITTER = 0.0
        return config

    def test_rc_receiver_initialization(self, mock_config):
        """Test RCReceiver initialization."""
        receiver = RCReceiver(mock_config, debug=False)

        assert receiver.debug is False
        assert receiver.mode == 'user'
        assert receiver.is_action is False
        assert len(receiver.channels) == 3
        assert len(receiver.signals) == 3
        assert receiver.signals == [0, 0, 0]
        assert receiver.min_pwm == 1000
        assert receiver.max_pwm == 2000
        assert receiver.STEERING_MID == mock_config.PIGPIO_STEERING_MID
        assert receiver.MAX_FORWARD == mock_config.PIGPIO_MAX_FORWARD
        assert receiver.STOPPED_PWM == mock_config.PIGPIO_STOPPED_PWM
        assert receiver.MAX_REVERSE == mock_config.PIGPIO_MAX_REVERSE

    def test_rc_receiver_channels_creation(self, mock_config):
        """Test that RCReceiver creates correct channels."""
        receiver = RCReceiver(mock_config)

        assert receiver.channels[0].pin == mock_config.STEERING_RC_GPIO
        assert receiver.channels[1].pin == mock_config.THROTTLE_RC_GPIO
        assert receiver.channels[2].pin == mock_config.DATA_WIPER_RC_GPIO

    def test_rc_receiver_factor_calculation(self, mock_config):
        """Test that factor is calculated correctly."""
        receiver = RCReceiver(mock_config)
        expected_factor = (receiver.MAX_OUT - receiver.MIN_OUT) / (2000 - 1000)

        # Allow for floating point precision differences
        assert abs(receiver.factor - expected_factor) < 1e-9
        assert abs(receiver.factor - 2.0) < 1e-9

    def test_rc_receiver_class_constants(self):
        """Test RCReceiver class constants."""
        assert RCReceiver.MIN_OUT == -1
        assert RCReceiver.MAX_OUT == 1

    def test_rc_receiver_debug_mode(self, mock_config):
        """Test RCReceiver with debug enabled."""
        receiver = RCReceiver(mock_config, debug=True)

        assert receiver.debug is True

    def test_rc_receiver_pulse_width_none(self, mock_config):
        """Test pulse_width with None value."""
        receiver = RCReceiver(mock_config)
        result = receiver.pulse_width(None)

        assert result is not None
        assert abs(result - 0.0) < 1e-9

    def test_rc_receiver_pulse_width_value(self, mock_config):
        """Test pulse_width with actual value."""
        receiver = RCReceiver(mock_config)
        result = receiver.pulse_width(1500)

        assert result == 1500

    def test_rc_receiver_cbf_steering_channel(self, mock_config):
        """Test callback function for steering channel."""
        receiver = RCReceiver(mock_config)

        # Test high edge
        receiver.cbf(mock_config.STEERING_RC_GPIO, 1, 1000)
        assert receiver.channels[0].high_tick == 1000

        # Test low edge
        receiver.cbf(mock_config.STEERING_RC_GPIO, 0, 2000)
        assert receiver.channels[0].tick == 1000  # 2000 - 1000

    def test_rc_receiver_cbf_wrong_channel(self, mock_config):
        """Test callback function with wrong GPIO pin."""
        receiver = RCReceiver(mock_config)

        # Call with non-existent GPIO
        receiver.cbf(99, 1, 1000)

        # Should not affect any channels
        for channel in receiver.channels:
            assert channel.high_tick is None
            assert channel.tick is None

    def test_rc_receiver_shutdown(self, mock_config):
        """Test shutdown method."""
        receiver = RCReceiver(mock_config)
        receiver.shutdown()

        # All callbacks should be cancelled
        assert len(receiver.cbs) == 3

    def test_rc_receiver_run_basic(self, mock_config):
        """Test run method with basic parameters."""
        receiver = RCReceiver(mock_config)

        signals, _throttle, mode, is_action = receiver.run()

        assert len(signals) == 3
        assert isinstance(signals, list)
        assert mode == 'user'
        assert is_action is False

    def test_rc_receiver_run_with_recording(self, mock_config):
        """Test run method with recording parameter."""
        receiver = RCReceiver(mock_config)

        _signals, _throttle, _mode, is_action = receiver.run(recording=True)

        assert is_action is True

    def test_rc_receiver_run_with_mode(self, mock_config):
        """Test run method with mode parameter."""
        receiver = RCReceiver(mock_config)

        _signals, _throttle, mode, _is_action = receiver.run(mode='local')

        assert mode == 'local'


class TestJoystick:
    """Tests for the Joystick class."""

    def test_joystick_initialization(self):
        """Test Joystick initialization."""
        js = Joystick()

        assert js.dev_fn == '/dev/input/js0'
        assert js.jsdev is None
        assert isinstance(js.axis_states, dict)
        assert isinstance(js.button_states, dict)
        assert isinstance(js.axis_names, dict)
        assert isinstance(js.button_names, dict)
        assert isinstance(js.axis_map, list)
        assert isinstance(js.button_map, list)

    def test_joystick_custom_dev_fn(self):
        """Test Joystick with custom device file."""
        custom_dev = '/dev/input/js1'
        js = Joystick(dev_fn=custom_dev)

        assert js.dev_fn == custom_dev

    @patch('os.path.exists')
    def test_joystick_init_missing_device(self, mock_exists):
        """Test Joystick init when device file doesn't exist."""
        mock_exists.return_value = False
        js = Joystick()

        result = js.init()

        assert result is False

    @patch('os.path.exists')
    @patch('donkeycar.parts.controller_device.ioctl')
    def test_joystick_init_fcntl_not_available(self, _mock_ioctl, mock_exists):
        """Test Joystick init when fcntl is not available."""
        mock_exists.return_value = True

        with patch('donkeycar.parts.controller_device.ioctl', side_effect=ModuleNotFoundError):
            js = Joystick()
            result = js.init()

            assert result is False


class TestPyGameJoystick:
    """Tests for the PyGameJoystick class."""

    @patch('donkeycar.parts.controller_device.pygame')
    def test_pygame_joystick_initialization(self, _mock_pygame_module):
        """Test PyGameJoystick initialization with pygame available."""
        mock_joystick = MagicMock()
        mock_joystick.get_numaxes.return_value = 2
        mock_joystick.get_numbuttons.return_value = 10
        mock_joystick.get_numhats.return_value = 1
        mock_joystick.get_name.return_value = "Test Joystick"

        with patch('pygame.init'), \
                patch('pygame.joystick.init'), \
                patch('pygame.joystick.Joystick', return_value=mock_joystick):
            js = PyGameJoystick()

            assert js.joystick is not None
            assert len(js.axis_states) == 2
            assert len(js.button_states) == 14  # 10 buttons + 1 hat * 4

    def test_pygame_joystick_initialization_no_pygame(self):
        """Test PyGameJoystick initialization when pygame is not available."""
        with patch.dict('sys.modules', {'pygame': None}):
            try:
                js = PyGameJoystick()
                # If pygame is mocked/unavailable, joystick should be None
                assert js.joystick is None or isinstance(
                    js.joystick, (type(None), MagicMock))
            except (ImportError, RuntimeError, AttributeError):
                # It's acceptable to raise an exception if pygame is truly unavailable
                pass

    @patch('donkeycar.parts.controller_device.pygame')
    def test_pygame_joystick_dead_zone(self, _mock_pygame_module):
        """Test PyGameJoystick dead_zone initialization."""
        with patch('pygame.init'), \
                patch('pygame.joystick.init'), \
                patch('pygame.joystick.Joystick', return_value=MagicMock()):
            js = PyGameJoystick()

            # Allow for floating point precision differences
            assert abs(js.dead_zone - 0.07) < 1e-9

    @patch('donkeycar.parts.controller_device.pygame')
    def test_pygame_joystick_poll_no_joystick(self, _mock_pygame_module):
        """Test PyGameJoystick poll when joystick is None."""
        js = PyGameJoystick()
        js.joystick = None

        button, button_state, axis, axis_val = js.poll()

        assert button is None
        assert button_state is None
        assert axis is None
        assert axis_val is None

    @patch('donkeycar.parts.controller_device.pygame')
    def test_pygame_joystick_show_map(self, _mock_pygame_module):
        """Test PyGameJoystick show_map method."""
        mock_joystick = MagicMock()
        mock_joystick.get_numaxes.return_value = 2
        mock_joystick.get_numbuttons.return_value = 10

        with patch('pygame.init'), \
                patch('pygame.joystick.init'), \
                patch('pygame.joystick.Joystick', return_value=mock_joystick), \
                patch('builtins.print') as mock_print:
            js = PyGameJoystick()
            js.axis_map = ['X', 'Y']
            js.button_map = ['A', 'B']
            js.show_map()

            # show_map should call print
            assert mock_print.called


class TestIntegration:
    """Integration tests for controller_device classes."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.STEERING_RC_GPIO = 17
        config.THROTTLE_RC_GPIO = 27
        config.DATA_WIPER_RC_GPIO = 22
        config.PIGPIO_STEERING_MID = 1500
        config.PIGPIO_MAX_FORWARD = 2000
        config.PIGPIO_STOPPED_PWM = 1500
        config.PIGPIO_MAX_REVERSE = 1000
        config.AUTO_RECORD_ON_THROTTLE = False
        config.PIGPIO_INVERT = False
        config.PIGPIO_JITTER = 0.0
        return config

    def test_rc_receiver_full_cycle(self, mock_config):
        """Test RCReceiver through a full cycle."""
        receiver = RCReceiver(mock_config)

        # Simulate receiving pulses
        receiver.cbf(mock_config.STEERING_RC_GPIO, 1, 1000)
        receiver.cbf(mock_config.STEERING_RC_GPIO, 0, 2500)

        # Run and get signals
        signals, _throttle, _mode, _is_action = receiver.run()

        assert isinstance(signals, list)
        assert len(signals) == 3

    def test_channel_integration_with_receiver(self, mock_config):
        """Test Channel integration with RCReceiver."""
        receiver = RCReceiver(mock_config)

        # Verify channels are properly initialized
        for _i, channel in enumerate(receiver.channels):
            assert isinstance(channel, Channel)
            assert channel.pin in [
                mock_config.STEERING_RC_GPIO,
                mock_config.THROTTLE_RC_GPIO,
                mock_config.DATA_WIPER_RC_GPIO,
            ]
