# -*- coding: utf-8 -*-
import datetime
import json
import unittest

from sqreen_security_signal_sdk.sender import Sender


class SenderJSONEncoderTestCase(unittest.TestCase):

    def test_bytes(self):
        data = {
            "signal_name": b"\xe9",
            "payload": {}
        }
        expected = {
            "signal_name": "�",
            "payload": {}
        }
        result = json.loads(Sender().serialize_data(data))
        self.assertEqual(expected, result)

    def test_datetime(self):
        data = {
            "signal_name": "test",
            "payload": {"time": datetime.datetime(2020, 4, 14, 15, 3, 19)}
        }
        expected = {
            "signal_name": "test",
            "payload": {"time": "2020-04-14T15:03:19"}
        }
        result = json.loads(Sender().serialize_data(data))
        self.assertEqual(expected, result)

    def test_repr(self):
        obj = object()
        data = {
            "signal_name": "test",
            "payload": {"object": obj}
        }
        expected = {
            "signal_name": "test",
            "payload": {"object": repr(obj)}
        }
        result = json.loads(Sender().serialize_data(data))
        self.assertEqual(expected, result)
