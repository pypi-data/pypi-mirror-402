# Primitive i/o functions referenced elsewhere, useful for test patching (a
# sort of dependency injection

import sys

import readchar

from wizlib.parser import WizArgumentError
from wizlib.ui.shell import ESC


# Is it OK to read tty input? Patch this for testing

TTY_OK = True

# ISATTY = all(s.isatty() for s in (sys.stdin, sys.stdout, sys.stderr))


# def isatty():
#     return ISATTY


# def stream():
#     return '' if ISATTY else sys.stdin.read()


def ttyin():  # pragma: nocover
    """Read a character from the tty (via readchar). Patch this for testing."""
    if TTY_OK:
        key = readchar.readkey()
        # Handle specialized escape sequences
        if key == ESC + '[1;':
            key = key + readchar.readkey() + readchar.readkey()
        return key
    else:
        raise WizArgumentError(
            'Command designed for interactive use')
