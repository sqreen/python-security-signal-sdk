# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import codecs
import datetime
import json
import sys

if sys.version_info >= (3, 5):
    from typing import Mapping, Iterable

    string_type = str
elif sys.version_info[0] >= 3:
    from collections.abc import Mapping, Iterable

    string_type = str
else:
    from collections import Mapping, Iterable

    string_type = basestring  # noqa


def codecs_error_ascii_to_hex(exception):
    """On unicode decode error (bytes -> unicode error), tries to replace
    invalid unknown bytes by their hex notation."""
    if isinstance(exception, UnicodeDecodeError):
        obj = exception.object
        start = exception.start
        end = exception.end

        invalid_part = obj[start:end]
        result = []

        for character in invalid_part:
            # Python 2 strings
            if isinstance(character, str):
                result.append(u"\\x{}".format(character.encode("hex")))
            # Python 3 int
            elif isinstance(character, int):
                result.append(u"\\{}".format(hex(character)[1:]))
            else:
                raise exception
        result = ("".join(result), end)
        return result
    raise exception


codecs.register_error("__sqreen_ascii_to_hex", codecs_error_ascii_to_hex)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JsonEncoder which can handle datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode("utf-8", errors="__sqreen_ascii_to_hex")
        else:
            try:
                return repr(obj)
            except Exception:
                return "instance of type {}".format(repr(obj.__class__))


def reencode_payload(payload):
    """Do everything necessary to be able to encode a payload into JSON."""
    if isinstance(payload, (bytes, string_type)):
        return _reencode_string(payload)
    elif isinstance(payload, Mapping):
        return {
            _reencode_string(key): reencode_payload(value)
            for key, value in payload.items()
        }
    elif isinstance(payload, Iterable):
        return [reencode_payload(item) for item in payload]
    return payload


def _reencode_string(string):
    """Ensure that the string is encodable into JSON."""
    if isinstance(string, bytes):
        return string.decode("utf-8", errors="__sqreen_ascii_to_hex")
    return string
