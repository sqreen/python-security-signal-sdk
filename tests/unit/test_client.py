import unittest

from sqreen_security_signal_sdk.client import Client
from sqreen_security_signal_sdk.sender import BaseSender


class FakeSender(BaseSender):

    def send(self, endpoint, data, headers={}, **kwargs):
        # Do not send anything but return the input data if not closed.
        if hasattr(self, "closed"):
            raise RuntimeError
        return data

    def close(self, **kwargs):
        self.closed = True


class FakeClient(Client):

    sender_class = FakeSender


class ClientTestCase(unittest.TestCase):

    def test_metric(self):
        client = FakeClient(token="42", app_name="test", max_batch_size=1)
        ret = client.metric(signal_name="test", payload={})
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["type"], "metric")

        ret = client.metric(signal_name="test", payload={}, actor="hello")
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["actor"], "hello")

        self.assertEqual(client.sender.headers["X-Api-Token"], "42")
        self.assertEqual(client.sender.headers["X-App-Name"], "test")
        self.assertNotIn("X-Session-Key", client.sender.headers)

    def test_point(self):
        client = FakeClient(token="42", session_token=True, max_batch_size=1)
        ret = client.point(signal_name="test", payload={})
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["type"], "point")

        ret = client.point(signal_name="test", payload={}, actor="hello")
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["actor"], "hello")

        self.assertEqual(client.sender.headers["X-Session-Key"], "42")
        self.assertNotIn("X-App-Name", client.sender.headers)
        self.assertNotIn("X-Api-Token", client.sender.headers)

    def test_trace(self):
        client = FakeClient(token="42", max_batch_size=1)
        ret = client.trace({})
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["data"], {})

        ret = client.trace(data={}, actor="hello")
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["actor"], "hello")

    def test_flush(self):
        client = FakeClient(token="42", max_batch_size=2)
        self.assertIsNone(client.flush())
        self.assertIsNone(client.trace({}))
        ret = client.flush()
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["data"], {})

    def test_close(self):
        client = FakeClient(token="42", max_batch_size=1)
        self.assertIsNotNone(client.trace({}))
        client.close()
        with self.assertRaises(RuntimeError):
            client.trace({})
