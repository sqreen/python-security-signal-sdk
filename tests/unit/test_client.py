import unittest

from sqreen_security_signal_sdk.client import Client
from sqreen_security_signal_sdk.sender import BaseSender


class FakeSender(BaseSender):

    def __init__(self, *args, **kwargs):
        super(FakeSender, self).__init__(*args, **kwargs)
        self.sent_data = []

    def send(self, endpoint, data, headers={}, **kwargs):
        if hasattr(self, "closed"):
            raise RuntimeError
        self.sent_data.append(data)

    def close(self, **kwargs):
        self.closed = True


class FakeClient(Client):

    sender_class = FakeSender


class ClientTestCase(unittest.TestCase):

    def test_metric(self):
        client = FakeClient(token="42", app_name="test", max_batch_size=1)
        client.metric(signal_name="test", payload={})
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["type"], "metric")

        client = FakeClient(token="42", app_name="test", max_batch_size=1)
        client.metric(signal_name="test", payload={}, actor="hello")
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["actor"], "hello")

        self.assertEqual(client.sender.headers["X-Api-Token"], "42")
        self.assertEqual(client.sender.headers["X-App-Name"], "test")
        self.assertNotIn("X-Session-Key", client.sender.headers)

    def test_point(self):
        client = FakeClient(token="42", session_token=True, max_batch_size=1)
        client.point(signal_name="test", payload={})
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["type"], "point")

        client = FakeClient(token="42", session_token=True, max_batch_size=1)
        client.point(signal_name="test", payload={}, actor="hello")
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["actor"], "hello")

        self.assertEqual(client.sender.headers["X-Session-Key"], "42")
        self.assertNotIn("X-App-Name", client.sender.headers)
        self.assertNotIn("X-Api-Token", client.sender.headers)

    def test_trace(self):
        client = FakeClient(token="42", max_batch_size=1)
        client.trace({})
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["data"], {})

        client = FakeClient(token="42", max_batch_size=1)
        client.trace(data={}, actor="hello")
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["actor"], "hello")

    def test_flush(self):
        client = FakeClient(token="42", max_batch_size=2)
        client.flush()
        client.trace({})
        client.flush()
        client.close()
        self.assertEqual(len(client.sender.sent_data), 1)
        self.assertEqual(client.sender.sent_data[0][0]["data"], {})

    def test_close(self):
        client = FakeClient(token="42", max_batch_size=1)
        client.trace({})
        client.close()
        with self.assertRaises(RuntimeError):
            client.trace({})
