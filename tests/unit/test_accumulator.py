import datetime
import unittest

import freezegun
from sqreen_security_signal_sdk.accumulator import BatchingAccumulator
from sqreen_security_signal_sdk.compat_model import Batch, Signal


class BatchingAccumulatorTestCase(unittest.TestCase):

    @freezegun.freeze_time()
    def test_single_item_batch(self):
        acc = BatchingAccumulator(max_batch_size=1)
        s = Signal(signal_name="test", payload={})
        ret = acc.add(s)
        self.assertEqual(ret, Batch([s]))
        self.assertIsNone(acc.flush())

    @freezegun.freeze_time()
    def test_lot_of_items_batch(self):
        acc = BatchingAccumulator(max_batch_size=50)
        for i in range(49):
            s = Signal(signal_name="test{:03}".format(i), payload={})
            self.assertIsNone(acc.add(s))
        ret = acc.add(Signal(signal_name="boom", payload={}))
        self.assertEqual(len(ret), 50)
        self.assertIsNone(acc.flush())

    @freezegun.freeze_time()
    def test_recycling_accumulator(self):
        acc = BatchingAccumulator(max_batch_size=2)
        s1 = Signal(signal_name="test", payload={})
        self.assertIsNone(acc.add(s1))
        s2 = Signal(signal_name="boom", payload={})
        ret = acc.add(s2)
        self.assertEqual(ret, Batch([s1, s2]))
        self.assertIsNone(acc.add(s1))
        ret = acc.flush()
        self.assertEqual(ret, Batch([s1]))
        self.assertIsNone(acc.add(s1))

    def test_linger(self):
        with freezegun.freeze_time() as frozen_time:
            acc = BatchingAccumulator(max_batch_size=100, linger_time=0.300)
            frozen_time.tick(delta=datetime.timedelta(milliseconds=500))
            s1 = Signal(signal_name="test", payload={})
            self.assertIsNone(acc.add(s1))
            frozen_time.tick(delta=datetime.timedelta(milliseconds=500))
            s2 = Signal(signal_name="boom", payload={})
            ret = acc.add(s2)
            self.assertEqual(ret, Batch([s1, s2]))
