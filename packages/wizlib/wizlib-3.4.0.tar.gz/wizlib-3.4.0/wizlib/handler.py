from argparse import Action

from wizlib.parser import WizParser


class Handler:
    """Base class for handlers"""

    default = ''
    app = None

    @classmethod
    def add_args(cls, parser: WizParser):
        parser.add_argument(
            f"--{cls.name}",
            f"-{cls.name[0]}",
            default=cls.default)

    @classmethod
    def setup(cls, val):
        return cls(val)

    def __init__(self, val=None):
        pass
