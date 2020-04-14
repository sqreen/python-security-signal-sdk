# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import sys

if sys.version_info >= (3, 8):
    # The syntax of this module is not compatible with Python 2.7, lazy loading it.

    from .model import AnySignal, Batch, SignalType, Signal, Trace

elif sys.version_info >= (3, 5):
    # Fallback to more basic types.

    from enum import Enum
    from typing import Any, Dict, List, Union

    class SignalType(Enum):
        POINT = "point"
        METRIC = "metric"

    class Signal(Dict[str, Any]):
        pass

    class Trace(Dict[str, Any]):
        pass

    AnySignal = Union[Signal, Trace]

    class Batch(List[AnySignal]):
        pass

else:
    # Compatibility types for Python environments without the typing module.
    class SignalType:
        class POINT:
            name = "POINT"
            value = "point"

        class METRIC:
            name = "METRIC"
            value = "metric"

    class Signal(dict):
        """
        Compatibility type for signals.
        """

    class Trace(dict):
        """
        Compatibility type for traces.
        """

    class Batch(list):
        """
        Compatibility type for batches.
        """
