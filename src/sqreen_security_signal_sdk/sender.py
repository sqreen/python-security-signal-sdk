# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import datetime
import json
import sys

from urllib3 import poolmanager, util  # type: ignore

from .compat_model import Batch, Signal, Trace
from .exceptions import (AuthenticationFailed, DataIngestionFailed,
                         UnexpectedStatusCode)

if sys.version_info[0] >= 3:
    from urllib import parse as urlparse
else:
    import urlparse

if sys.version_info >= (3, 5):
    from typing import Any, Mapping, Optional, Union, Type

    from .compat_model import AnySignal


class SenderJSONEncoder(json.JSONEncoder):

    def default(self, obj):  # type: (Any) -> Optional[str]
        """Return the repr of unknown objects.
        """
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return repr(obj)


class BaseSender(object):
    """Base sender for the Sqreen Ingestion service.

    :param base_url: (optional) URL of the Ingestion service.
    :param proxy_url: (optional) URL of a Proxy server.
    :param headers: (optional) Headers to send with all requests.
    :param json_encoder: (optional) JSON serializer for data to be sent.
    """

    default_base_url = "https://ingestion.sqreen.com/"  # type: str
    default_json_encoder = json.JSONEncoder

    def __init__(self, base_url=None, proxy_url=None, headers={}, json_encoder=None):
        # type: (Optional[str], Optional[str], Mapping[str, str], Optional[Type[json.JSONEncoder]]) -> None
        self.base_url = base_url or self.default_base_url
        self.proxy_url = proxy_url
        self.headers = headers
        self.json_encoder = json_encoder or self.default_json_encoder

    def send_batch(self, data, headers={}, **kwargs):
        # type: (Batch, Mapping[str, str], **Any) -> None
        return self.send("/batches", data, headers=headers, **kwargs)

    def send_signal(self, data, headers={}, **kwargs):
        # type: (Signal, Mapping[str, str], **Any) -> None
        return self.send("/signals", data, headers=headers, **kwargs)

    def send_trace(self, data, headers={}, **kwargs):
        # type: (Trace, Mapping[str, str], **Any) -> None
        return self.send("/traces", data, headers=headers, **kwargs)

    def send(self, endpoint, data, headers={}, **kwargs):
        # type: (str, Union[AnySignal, Batch], Mapping[str, str], **Any) -> None
        raise NotImplementedError

    def serialize_data(self, data):
        # type: (Union[AnySignal, Batch]) -> str
        return json.dumps(data, separators=(",", ":"), cls=self.json_encoder)

    def handle_response(self, response):
        if response.status not in(200, 202):
            if response.status == 422:
                raise DataIngestionFailed
            elif response.status in (401, 403):
                raise AuthenticationFailed
            raise UnexpectedStatusCode(response.status)
        # ignore the response content for now

    def close(self, timeout=None):
        # type: (Optional[float]) -> None
        raise NotImplementedError


class BlockingSender(BaseSender):
    """
    Sender based on urllib3 for the Ingestion service.

    :param base_url: (optional) URL of the Ingestion service.
    :param proxy_url: (optional) URL of a Proxy server.
    :param headers: (optional) Headers to send with all requests.
    :param json_encoder: (optional) JSON serializer for data to be sent.
    """

    max_pool_size = 10

    def __init__(self, base_url=None, proxy_url=None, headers={}, json_encoder=None):
        # type: (Optional[str], Optional[str], Mapping[str, str], Optional[Type[json.JSONEncoder]]) -> None
        base_headers = util.make_headers(keep_alive=True, accept_encoding=True)
        base_headers.update(headers)
        super(BlockingSender, self).__init__(
            base_url=base_url, proxy_url=proxy_url, headers=base_headers,
            json_encoder=json_encoder)

        options = dict(
            block=True,
            maxsize=self.max_pool_size,
        )
        if self.proxy_url is not None:
            self.pool_manager = poolmanager.ProxyManager(self.proxy_url, **options)  # type: poolmanager.PoolManager
        else:
            self.pool_manager = poolmanager.PoolManager(**options)

    def _url(self, endpoint):
        return urlparse.urljoin(self.base_url, endpoint, allow_fragments=False)

    def send(self, endpoint, data, headers={}, **kwargs):
        # type: (str, Union[AnySignal, Batch], Mapping[str, str], **Any) -> None
        assert self.pool_manager is not None
        body = self.serialize_data(data)
        request_headers = dict(self.headers)
        request_headers["Content-Type"] = "application/json"
        request_headers.update(headers)
        response = self.pool_manager.urlopen(
            "POST", self._url(endpoint),
            body=body,
            headers=request_headers,
            preload_content=True,
            release_conn=True,
            redirect=False,
            **kwargs
        )
        return self.handle_response(response)

    def close(self, timeout=None):
        # type: (Optional[float]) -> None
        self.pool_manager.clear()
        del self.pool_manager


Sender = BlockingSender