# -*- coding: utf-8 -*-
"""
Created on Wed Sep 13 21:27:44 2017

@author: wroscoe
"""
import os
import types
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Config class for managing application configuration.
    This class provides methods to load, update, display, and save configuration
    settings from various sources such as Python files, dictionaries, and objects.
    Configuration keys are expected to be uppercase.
    Methods
    -------
    from_pyfile(filename):
        Loads configuration from a JSON file and updates the config object.
    from_object(obj):
        Updates the config object with uppercase attributes from the given object.
    from_dict(d, keys=None):
        Overwrites config values from a dictionary for specified keys or all if keys is empty.
    __str__():
        Returns a string representation of all uppercase config attributes.
    show():
        Prints all uppercase config attributes and their values.
    to_pyfile(path):
        Writes all uppercase config attributes to a Python file at the specified path.
    """

    def from_pyfile(self, filename):
        """Load config values from a Python config file.

        The configuration file is executed in a fresh module namespace and
        any UPPERCASE attributes are copied into this Config instance.
        """
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('config', filename)
            module = importlib.util.module_from_spec(spec)
            if spec is None or spec.loader is None:
                raise IOError(f'Unable to load configuration file: {filename}')
            spec.loader.exec_module(module)
            d = module
            d.__file__ = filename
        except Exception as e:
            err_msg = getattr(e, 'strerror', None) or str(e)
            error_message = f'Unable to load configuration file: {err_msg}'
            raise IOError(error_message) from e
        self.from_object(d)
        return True

    def from_object(self, obj):
        """Update config values from an object."""
        for key in dir(obj):
            if key.isupper():
                setattr(self, key, getattr(obj, key))

    def from_dict(self, d, keys=None):
        """Overwrite config values from a dictionary."""
        keys = keys or []
        msg = 'Overwriting config with: '
        for k, v in d.items():
            if k.isupper() and (k in keys or not keys):
                setattr(self, k, v)
                msg += f'{k}:{v}, '
        logger.info(msg)

    def __str__(self):
        """Return a string representation of all uppercase config attributes."""
        result = []
        for key in dir(self):
            if key.isupper():
                result.append((key, getattr(self, key)))
        return str(result)

    def show(self):
        """Print all uppercase config attributes and their values."""
        for attr in dir(self):
            if attr.isupper():
                print(attr, ":", getattr(self, attr))

    def to_pyfile(self, path):
        """Write all uppercase config attributes to a Python file."""
        lines = []
        for attr in dir(self):
            if attr.isupper():
                v = getattr(self, attr)
                if isinstance(v, str):
                    v = f'"{v}"'
                lines.append(f'{attr} = {v}{os.linesep}')
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


def load_config(config_path=None, myconfig="myconfig.py"):
    """
    Load the main configuration file and optionally override with a personal configuration file.
    Args:
        config_path (str, optional): Path to the main configuration file. If None, attempts to find 'config.py'
            in the current working directory or current directory.
        myconfig (str, optional): Filename for the personal configuration file to override main config.
            Defaults to 'myconfig.py'.
    Returns:
        Config: An instance of Config with settings loaded from the main config file and optionally overridden
            by the personal config file.
    Logs:
        - Info message when loading the main and personal config files.
        - Warning if the personal config file is not found.
    """
    if config_path is None:
        main_path = os.getcwd()
        config_path = os.path.join(main_path, 'config.py')
        if not os.path.exists(config_path):
            local_config = os.path.join(os.path.curdir, 'config.py')
            if os.path.exists(local_config):
                config_path = local_config

    logger.info('loading config file: %s', config_path)
    cfg = Config()
    cfg.from_pyfile(config_path)

    # look for the optional myconfig.py in the same path.
    personal_cfg_path = config_path.replace("config.py", myconfig)
    if os.path.exists(personal_cfg_path):
        logger.info("loading personal config over-rides from %s", myconfig)
        personal_cfg = Config()
        personal_cfg.from_pyfile(personal_cfg_path)
        cfg.from_object(personal_cfg)
    else:
        logger.warning("personal config: file not found %s", personal_cfg_path)

    return cfg
