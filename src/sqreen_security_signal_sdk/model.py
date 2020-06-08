# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
from datetime import datetime
from enum import Enum
from typing import Any, List, Sequence, TypedDict, Union


class SignalType(str, Enum):
    POINT = "point"
    METRIC = "metric"


class SignalProperties(TypedDict, total=False):
    actor: Any
    context: Any
    context_schema: str
    location: Any
    location_infra: Any
    payload_schema: str
    source: str
    trigger: Any
    time: datetime
    type: SignalType


class Signal(SignalProperties):
    signal_name: str
    payload: Any


class TraceProperties(SignalProperties, total=False):
    signal_name: str
    payload: Any


class Trace(TraceProperties):
    data: Sequence[Signal]


AnySignal = Union[Signal, Trace]


class Batch(List[AnySignal]):
    pass
