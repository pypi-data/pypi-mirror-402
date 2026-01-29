import os
from pathlib import Path
import sys

from wizlib.handler import Handler
from wizlib.parser import WizParser
import wizlib.io


class StreamHandler(Handler):
    """Handle non-interactive input, such as via a pipe in a shell. Only
    applies when not in a tty. Doesn't actually stream anything and should
    probably be called PipedInputHandler in a future major upgrade."""

    name = 'stream'

    def __init__(self, file=None):
        if file:
            self._text = Path(file).read_text()
        elif sys.stdin.isatty():
            self._text = ''
        else:
            self._text = sys.stdin.read()
            # Reset sys.stdin to tty for possible interactions
            # if os.path.exists(os.ctermid()):
            try:
                sys.stdin = open(os.ctermid(), 'r')
            except OSError:
                pass

    @property
    def text(self):
        return self._text
    
    def read(self):
        return self.text