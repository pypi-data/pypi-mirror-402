from enum import StrEnum
import sys

from wizlib.ui import UI, Chooser, Emphasis
from wizlib.ui.shell.line_editor import ShellLineEditor
from wizlib.ui.shell import S
from wizlib.ui.text_wrapper import StreamingTextWrapper
import wizlib.io

COLOR = {
    Emphasis.INFO: S.BLUE,
    Emphasis.GENERAL: S.CYAN,
    Emphasis.PRINCIPAL: S.YELLOW,
    Emphasis.ERROR: S.RED
}


class ShellUI(UI):

    """The UI to execute one command passed in through the shell. There will be
    limited interactivity, if the user omits an argument on the command line,
    but otherwise this is a run and done situation.
    """

    name = "shell"

    def __init__(self):
        super().__init__()
        self._wrapper = None

    def send(self, value: str = '', emphasis: Emphasis = Emphasis.GENERAL,
             newline: bool = True, wrap: int = 0):
        """Output some text

        Args:
            value: Text to output
            emphasis: Color/emphasis style
            newline: Whether to append a newline
            wrap: Column width to wrap at (0 = no wrapping)
        """
        if wrap > 0:
            # Initialize wrapper if needed or if width changed
            if self._wrapper is None or self._wrapper.width != wrap:
                self._wrapper = StreamingTextWrapper(
                    width=wrap, output_stream=sys.stderr)

            # Use streaming wrapper
            self._wrapper.write_streaming(value, COLOR[emphasis])
            if newline:
                self._wrapper.write_newline()
        else:
            # Original behavior - no wrapping
            end = '\n' if newline else ''
            sys.stderr.write(COLOR[emphasis] + value + S.RESET + end)
            sys.stderr.flush()

    def ask(self, value: str):
        """Prompt for input"""
        if value:
            sys.stderr.write(S.GREEN + value + S.RESET)
            sys.stderr.flush()

    def get_option(self, chooser: Chooser):
        """Get a choice from the user with a single keystroke. Only works when
        in a tty."""
        while True:
            self.ask(chooser.prompt_string)
            key = wizlib.io.ttyin()
            out = chooser.default if key == '\n' else \
                key if key.isprintable() else ''
            choice = chooser.choice_by_key(key)
            emphasis = Emphasis.ERROR if (
                choice is None) else Emphasis.PRINCIPAL
            self.send(out, emphasis=emphasis)
            if choice is not None:
                break
        return choice() if callable(choice) else choice

    def get_text(self, prompt='', choices=[], default=''):
        """Allow the user to input an arbitrary line of text, with possible tab
        completion"""
        self.ask(prompt)
        value = ShellLineEditor(choices, default).edit()
        # else:
        #     value = input()
        return value
