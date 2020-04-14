# -*- coding: utf-8 -*-
# Copyright (c) 2016 - 2020 Sqreen. All rights reserved.
# Please refer to our terms for more information:
#
#     https://www.sqreen.io/terms.html
#


class AuthenticationFailed(Exception):
    """The authentication token or application name was rejected by the
    Sqreen Ingestion service."""


class DataIngestionFailed(Exception):
    """The recorded data was rejected by the Sqreen Ingestion service."""


class UnexpectedStatusCode(Exception):
    """Unexpected error from the Sqreen Ingestion service."""
