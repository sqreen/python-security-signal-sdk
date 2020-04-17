import random
import sys
import threading
import time
import unittest

from sqreen_security_signal_sdk.exceptions import (AuthenticationFailed,
                                                   DataIngestionFailed,
                                                   UnexpectedStatusCode)
from sqreen_security_signal_sdk.sender import BlockingSender

if sys.version_info[0] >= 3:
    from http import server
else:
    import BaseHTTPServer as server


class FakeIngestionHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        assert "X-Test-Client" in self.headers
        assert "X-Test-Request" in self.headers
        assert self.headers.get("Content-Type") == "application/json"
        self.send_response(202)
        self.send_header("Connection", "close")
        self.send_header("Content-Length", "2")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")


class AuthenticationFailedHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_error(401)
        self.end_headers()


class DataIngestionFailedHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_error(422)
        self.end_headers()


class UnexpectedFailureHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_error(506)
        self.end_headers()


class RetryFailureHandler(server.BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_error(500)
        self.end_headers()


class FakeProxyHandler(FakeIngestionHandler):

    def do_POST(self):
        assert self.path == "http://ingestion.sqreen.com/traces"
        assert self.headers.get("Host") == "ingestion.sqreen.com"
        return FakeIngestionHandler.do_POST(self)


class BlockingSenderTestCase(unittest.TestCase):

    def setUp(self):
        self.fake_server = None
        self.fake_server_thread = threading.Thread(target=self.run_fake_server)
        self.fake_server_thread.start()
        # Wait for the server to be ready
        while getattr(self.fake_server, "fileno", None) is None:
            time.sleep(0.1)

    def tearDown(self):
        self.fake_server.shutdown()
        self.fake_server_thread.join()
        self.fake_server = None

    def run_fake_server(self):
        port = random.randint(25252, 32323)
        self.fake_server = server.HTTPServer(
            ("localhost", port), FakeIngestionHandler)
        self.fake_server_url = "http://localhost:{}/".format(port)
        self.fake_server.serve_forever()

    def test_send(self):
        s = BlockingSender(base_url=self.fake_server_url,
                           headers={"X-Test-Client": "hello"})
        ret = s.send_trace({"data": {}}, headers={"X-Test-Request": "world"})
        self.assertIsNone(ret)
        ret = s.send_signal({"signal_name": "test", "payload": {}},
                            headers={"X-Test-Request": "world"})
        self.assertIsNone(ret)

    def test_send_auth_failed(self):
        self.fake_server.RequestHandlerClass = AuthenticationFailedHandler
        s = BlockingSender(base_url=self.fake_server_url)
        with self.assertRaises(AuthenticationFailed):
            s.send("/traces", {"data": {}})

    def test_send_data_ingestion_failed(self):
        self.fake_server.RequestHandlerClass = DataIngestionFailedHandler
        s = BlockingSender(base_url=self.fake_server_url)
        with self.assertRaises(DataIngestionFailed):
            s.send("/traces", {"data": {}})

    def test_send_unexpected_status(self):
        self.fake_server.RequestHandlerClass = UnexpectedFailureHandler
        s = BlockingSender(base_url=self.fake_server_url)
        with self.assertRaises(UnexpectedStatusCode):
            s.send("/traces", {"data": {}})

    def test_send_retry(self):
        self.fake_server.RequestHandlerClass = RetryFailureHandler
        s = BlockingSender(base_url=self.fake_server_url)
        s.send("/traces", {"data": {}})

    def test_close(self):
        s = BlockingSender(base_url=self.fake_server_url)
        s.close()
        with self.assertRaises(Exception):
            s.send("/traces", {"data": {}})

    def test_proxy(self):
        self.fake_server.RequestHandlerClass = FakeProxyHandler
        s = BlockingSender(proxy_url=self.fake_server_url,
                           base_url="http://ingestion.sqreen.com/",
                           headers={"X-Test-Client": "hello"})
        ret = s.send_trace({"data": {}}, headers={"X-Test-Request": "world"})
        self.assertIsNone(ret)
