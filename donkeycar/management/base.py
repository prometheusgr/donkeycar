import argparse
import os
import shutil
import socket
import stat
import sys
import logging

try:
    from progress.bar import IncrementalBar
except ImportError:
    # Lightweight fallback when `progress` package is not installed (tests/CI).
    class IncrementalBar:  # pragma: no cover - fallback for tests
        def __init__(self, *args, **kwargs):
            # This method is intentionally left empty as it serves as a placeholder
            # for the `IncrementalBar` class when the `progress` package is not installed.
            pass

        def next(self):
            '''intentionally left blank'''
            return None

        def finish(self):
            '''intentionally left blank'''
            return None

        def start(self):
            '''intentionally left blank'''
            return None

        def update(self, *args, **kwargs):
            '''intentionally left blank'''
            return None

        def goto(self, *args, **kwargs):
            '''intentionally left blank'''
            return None

        def __enter__(self):
            '''intentionally left blank'''
            return self

        def __exit__(self, exc_type, exc, tb):
            '''intentionally left blank'''
            return None
import donkeycar as dk
from donkeycar.management.joystick_creator import CreateJoystick

from donkeycar.utils import normalize_image, load_image, math

PACKAGE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_PATH = os.path.join(PACKAGE_PATH, 'templates')
MYCONFIG = 'myconfig.py'
CONFIG_DEFAULT = './config.py'
HELP_CONFIG = f'location of config file to use. default: ./{MYCONFIG}'
USAGE = '%(prog)s [options]'
logger = logging.getLogger(__name__)


def make_dir(path):
    ''' make directory if it does not exist'''
    real_path = os.path.expanduser(path)
    print('making dir ', real_path)
    if not os.path.exists(real_path):
        os.makedirs(real_path)
    return real_path


def load_config(config_path, myconfig=MYCONFIG):
    """
    load a config from the given path
    """
    conf = os.path.expanduser(config_path)
    if not os.path.exists(conf):
        logger.error("No config file at location: %s. Add --config to "
                     "specify location or run from dir containing config.py.", conf)
        return None

    try:
        cfg = dk.load_config(conf, myconfig)
    except (ImportError, SyntaxError) as e:
        logger.error("Exception %s while loading config from %s", e, conf)
        return None

    return cfg


class BaseCommand:
    ''' Base class for management commands.'''

    def parse_args(self, args):
        """Parse command line arguments."""
        raise NotImplementedError("Subclasses must implement this method.")

    def run(self, args):
        """Run the command with the given arguments."""
        raise NotImplementedError("Subclasses must implement this method.")


class CreateCar(BaseCommand):
    ''' Create a donkey car folder structure.'''

    def parse_args(self, args):
        ''' Parse the command line arguments.'''
        parser = argparse.ArgumentParser(
            prog='createcar', usage=USAGE)
        parser.add_argument('--path', default=None,
                            help='path where to create car folder')
        parser.add_argument('--template', default=None,
                            help='name of car template to use')
        parser.add_argument('--overwrite', action='store_true',
                            help='should replace existing files')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        ''' Run the command with the given args.'''
        args = self.parse_args(args)
        self.create_car(path=args.path, template=args.template,
                        overwrite=args.overwrite)

    def create_car(self, path, template='complete', overwrite=False):
        """
        Sets up the folder structure for donkey to work. Refactored to
        delegate smaller tasks to helper methods to reduce complexity.
        """
        # defaults
        path = path or '~/mycar'
        template = template or 'complete'
        print(f"Creating car folder: {path}")
        path = make_dir(path)

        self._ensure_standard_folders(path)

        # template / file names
        app_template_path = os.path.join(TEMPLATES_PATH, template + '.py')
        config_template_path = os.path.join(
            TEMPLATES_PATH, 'cfg_' + template + '.py')
        myconfig_template_path = os.path.join(TEMPLATES_PATH, MYCONFIG)
        train_template_path = os.path.join(TEMPLATES_PATH, 'train.py')
        calibrate_template_path = os.path.join(TEMPLATES_PATH, 'calibrate.py')

        car_app_path = os.path.join(path, 'manage.py')
        car_config_path = os.path.join(path, 'config.py')
        mycar_config_path = os.path.join(path, MYCONFIG)
        train_app_path = os.path.join(path, 'train.py')
        calibrate_app_path = os.path.join(path, 'calibrate.py')

        # copy files (each helper handles existence/overwrite)
        self._copy_template(app_template_path, car_app_path, overwrite, make_executable=True,
                            exist_message='Car app already exists. Delete it and rerun createcar to replace.',
                            copy_message=f"Copying car application template: {template}")

        self._copy_template(config_template_path, car_config_path, overwrite,
                            exist_message='Car config already exists. Delete it and rerun createcar to replace.',
                            copy_message="Copying car config defaults. Adjust these before starting your car.")

        self._copy_template(train_template_path, train_app_path, overwrite, make_executable=True,
                            exist_message='Train already exists. Delete it and rerun createcar to replace.',
                            copy_message="Copying train script. Adjust these before starting your car.")

        self._copy_template(calibrate_template_path, calibrate_app_path, overwrite, make_executable=True,
                            exist_message='Calibrate already exists. Delete it and rerun createcar to replace.',
                            copy_message="Copying calibrate script. Adjust these before starting your car.")

        if not os.path.exists(mycar_config_path):
            self._create_myconfig_from_config(
                car_config_path, myconfig_template_path, mycar_config_path)

        print("Donkey setup complete.")

    def _ensure_standard_folders(self, path):
        """Create the standard models/data/logs folders inside path."""
        print("Creating data & model folders.")
        folders = ['models', 'data', 'logs']
        for f in folders:
            make_dir(os.path.join(path, f))

    def _copy_template(self, src, dst, overwrite, make_executable=False,
                       exist_message=None, copy_message=None):
        """
        Copy a template file from src to dst, respecting overwrite flag.
        Optionally make the destination executable for the current user.
        """
        if os.path.exists(dst) and not overwrite:
            if exist_message:
                print(exist_message)
            return

        if copy_message:
            print(copy_message)
        try:
            shutil.copyfile(src, dst)
            if make_executable:
                os.chmod(dst, stat.S_IRWXU)
        except Exception as e:
            # Keep behavior simple: report failure but don't crash
            print(f"Failed to copy {src} to {dst}: {e}")

    def _create_myconfig_from_config(self, car_config_path, myconfig_template_path, mycar_config_path):
        """
        Copy the myconfig template and then append commented lines from
        the generated config.py so users can easily enable overrides.
        """
        print("Copying my car config overrides")
        try:
            shutil.copyfile(myconfig_template_path, mycar_config_path)
        except Exception as e:
            print(f"Failed to copy myconfig template: {e}")
            return

        # Append commented config contents from config.py starting at 'import os'
        try:
            with open(car_config_path, "r", encoding="utf-8") as cfg, \
                    open(mycar_config_path, "a", encoding="utf-8") as mcfg:
                copy = False
                for line in cfg:
                    if "import os" in line:
                        copy = True
                    if copy:
                        mcfg.write("# " + line)
        except Exception as e:
            print(f"Failed to append config contents to myconfig: {e}")


class UpdateCar(BaseCommand):
    '''
    always run in the base ~/mycar dir to get latest
    '''

    def parse_args(self, args):
        ''' Parse the command line arguments.'''
        parser = argparse.ArgumentParser(
            prog='update', usage=USAGE)
        parser.add_argument('--template', default=None,
                            help='name of car template to use')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        ''' Run the command with the given args.'''
        args = self.parse_args(args)
        cc = CreateCar()
        cc.create_car(path=".", overwrite=True, template=args.template)


class FindCar(BaseCommand):
    def parse_args(self, args):
        ''' Parse the command line arguments.'''
        pass

    def run(self, args):
        ''' Run the command with the given args.'''
        print('Looking up your computer IP address...')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        print('Your IP address: %s ' % s.getsockname()[0])
        s.close()

        print("Finding your car's IP address...")
        cmd = "sudo nmap -sP " + ip + \
            "/24 | awk '/^Nmap/{ip=$NF}/B8:27:EB/{print ip}'"
        cmd_rpi4 = "sudo nmap -sP " + ip + \
            "/24 | awk '/^Nmap/{ip=$NF}/DC:A6:32/{print ip}'"
        print("Your car's ip address is:")
        os.system(cmd)
        os.system(cmd_rpi4)


class CalibrateCar(BaseCommand):
    ''' Calibrate the PWM settings for your car.'''

    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog='calibrate', usage=USAGE)
        parser.add_argument(
            '--pwm-pin',
            help="The PwmPin specifier of pin to calibrate, like 'RPI_GPIO.BOARD.33' or 'PCA9685.1:40.13'")
        parser.add_argument('--channel', default=None,
                            help="The PCA9685 channel you'd like to calibrate [0-15]")
        parser.add_argument(
            '--address',
            default='0x40',
            help="The i2c address of PCA9685 you'd like to calibrate [default 0x40]")
        parser.add_argument(
            '--bus',
            default=None,
            help="The i2c bus of PCA9685 you'd like to calibrate [default autodetect]")
        parser.add_argument('--pwmFreq', default=60,
                            help="The frequency to use for the PWM")
        parser.add_argument(
            '--arduino',
            dest='arduino',
            action='store_true',
            help='Use arduino pin for PWM (calibrate pin=<channel>)')
        parser.set_defaults(arduino=False)
        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        args = self.parse_args(args)

        apply_pwm, input_prompt = self._setup_controller(args)

        while True:
            try:
                val = input(input_prompt)
                if val.lower() == 'q':
                    break
                pmw = int(val)
                apply_pwm(pmw)
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt received, exit.")
                break
            except (ValueError, TypeError) as ex:
                print(f"Oops, {ex}")

    def _setup_controller(self, args):
        """
        Initialize the appropriate controller and return an apply_pwm callable
        and the input prompt string.
        """
        if args.arduino:
            from donkeycar.parts.actuator import ArduinoFirmata

            channel = int(args.channel)
            arduino_controller = ArduinoFirmata(servo_pin=channel)
            print(f'init Arduino PWM on pin {channel}')
            input_prompt = "Enter a PWM setting to test ('q' for quit) (0-180): "

            def apply__arduino_pwm(pmw):
                arduino_controller.set_pulse(channel, pmw)

            return apply__arduino_pwm, input_prompt

        if args.pwm_pin is not None:
            from donkeycar.parts.actuator import PulseController
            from donkeycar.parts import pins

            try:
                pwm_pin = pins.pwm_pin_by_id(args.pwm_pin)
            except ValueError as e:
                print(e)
                print("See pins.py for a description of pin specification strings.")
                exit(-1)
            print(f'init pin {args.pwm_pin}')
            freq = int(args.pwmFreq)
            print(f"Using PWM freq: {freq}")
            c = PulseController(pwm_pin)
            input_prompt = "Enter a PWM setting to test ('q' for quit) (0-1500): "
            print()

            def apply_pin_pwm(pmw):
                c.run(pmw)

            return apply_pin_pwm, input_prompt

        # default to PCA9685 path
        from donkeycar.parts.actuator import PCA9685
        from donkeycar.parts.sombrero import Sombrero

        Sombrero()  # setup pins for Sombrero hat

        channel = int(args.channel)
        busnum = int(args.bus) if args.bus else None
        address = int(args.address, 16)
        print(
            f'init PCA9685 on channel {channel} address {hex(address)} bus {busnum}')
        freq = int(args.pwmFreq)
        print(f"Using PWM freq: {freq}")
        c = PCA9685(channel, address=address, busnum=busnum, frequency=freq)
        input_prompt = "Enter a PWM setting to test ('q' for quit) (0-1500): "
        print()

        def apply_pwm(pmw):
            c.run(pmw)

        return apply_pwm, input_prompt


class MakeMovieShell(BaseCommand):
    '''
    take the make movie args and then call make movie command
    with lazy imports
    '''

    def __init__(self):
        self.deg_to_rad = math.pi / 180.0

    def parse_args(self, args):
        parser = argparse.ArgumentParser(prog='makemovie', usage=USAGE)
        parser.add_argument('--tub', help='The tub to make movie from')
        parser.add_argument(
            '--out',
            default='tub_movie.mp4',
            help='The movie filename to create. default: tub_movie.mp4')
        parser.add_argument(
            '--config', default=CONFIG_DEFAULT, help=HELP_CONFIG)
        parser.add_argument('--model', default=None,
                            help='the model to use to show control outputs')
        parser.add_argument('--type', default=None,
                            required=False, help='the model type to load')
        parser.add_argument('--salient', action="store_true",
                            help='should we overlay salient map showing activations')
        parser.add_argument('--start', type=int, default=0,
                            help='first frame to process')
        parser.add_argument('--end', type=int, default=-1,
                            help='last frame to process')
        parser.add_argument('--scale', type=int, default=2,
                            help='make image frame output larger by X mult')
        parser.add_argument(
            '--draw-user-input',
            default=True, action='store_false',
            help='show user input on the video')
        parsed_args = parser.parse_args(args)
        return parsed_args, parser

    def run(self, args):
        '''
        Load the images from a tub and create a movie from them.
        Movie
        '''
        args, parser = self.parse_args(args)

        from donkeycar.management.makemovie import MakeMovie

        mm = MakeMovie()
        mm.run(args, parser)


class ShowHistogram(BaseCommand):

    def parse_args(self, args):
        ''' Parse the command line arguments.'''
        parser = argparse.ArgumentParser(prog='tubhist', usage=USAGE)
        parser.add_argument('--tub', nargs='+', help='paths to tubs')
        parser.add_argument('--record', default=None,
                            help='name of record to create histogram')
        parser.add_argument('--out', default=None,
                            help='path where to save histogram end with .png')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def show_histogram(self, tub_paths, record_name, out):
        """
        Produce a histogram of record type frequency in the given tub
        """
        # Ensure matplotlib is available before attempting any plotting.
        try:
            import pandas as pd
            from matplotlib import pyplot as plt
        except ImportError:
            logger.error(
                "matplotlib is not available; install matplotlib to use the 'tubhist' command.")
            return
        from donkeycar.parts.tub_v2 import Tub

        output = out or os.path.basename(tub_paths)
        path_list = tub_paths.split(",")
        records = [record for path in path_list for record
                   in Tub(path, read_only=True)]
        df = pd.DataFrame(records)
        df.drop(columns=["_index", "_timestamp_ms"], inplace=True)
        # this prints it to screen
        if record_name is not None:
            df[record_name].hist(bins=50)
        else:
            df.hist(bins=50)

        try:
            if out is not None:
                filename = output
            else:
                if record_name is not None:
                    filename = f"{output}_hist_{record_name.replace('/', '_')}.png"
                else:
                    filename = f"{output}_hist.png"
            plt.savefig(filename)
            logger.info('saving image to: %s', filename)
        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Failed to save histogram image: %s", e)
        plt.show()

    def run(self, args):
        args = self.parse_args(args)
        if isinstance(args.tub, list):
            args.tub = ','.join(args.tub)
        self.show_histogram(args.tub, args.record, args.out)


class ShowCnnActivations(BaseCommand):

    def __init__(self):
        import matplotlib
        try:
            matplotlib.use('Agg')
        except Exception:
            # If backend can't be set, continue and let matplotlib pick one
            pass
        import matplotlib.pyplot as plt
        self.plt = plt

    def get_activations(self, image_path, model_path, cfg):
        '''
        Extracts features from an image

        returns activations/features
        '''
        from tensorflow.python.keras.models import load_model, Model

        model_path = os.path.expanduser(model_path)
        image_path = os.path.expanduser(image_path)

        model = load_model(model_path, compile=False)
        image = load_image(image_path, cfg)[None, ...]

        conv_layer_names = self.get_conv_layers(model)
        input_layer = model.get_layer(name='img_in').input
        activations = []
        for conv_layer_name in conv_layer_names:
            output_layer = model.get_layer(name=conv_layer_name).output

            layer_model = Model(inputs=[input_layer], outputs=[output_layer])
            activations.append(layer_model.predict(image)[0])
        return activations

    def create_figure(self, activations):
        import math
        cols = 6

        for i, layer in enumerate(activations):
            fig = self.plt.figure()
            fig.suptitle(f'Layer {i+1}')

            print(f'layer {i+1} shape: {layer.shape}')
            feature_maps = layer.shape[2]
            rows = math.ceil(feature_maps / cols)

            for j in range(feature_maps):
                self.plt.subplot(rows, cols, j + 1)

                self.plt.imshow(layer[:, :, j])

        self.plt.show()

    def get_conv_layers(self, model):
        conv_layers = []
        for layer in model.layers:
            if layer.__class__.__name__ == 'Conv2D':
                conv_layers.append(layer.name)
        return conv_layers

    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog='cnnactivations', usage=USAGE)
        parser.add_argument('--image', help='path to image')
        parser.add_argument('--model', default=None, help='path to model')
        parser.add_argument(
            '--config', default=CONFIG_DEFAULT, help=HELP_CONFIG)

        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        args = self.parse_args(args)
        cfg = load_config(args.config)
        activations = self.get_activations(args.image, args.model, cfg)
        self.create_figure(activations)


class ShowPredictionPlots(BaseCommand):

    def plot_predictions(self, cfg, tub_paths, model_path, limit, model_type,
                         noshow, dark=False):
        """
        Plot model predictions for angle and throttle against data from tubs.
        """
        import matplotlib.pyplot as plt
        import pandas as pd
        from pathlib import Path
        from donkeycar.pipeline.types import TubDataset

        model_path = os.path.expanduser(model_path)
        model = dk.utils.get_model_by_type(model_type, cfg)
        # This just gets us the text for the plot title:
        if model_type is None:
            model_type = cfg.DEFAULT_MODEL_TYPE
        model.load(model_path)

        user_angles = []
        user_throttles = []
        pilot_angles = []
        pilot_throttles = []

        base_path = Path(os.path.expanduser(tub_paths)).absolute().as_posix()
        dataset = TubDataset(config=cfg, tub_paths=[base_path],
                             seq_size=model.seq_size())
        records = dataset.get_records()[:limit]
        bar = IncrementalBar('Inferencing', max=len(records))

        for tub_record in records:
            input_dict = model.x_transform(
                tub_record, normalize_image)
            pilot_angle, pilot_throttle = \
                model.inference_from_dict(input_dict)
            user_angle = tub_record.underlying['user/angle']
            user_throttle = tub_record.underlying['user/throttle']
            user_angles.append(user_angle)
            user_throttles.append(user_throttle)
            pilot_angles.append(pilot_angle)
            pilot_throttles.append(pilot_throttle)
            bar.next()

        bar.finish()
        angles_df = pd.DataFrame({'user_angle': user_angles,
                                  'pilot_angle': pilot_angles})
        throttles_df = pd.DataFrame({'user_throttle': user_throttles,
                                     'pilot_throttle': pilot_throttles})
        if dark:
            plt.style.use('dark_background')
        fig = plt.figure('Tub Plot')
        fig.set_layout_engine('tight')
        title = f"Model Predictions\nTubs: {tub_paths}\nModel: {model_path}\n" \
                f"Type: {model_type}"
        fig.suptitle(title)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        angles_df.plot(ax=ax1)
        throttles_df.plot(ax=ax2)
        ax1.legend(loc=4)
        ax2.legend(loc=4)
        plt.savefig(model_path + '_pred.png')
        # Ensure the figure is closed and file handles are released so the
        # subprocess can exit reliably and the file is visible to callers.
        try:
            plt.close(fig)
        except (RuntimeError, AttributeError, ValueError) as e:
            # If closing the figure fails for any reason, log a warning and continue.
            logger.warning("Failed closing matplotlib figure: %s", e)
        logger.info('Saving tubplot at %s_pred.png', model_path)
        if not noshow:
            plt.show()

    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog='tubplot', usage=USAGE)
        parser.add_argument('--tub', nargs='+',
                            help='The tub to make plot from')
        parser.add_argument('--model', default=None,
                            help='model for predictions')
        parser.add_argument('--limit', type=int, default=1000,
                            help='how many records to process')
        parser.add_argument('--type', default=None, help='model type')
        parser.add_argument('--noshow', default=False, action="store_true",
                            help='if plot is shown in window')
        parser.add_argument(
            '--config', default=CONFIG_DEFAULT, help=HELP_CONFIG)

        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        args = self.parse_args(args)
        args.tub = ','.join(args.tub)
        cfg = load_config(args.config)
        self.plot_predictions(cfg, args.tub, args.model, args.limit,
                              args.type, args.noshow)


class Train(BaseCommand):

    def parse_args(self, args):
        HELP_FRAMEWORK = 'the AI framework to use (tensorflow|pytorch). ' \
                         'Defaults to config.DEFAULT_AI_FRAMEWORK'
        parser = argparse.ArgumentParser(
            prog='train', usage=USAGE)
        parser.add_argument('--tub', nargs='+', help='tub data for training')
        parser.add_argument('--model', default=None, help='output model name')
        parser.add_argument('--type', default=None, help='model type')
        parser.add_argument(
            '--config', default=CONFIG_DEFAULT, help=HELP_CONFIG)
        parser.add_argument('--myconfig', default=f'./{MYCONFIG}',
                            help=f'file name of {MYCONFIG} file, defaults to {MYCONFIG}')
        parser.add_argument('--framework',
                            choices=['tensorflow', 'pytorch', None],
                            required=False,
                            help=HELP_FRAMEWORK)
        parser.add_argument('--checkpoint', type=str,
                            help='location of checkpoint to resume training from')
        parser.add_argument('--transfer', type=str, help='transfer model')
        parser.add_argument('--comment', type=str,
                            help='comment added to model database - use '
                                 'double quotes for multiple words')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        args = self.parse_args(args)
        args.tub = ','.join(args.tub)
        my_cfg = args.myconfig
        cfg = load_config(args.config, my_cfg)
        framework = args.framework if args.framework \
            else getattr(cfg, 'DEFAULT_AI_FRAMEWORK', 'tensorflow')

        if framework == 'tensorflow':
            from donkeycar.pipeline.training import train
            train(cfg, args.tub, args.model, args.type, args.transfer,
                  args.comment)
        elif framework == 'pytorch':
            from donkeycar.parts.pytorch.torch_train import train
            train(cfg, args.tub, args.model, args.type,
                  checkpoint_path=args.checkpoint)
        else:
            logger.error("Unrecognized framework: %s. Please specify "
                         "one of 'tensorflow' or 'pytorch'", framework)


class ModelDatabase(BaseCommand):

    def parse_args(self, args):
        parser = argparse.ArgumentParser(prog='models', usage=USAGE)
        parser.add_argument(
            '--config', default=CONFIG_DEFAULT, help=HELP_CONFIG)
        parser.add_argument('--group', action="store_true",
                            default=False,
                            help='group tubs and plot separately')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def run(self, args):
        from donkeycar.pipeline.database import PilotDatabase
        args = self.parse_args(args)
        cfg = load_config(args.config)
        p = PilotDatabase(cfg)
        pilot_txt, tub_txt, _ = p.pretty_print(args.group)
        print(pilot_txt)
        print(tub_txt)


class Gui(BaseCommand):
    ''' Launch the Donkey Car GUI.'''

    def run(self, args):
        ''' Run the command with the given args.'''
        from donkeycar.management.ui.ui import main
        main()


def execute_from_command_line():
    """
    This is the function linked to the "donkey" terminal command.
    """
    commands = {
        'createcar': CreateCar,
        'findcar': FindCar,
        'calibrate': CalibrateCar,
        'tubplot': ShowPredictionPlots,
        'tubhist': ShowHistogram,
        'makemovie': MakeMovieShell,
        'createjs': CreateJoystick,
        'cnnactivations': ShowCnnActivations,
        'update': UpdateCar,
        'train': Train,
        'models': ModelDatabase,
        'ui': Gui,
    }

    args = sys.argv[:]

    if len(args) > 1 and args[1] in commands.keys():
        command = commands[args[1]]
        c = command()
        c.run(args[2:])
    else:
        dk.utils.eprint('Usage: The available commands are:')
        dk.utils.eprint(list(commands.keys()))


if __name__ == "__main__":
    execute_from_command_line()
