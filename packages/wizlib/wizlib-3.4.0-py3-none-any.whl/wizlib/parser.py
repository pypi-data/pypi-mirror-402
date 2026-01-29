"""A drop-in replacement for ArgumentParser that always raises exceptions
for argument errors (including unrecognized arguments) and returns help
messages in a 'help' item in the resulting namespace. Useful especially for
REPLs."""


from argparse import ArgumentParser
from argparse import ArgumentError
from argparse import Action
from argparse import SUPPRESS
from contextlib import redirect_stdout
from io import StringIO
import sys
import os


# We found the help process a little clumsy

class WizHelpAction(Action):

    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=None):
        super(WizHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        with redirect_stdout(output := StringIO()):
            parser.print_help()
        output.seek(0)
        setattr(namespace, self.dest, output.read())


class WizArgumentError(ArgumentError):

    def __init__(self, message):
        self.argument_name = None
        self.message = message


class WizParser(ArgumentParser):

    def __init__(self, **vals):
        vals['exit_on_error'] = False
        vals['add_help'] = False
        super().__init__(**vals)
        self.add_argument('--help', '-h', action=WizHelpAction)

    def error(self, *args, **vals):
        raise WizArgumentError(str(args[0]))
