# -*- coding: ascii -*-
import datetime
import json
import sys
import unittest

from sqreen_security_signal_sdk.utils import (CustomJSONEncoder,
                                              reencode_payload)


class JSONTestCase(unittest.TestCase):

    def test_simple_json(self):
        self.assertEqual(
            json.dumps({"foo": "bar"}, cls=CustomJSONEncoder), '{"foo": "bar"}'
        )

    def test_datetime(self):
        date = datetime.datetime.utcnow()

        self.assertEqual(
            json.dumps(date, cls=CustomJSONEncoder), '"%s"' % date.isoformat()
        )

    def test_abstract_repr(self):
        class MyClass(object):
            def __repr__(self):
                return "My custom repr"

        obj = MyClass()
        self.assertEqual(
            json.dumps(obj, cls=CustomJSONEncoder), '"%s"' % obj.__repr__()
        )

    def test_failing_repr(self):
        class MyFailingClass(object):
            def __repr__(self):
                raise KeyError("test")

        obj = MyFailingClass()
        self.assertEqual(
            json.dumps(obj, cls=CustomJSONEncoder),
            '"instance of type %r"' % MyFailingClass,
        )

    @unittest.skipIf(sys.version_info.major > 2, "Only test for Python 2")
    def test_reencode_encoding(self):
        bad_payload = {"foo": ["bar\xe9"]}

        reencoded_payload = reencode_payload(bad_payload)

        self.assertEqual(
            json.dumps(reencoded_payload, cls=CustomJSONEncoder),
            u'{"foo": ["bar\\\\xe9"]}',
        )

    def test_reencode_unicode(self):
        valid_payload = {"foo": [u"\xe9"]}

        reencoded_payload = reencode_payload(valid_payload)

        self.assertEqual(reencoded_payload, valid_payload)

    def test_reencode_other(self):
        self.assertEqual(reencode_payload(42), 42)
