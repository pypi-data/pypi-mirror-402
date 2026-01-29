from netsuite_async.catalog import RecordCatalog
from netsuite_async.client import (
    AsyncAuthProvider,
    AsyncNetsuiteRestClient,
    OAuth1AsyncAuthProvider,
    OAuth1Credentials,
    async_oauth1_client,
    GetParams,
    UpdateParams,
    CreateParams
)
from netsuite_async.exceptions import (
    NetsuiteAuthError,
    NetsuiteClientException,
    NetsuiteError,
    NetsuiteRateLimitError,
    NetsuiteRequestError,
    NetsuiteResponseError,
    NetsuiteServerError,
    NetsuiteValidationError,
)


__all__ = [
    "RecordCatalog",
    "AsyncNetsuiteRestClient",
    "async_oauth1_client",
    "OAuth1Credentials",
    "AsyncAuthProvider",
    "OAuth1AsyncAuthProvider",
    "NetsuiteError",
    "NetsuiteRequestError",
    "NetsuiteValidationError",
    "NetsuiteAuthError",
    "NetsuiteRateLimitError",
    "NetsuiteServerError",
    "NetsuiteResponseError",
    "NetsuiteClientException",
    "GetParams",
    "UpdateParams",
    "CreateParams",
]


def register_signature_method():
    """
    NetSuite’s REST API's OAuth1  with HMAC-SHA256 signatures.

    Authlib only includes HMAC-SHA1 out of the box, so we must register
    a custom signature method at import time for clients using
    OAuth1AsyncAuthProvider or async_oauth1_client().

    This must run before any OAuth1 requests are made.
    """
    from authlib.oauth1 import ClientAuth
    from netsuite_async.signature import SIGNATURE_HMAC_SHA256, sign_hmac_sha256

    if SIGNATURE_HMAC_SHA256 not in ClientAuth.SIGNATURE_METHODS:
        ClientAuth.register_signature_method(SIGNATURE_HMAC_SHA256, sign_hmac_sha256)


register_signature_method()
