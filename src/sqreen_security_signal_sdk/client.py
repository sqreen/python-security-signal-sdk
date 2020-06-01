# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import sys
from concurrent.futures import ThreadPoolExecutor

from .__about__ import __version__
from .accumulator import BatchingAccumulator
from .compat_model import Signal, SignalType, Trace
from .sender import SyncSender

if sys.version_info >= (3, 5):
    from typing import Any, Optional

    from .compat_model import AnySignal


class SyncClient(object):
    """Send signals to the Sqreen Ingestion service.

    :param token: Your application API token.
    :param app_name: (optional) Your application name.
    :param proxy_url: (optional) Send requests througth this proxy.
    :param max_batch_size: (optional) Maximum number of items sent per batch (default to 50).
    :param interval_batch: (optional) Interval at which non-empty batch should be sent (default to 60s).
    :param session_token: (optional) When true, token is a session token instead of an API token.
    """

    accumulator_class = BatchingAccumulator
    sender_class = SyncSender

    user_agent = "sqreen-python-security-signal-sdk/{}".format(__version__)
    max_workers = 2

    def __init__(self, token, app_name=None, proxy_url=None, max_batch_size=50,
                 interval_batch=60, session_token=False):
        # type: (str, Optional[str], Optional[str], int, float, bool) -> None

        headers = {"User-Agent": self.user_agent}
        if session_token:
            headers["X-Session-Key"] = token
        else:
            headers["X-Api-Token"] = token
            if app_name is not None:
                headers["X-App-Name"] = app_name

        self.sender = self.sender_class(proxy_url=proxy_url, headers=headers)
        self.accumulator = self.accumulator_class(
            max_batch_size=max_batch_size, linger_time=interval_batch)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def point(self, signal_name, payload, **properties):  # type: (str, Any, **Any) -> None
        """Record a point signal to be sent."""
        properties["type"] = SignalType.POINT.value
        return self.signal(signal_name, payload, **properties)

    def metric(self, signal_name, payload, **properties):  # type: (str, Any, **Any) -> None
        """Record a metric signal to be sent."""
        properties["type"] = SignalType.METRIC.value
        return self.signal(signal_name, payload, **properties)

    def signal(self, signal_name, payload, **properties):  # type: (str, Any, **Any) -> None
        """Record a signal to be sent."""
        signal = dict(signal_name=signal_name, payload=payload)  # type: Signal
        signal.update(properties)  # type: ignore
        return self._add_and_send(signal)

    def trace(self, data, **properties):  # type: (Any, **Any) -> None
        """Record a trace to be sent."""
        trace = dict(data=data)  # type: Trace
        trace.update(properties)  # type: ignore
        return self._add_and_send(trace)

    def _add_and_send(self, data):  # type: (AnySignal) -> None
        batch = self.accumulator.add(data)
        if batch:
            self.executor.submit(self.sender.send_batch, batch)

    def flush(self, soft=False):  # type: (bool) -> None
        """Send all pending signals and traces.

        :param soft: (optional) Do not send the batch if it has not exceeded
        the interval time.
        """
        batch = self.accumulator.flush(soft=soft)
        if batch:
            self.executor.submit(self.sender.send_batch, batch)

    def close(self):  # type: () -> None
        """Close the client.
        """
        self.executor.shutdown(wait=True)
        self.sender.close()


Client = SyncClient
