# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import sys
import threading
import time

from .compat_model import Batch

if sys.version_info >= (3, 5):
    from typing import Optional

    from .compat_model import AnySignal


class BatchingAccumulator(object):
    """Accumulate signals into a batch.

    :param max_batch_size: (optional) Maximum number of items in the batch (default to 50).
    :param linger_time: (optional) Maximum age of a non-empty batch in seconds (default to 60s).
    """

    def __init__(self, max_batch_size=50, linger_time=60):
        # type: (int, float) -> None
        self.max_batch_size = max_batch_size
        self.linger_ms = int(linger_time * 1000)
        self.batch = Batch()
        self.batch_creation_time = 0
        self.batch_lock = threading.RLock()

    def add(self, signal):  # type: (AnySignal) -> Optional[Batch]
        """Add a signal to the current batch and flush it if needed."""
        with self.batch_lock:
            if not self.batch:
                self.batch_creation_time = self._current_time_ms()
            self.batch.append(signal)
            return self.flush(soft=True)

    def flush(self, soft=False):  # type: (bool) -> Optional[Batch]
        """Flush the current batch if not empty.

        :param soft: (optional) Do not flush the batch if it has not exceeded
        the linger time.
        """
        with self.batch_lock:
            if soft:
                now = self._current_time_ms()
                soft = len(self.batch) < self.max_batch_size \
                    and (now - self.batch_creation_time) < self.linger_ms
            if not soft and self.batch:
                batch = self.batch
                self.batch = Batch()
                return batch
            return None

    @staticmethod
    def _current_time_ms():  # type: () -> int
        return int(time.time() * 1000)
