"""
Streaming text wrapper that provides word wrapping with backspace correction
for a typewriter-like streaming experience.
"""

import sys
from enum import Enum
from wizlib.ui import Emphasis


class StreamingTextWrapper:
    """Handles streaming text output with word wrapping that uses backspace
    to correct words that would overflow the line boundary.

    Provides a typewriter-like streaming experience where characters are
    written immediately, but words are moved to the next line if they
    would overflow.
    """

    def __init__(self, width: int = 80, output_stream=None):
        """Initialize the wrapper.

        Args:
            width: Column width to wrap at
            output_stream: Stream to write to (defaults to sys.stderr)
        """
        self.width = width
        self.output_stream = output_stream or sys.stderr
        self._current_col = 0
        self._word_buffer = []  # Buffer for current word being streamed

    def _write_char(self, char: str, color_code: str = ''):
        """Write a single character with optional color."""
        if color_code:
            self.output_stream.write(color_code + char + '\033[0m')
        else:
            self.output_stream.write(char)
        self.output_stream.flush()

    def _backspace_buffer(self):
        """Backspace over the current word buffer."""
        for _ in range(len(self._word_buffer)):
            self.output_stream.write('\b \b')  # backspace, space, backspace
        self.output_stream.flush()

    def write_streaming(self, text: str, color_code: str = ''):
        """Write text with streaming word wrapping.

        Args:
            text: Text to output
            color_code: ANSI color code to apply
        """
        for char in text:
            if char == '\n':
                # Explicit newline - flush buffer and reset
                self._word_buffer = []
                self._write_char(char)
                self._current_col = 0
            elif char in ' \t':
                # Word boundary - write the space and clear buffer
                self._word_buffer = []
                self._write_char(char, color_code)
                self._current_col += 1
            else:
                # Regular character - add to buffer and write immediately
                self._word_buffer.append(char)
                self._write_char(char, color_code)
                self._current_col += 1

                # Check if this character pushed us over the width
                if self._current_col > self.width:
                    # Only backspace and wrap if the word can fit on a new line
                    # If the word itself is longer than width, let it continue
                    if len(self._word_buffer) <= self.width:
                        # We've gone over - backspace the whole current word
                        self._backspace_buffer()
                        self._current_col -= len(self._word_buffer)

                        # Write newline
                        self._write_char('\n')
                        self._current_col = 0

                        # Rewrite word on new line
                        for c in self._word_buffer:
                            self._write_char(c, color_code)
                            self._current_col += 1

    def write_newline(self):
        """Write a newline and reset position."""
        self.output_stream.write('\n')
        self.output_stream.flush()
        self._current_col = 0
        self._word_buffer = []

    def reset_position(self):
        """Reset the column position (useful for explicit positioning)."""
        self._current_col = 0
        self._word_buffer = []

    @property
    def current_column(self):
        """Get the current column position."""
        return self._current_col
