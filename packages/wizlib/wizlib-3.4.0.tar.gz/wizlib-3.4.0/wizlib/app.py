from argparse import ArgumentError
import sys
from dataclasses import dataclass
import os
from pathlib import Path

from wizlib.class_family import ClassFamily
from wizlib.command import WizHelpCommand
from wizlib.super_wrapper import SuperWrapper
from wizlib.parser import WizArgumentError, WizParser
from wizlib.ui import UI


RED = '\033[91m'
RESET = '\033[0m'


class AppCancellation(BaseException):
    pass


class WizApp:
    """Root of all WizLib-based CLI applications. Subclass it. Can be
    instantiated and then run multiple commands."""

    # Name of this app, used in argparse (override)
    name = ''

    # Base command class, typically defined in command/__init__.py (override)
    base = None

    # List of Handler classes used by this app (override)
    handlers = []

    # Set some default types so linting works
    ui: UI

    @classmethod
    def main(cls):  # pragma: nocover
        """Call this from a __main__ entrypoint"""
        cls.start(*sys.argv[1:], debug=os.getenv('DEBUG'))

    @classmethod
    def start(cls, *args, debug=False):
        """Call this from a Python entrypoint"""
        try:
            cls.initialize()
            try:
                ns = cls.parser.parse_args(args)
                if (ns.command is None) and (not hasattr(ns, 'help')):
                    ns = cls.dparser.parse_args(args)
            except ArgumentError as e:
                ns = cls.dparser.parse_args(args)
            app = cls(**vars(ns))
            app.run(**vars(ns))
        except AppCancellation as cancellation:
            if str(cancellation):
                print(str(cancellation), file=sys.stderr)
        except BaseException as error:
            if debug:
                raise error
            else:
                name = type(error).__name__
                print(f"\n{RED}{name}{': ' if str(error) else ''}" +
                      f"{error}{RESET}", file=sys.stderr)
                sys.exit(1)

    @classmethod
    def initialize(cls):
        """Set up the parser for the app class"""
        cls.parser = WizParser(prog=cls.name)
        subparsers = cls.parser.add_subparsers(dest='command')
        cls.dparser = WizParser(prog=f"{cls.name} {cls.base.default}")
        for command in cls.base.family_members('name'):
            key = command.get_member_attr('key')
            aliases = [key] if key else []
            subparser = subparsers.add_parser(command.name, aliases=aliases)
            if command.name == cls.base.default:
                command.add_args(cls.dparser)
            command.add_args(subparser)
        for handler in cls.handlers:
            handler.add_args(cls.parser)
            # Throws ArgumentError if the default command includes an optional
            # argument that overlaps with one of the handlers
            handler.add_args(cls.dparser)

    def __init__(self, **vals):
        """Create the app. Only interested in the handlers from the parsed
        values passed in"""
        for hcls in self.handlers:
            val = vals[hcls.name] if (hcls.name in vals) else hcls.default
            handler = hcls.setup(val)
            handler.app = self
            setattr(self, hcls.name, handler)

    def run(self, **vals):
        """Perform a command. May be called more than once. Only interested in
        the command itself and its specific arguments from the values passed
        in."""
        if 'help' in vals:
            ccls = WizHelpCommand
        else:
            c = 'command'
            cname = (vals.pop(c) if c in vals else None) or self.base.default
            ccls = self.base.family_member('name', cname)
            if not ccls:
                raise Exception(f"Unknown command {cname}")
        command = ccls(self, **vals)
        result = command.execute()
        if result:
            print(result, end='')
            if sys.stdout.isatty():  # pragma: nocover
                print()
        if command.status:
            print(command.status, file=sys.stderr)

    def parse_run(self, *args):
        """For testing, parse just the command part and tun"""
        ns = self.parser.parse_args(args)
        self.run(**vars(ns))
