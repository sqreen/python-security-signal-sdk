import json
import unittest

from sqreen_security_signal_sdk.compat_model import SignalType


class EnumTestCase(unittest.TestCase):

    def test_json_convertion(self):
        self.assertEqual(json.dumps(SignalType.POINT), '"point"')
        self.assertEqual(json.dumps(SignalType.METRIC), '"metric"')

    def test_enum_type(self):
        self.assertIsInstance(SignalType.POINT, str)
        self.assertIsInstance(SignalType.METRIC, str)
