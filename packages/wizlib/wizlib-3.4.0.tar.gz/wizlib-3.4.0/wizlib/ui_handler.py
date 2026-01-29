from pathlib import Path
import sys

from wizlib.handler import Handler
from wizlib.ui import UI


class UIHandler(Handler):
    """A sort of proxy-handler for the UI class family, which drives user
    interactions (if any) during and between command execution. In this case,
    the handler only contains class-level methods, because the action actually
    returns the UI itself for the command to use."""

    name = 'ui'
    default = 'shell'

    @classmethod
    def setup(cls, uitype):
        return UI.family_member('name', uitype)()

    @classmethod
    def fake(cls, val=None):
        """Use mock_keys"""
        return
