# Patch inputs and outputs for easy testing

from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch


class WizLibTestCase(TestCase):
    """Wrap your test cases in this class to use the patches correctly"""

    def setUp(self):
        """Test cases should never use true interaction"""
        self.notty = patch('wizlib.io.TTY_OK', False)
        self.notty.start()

    def tearDown(self):
        self.notty.stop()

    @staticmethod
    def patch_stream(val: str):
        """Patch stream input such as pipes for stream handler"""
        # mock = Mock(return_value=val)
        # return patch('wizlib.io.stream', mock)
        # return patch('wizlib.stream_handler.StreamHandler.read', mock)
        return patch('wizlib.stream_handler.StreamHandler.text', val)

    @staticmethod
    def patch_ttyin(val:str='\n'):
        """Patch input typed by a user in shell ui"""
        mock = Mock(side_effect=val)
        # mock = Mock(return_value = val)
        return patch('wizlib.io.ttyin', mock)

    @staticmethod
    def patcherr():  # pragma: nocover
        return patch('sys.stderr', StringIO())

    @staticmethod
    def patchout():  # pragma: nocover
        return patch('sys.stdout', StringIO())
