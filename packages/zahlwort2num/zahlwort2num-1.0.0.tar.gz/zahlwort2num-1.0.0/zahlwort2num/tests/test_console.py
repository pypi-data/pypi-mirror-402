from _ctypes import ArgumentError
from unittest import TestCase
from unittest.mock import patch
from zahlwort2num.command_line import main


class TestConsole(TestCase):
    @patch('sys.argv', ['test_script'])
    def test_basic(self):
        self.assertRaises(ArgumentError, main)
