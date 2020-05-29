# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#
import json
import logging
import sys

from urllib3 import Retry, poolmanager, util  # type: ignore
from urllib3.exceptions import HTTPError, MaxRetryError  # type: ignore
from urllib3.util import Timeout

from .compat_model import Batch, Signal, Trace
from .exceptions import (AuthenticationFailed, DataIngestionFailed,
                         UnexpectedStatusCode)
from .utils import CustomJSONEncoder, reencode_payload

if sys.version_info[0] >= 3:
    from urllib import parse as urlparse
else:
    import urlparse

if sys.version_info >= (3, 5):
    from typing import Any, Mapping, Optional, Union, Type

    from .compat_model import AnySignal


LOGGER = logging.getLogger(__name__)


class BaseSender(object):
    """Base sender for the Sqreen Ingestion service.

    :param base_url: (optional) URL of the Ingestion service.
    :param proxy_url: (optional) URL of a Proxy server.
    :param headers: (optional) Headers to send with all requests.
    :param json_encoder: (optional) JSON serializer for data to be sent.
    """

    default_base_url = "https://ingestion.sqreen.com/"  # type: str
    default_json_encoder = CustomJSONEncoder

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
        try:
            return json.dumps(
                data, separators=(",", ":"), cls=self.json_encoder)
        except UnicodeDecodeError:
            reencoded_data = reencode_payload(data)
            return json.dumps(
                reencoded_data, separators=(",", ":"), cls=self.json_encoder)

    def handle_response(self, response):
        if response.status not in (200, 202):
            if response.status == 422:
                raise DataIngestionFailed
            elif response.status in (401, 403):
                raise AuthenticationFailed
            raise UnexpectedStatusCode(response.status)
        # ignore the response content for now

    def close(self):  # type: () -> None
        raise NotImplementedError


class SyncSender(BaseSender):
    """
    Sender based on urllib3 for the Ingestion service.

    :param base_url: (optional) URL of the Ingestion service.
    :param proxy_url: (optional) URL of a Proxy server.
    :param headers: (optional) Headers to send with all requests.
    :param json_encoder: (optional) JSON serializer for data to be sent.
    """

    max_pool_size = 10
    retry_policy = Retry(
        total=3,
        method_whitelist=False,
        status_forcelist={500, 502, 503, 504, 408},
        raise_on_status=True,
    )
    timeout_policy = Timeout(connect=10, read=10)

    def __init__(self, base_url=None, proxy_url=None, headers={}, json_encoder=None):
        # type: (Optional[str], Optional[str], Mapping[str, str], Optional[Type[json.JSONEncoder]]) -> None
        base_headers = util.make_headers(keep_alive=True, accept_encoding=True)
        base_headers.update(headers)
        super(SyncSender, self).__init__(
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
        url = self._url(endpoint)
        try:
            response = self.pool_manager.urlopen(
                "POST",
                url,
                body=body,
                headers=request_headers,
                preload_content=True,
                release_conn=True,
                redirect=False,
                retries=self.retry_policy,
                timeout=self.timeout_policy,
                **kwargs
            )
        except (MaxRetryError, HTTPError) as exc:
            LOGGER.info(
                "Couldn't connect to %s due to exception %s", url, type(exc).__name__
            )
        else:
            return self.handle_response(response)

    def close(self):  # type: () -> None
        self.pool_manager.clear()
        del self.pool_manager


Sender = SyncSender
