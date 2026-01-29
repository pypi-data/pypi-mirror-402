from argparse import Namespace
from functools import cached_property
from pathlib import Path
import os
from dataclasses import dataclass
import re
import shlex
import subprocess
from unittest.mock import patch

import yaml

from wizlib.handler import Handler
from wizlib.error import ConfigHandlerError
from wizlib.parser import WizParser


class ConfigHandler(Handler):
    """
    Handle app-level configuration, where settings could come from specific
    settings (such as from argparse), environment variables, or a YAML file.
    Within the Python code, config keys are underscore-separated all-lower.

    A ConfigHandler returns null in the case of a missing value, assuming that
    commands can handle their own null cases.
    """

    name = 'config'

    @classmethod
    def setup(cls, val):
        """Allow for alternative setup, passing in an injected data value as a
        dict, bypassing file loading, for testing. Possible long-term
        alternative to .fake() below."""

        if isinstance(val, str) or isinstance(val, Path):
            return cls(file=val)
        elif isinstance(val, dict) or isinstance(val, list):
            return cls(data=val)

    def __init__(self, file: str = None, data: dict = None):
        """Initiatlize with either a yaml file path or a data block to inject
        (for testing)"""
        self.file = file
        self.injected_data = data
        self.cache = {}

    @cached_property
    def data(self):
        """Returns the full set of configuration data, typically loaded from a
        yaml file. Is cached in code."""

        # If yaml_dict was provided, use it directly
        if self.injected_data is not None:
            return self.injected_data

        path = None
        if self.file:
            path = Path(self.file)
        elif self.app and self.app.name:
            localpath = Path.cwd() / f".{self.app.name}.yml"
            homepath = Path.home() / f".{self.app.name}.yml"
            if (envvar := self.env(self.app.name + '-config')):
                path = Path(envvar)
            elif (localpath.is_file()):
                path = localpath
            elif (homepath.is_file()):
                path = homepath
        if path:
            with open(path) as file:
                data = yaml.safe_load(file)
                return data

    @staticmethod
    def env(name):
        if (envvar := name.upper().replace('-', '_')) in os.environ:
            return os.environ[envvar]

    def get(self, data_path: str):
        """Return the value for the requested config entry. If the value is a
        string, evaluate it for shell-type expressions using $(...) syntax. Can
        also return a dict or array. Note that the value returned is cached
        against the data_path, so future calls may not address nested paths.

        data_path: Hyphen-separated path through the yaml/dict hierarchy."""

        # If we already found the value, return it
        if data_path in self.cache:
            return self.cache[data_path]

        # Environment variables take precedence
        if (result := self.env(data_path)):
            self.cache[data_path] = result
            return result

        # Otherwise look at the YAML or injected data
        if (data := self.data):
            split = data_path.split('-')
            while (key := split.pop(0)) and (key in data):
                data = data[key] if key in data else None
                if not split:
                    if isinstance(data, str):
                        data = evaluate_string(data)
                    self.cache[data_path] = data
                    return data

    @classmethod
    def fake(cls, **vals):
        """Return a fake ConfigHandler with forced values, for testing"""
        self = cls()
        self.cache = {k.replace('_', '-'): vals[k] for k in vals}
        return self


def os_process(match):
    """Run a subprocess in shell form"""
    command_string = match.group(1).strip()
    command = shlex.split(command_string)
    result = subprocess.run(command, capture_output=True)
    return result.stdout.decode().strip()


def evaluate_string(yaml: str) -> str:
    """Evaluate shell commands in string values"""
    text = yaml.strip()
    return re.sub(r'\$\((.*?)\)', os_process, text)
