# Note that commands once used dataclass, but no longer.

from argparse import ArgumentParser
from pathlib import Path

from wizlib.class_family import ClassFamily
from wizlib.config_handler import ConfigHandler
from wizlib.stream_handler import StreamHandler
from wizlib.super_wrapper import SuperWrapper
from wizlib.ui import UI


class CommandCancellation(BaseException):
    pass


class WizCommand(ClassFamily, SuperWrapper):
    """Define all the args you want, but stdin always works."""

    status = ''

    @classmethod
    def add_args(self, parser):
        """Add arguments to the command's parser - override this.
        Add global arguments in the base class. Not wrapped."""
        pass

    def __init__(self, app=None, **vals):
        self.app = app
        for key in vals:
            setattr(self, key, vals[key])

    def handle_vals(self):
        """Clean up vals, calculate any, ask through UI, etc. - override
        this and call super().handle_vals()."""
        pass

    def provided(self, argument):
        """Was an argument provided?"""
        value = None
        if hasattr(self, argument):
            value = getattr(self, argument)
        return True if (value is False) else bool(value)

    def execute(self, method, *args, **kwargs):
        """Actually perform the command - override and wrap this via
        SuperWrapper"""
        try:
            self.handle_vals()
            result = method(self, *args, **kwargs)
            return result
        except CommandCancellation as cancellation:
            self.status = str(cancellation) if str(cancellation) else None


class WizHelpCommand(WizCommand):

    def execute(self):
        return self.help
