# Abstract classes for UIs. The idea here is to allow many different user
# interfaces (shell, curses, Slack, etc) to drive the same data model without
# the data model needing specific UI knowledge.
#
# Commands might call back to the UI for confirmations or arguments that are
# previously omitted, using the get_ methods.

#
# UI end classes must implement the following interface:
#
# start(): No arguments. Actually performs the operation of the UI. It might be
# short running (in the case of a shell UI) or long-running (in the case of an
# interactive UI).
#
# output(intro=""): Output some multi-line text explaining an action, usually a
# list of items being acted upon.
#
# get_string(prompt, default=""): For arguments that are omitted, get a string
# from the user. The prompt is just a word (like "Description") telling the
# user what to input.
#
# get_confirmation(verb): For delete-oriented commands to confirm with the user
# before proceeding. Verb is what we're asking the user to confirm. Description
# can be multiple lines, as with get_string. Returns a boolean saying whether
# the action is confirmed.

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from wizlib.class_family import ClassFamily


class Emphasis(Enum):
    """Semantic style"""
    INFO = 1
    GENERAL = 2
    PRINCIPAL = 3
    ERROR = 4


@dataclass
class Choice:
    """A single option, equivalent to a single radio button or select option in
    HTML.

    text - text of the option

    keys - keystrokes that might indicate this option in a keyboard-driven UI

    action - what to do when chosen
    """

    text: str = ''
    keys: str = ''
    action: object = None

    @property
    def key(self):
        return self.keys[0] if self.keys else ''

    def hit_key(self, key):
        return key in self.keys

    def hit_text(self, text):
        return self.text.startswith(text)

    @property
    def value(self):
        return self.text if (self.action is None) else self.action

    @property
    def key_prompt(self):
        """Text with keystroke in parens"""
        for key in self.keys:
            if key in self.text:
                pre, it, post = self.text.partition(key)
                return f"{pre}({it}){post}"
        return f"({self.keys[0]}){self.text}"


# TODO: Decide whether the Prompt/Chooser division makes sense

class Prompt:
    """Tell the user what kind of input to provide"""

    def __init__(self, intro: str = '', default: str = ''):
        self.intro = intro
        self.default = default

    @property
    def prompt_string(self):
        """Simple prompt string for stdio, no colours"""
        result = []
        if self.intro:
            result.append(self.intro)
        if self.default:
            result.append(f"[{self.default}]")
        for choice in self.choices:
            if choice.text == self.default:
                continue
            result.append(choice.key_prompt)
        return " ".join(result) + ": "


class Chooser(Prompt):
    """Hold a set of choices and get the result"""

    def __init__(self, intro: str = '', default: str = '', choices=None):
        super().__init__(intro, default)
        if isinstance(choices, dict):
            self.choices = [Choice(choices[k], k) for k in choices]
        elif isinstance(choices, list):
            self.choices = [(c if isinstance(c, Choice) else Choice(c))
                            for c in choices]
        else:
            self.choices = []

    def add_choice(self, *args, **kwargs):
        choice = Choice(*args, **kwargs)
        self.choices.append(choice)

    def choice_by_key(self, key):
        if key == '\n' and self.default:
            choice = self.choices[0].value
        else:
            choice = next(
                (o.value for o in self.choices if key in o.keys), None)
        return choice

    def choices_by_text(self, text):
        return [o.value for o in self.choices if o.hit_text(text)]


@dataclass
class UI(ClassFamily):

    def send(self, value: str = '', emphasis: Emphasis = Emphasis.GENERAL):
        pass
