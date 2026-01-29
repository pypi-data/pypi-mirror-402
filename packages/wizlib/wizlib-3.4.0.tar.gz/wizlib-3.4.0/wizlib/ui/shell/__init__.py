# We use an odd misc of nonprintable ASCII, ANSI escape sequences, with some
# custom preferences. So define them all here.


from enum import StrEnum


def sequence(hexes: str) -> str:
    return bytes.fromhex(hexes).decode()


ESC = sequence("1b")

# TODO: Is any of this available in the standard library?


class S(StrEnum):
    LEFT = sequence("1b5b44")
    RIGHT = sequence("1b5b43")
    BACKSPACE = sequence("7f")
    BEGINNING = sequence("01")
    END = sequence("05")
    RETURN = sequence("0a")
    TAB = sequence("09")
    SHIFT_TAB = sequence("1b5b5a")
    LEFT_WORD = sequence("1b62")
    RIGHT_WORD = sequence("1b66")
    KILL = sequence("0b")
    RESET = ESC + "[0m"
    FAINT = ESC + "[2m"
    BOLD = ESC + "[1m"
    SEPARATORS = ' -_.,'
    SPACE = ' '
    RED = ESC + '[31m'
    GREEN = ESC + '[32m'
    YELLOW = ESC + '[33m'
    BLUE = ESC + '[34m'
    MAGENTA = ESC + '[35m'
    CYAN = ESC + '[36m'
    CLEAR = ESC + '[2J'

    # Alternative keys that can be configured in a terminal emulator
    CUSTOM_END = ESC + '[1;5C'
    CUSTOM_BEGINNING = ESC + '[1;5D'
    CUSTOM_RIGHTWORD = ESC + '[1;3C'
    CUSTOM_LEFTWORD = ESC + '[1;3D'
