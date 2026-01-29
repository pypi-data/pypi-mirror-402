import hmac
import hashlib
import binascii

from authlib.oauth1.rfc5849.signature import generate_signature_base_string
from authlib.oauth1.rfc5849.util import escape
from authlib.common.encoding import to_bytes, to_unicode

__all__ = ["SIGNATURE_HMAC_SHA256"]

SIGNATURE_HMAC_SHA256 = "HMAC-SHA256"


def hmac_sha256_signature(base_string, client_secret, token_secret):
    """Generate signature via HMAC-SHA256, modeled after Authlib's HMAC-SHA1 function."""

    # Build signing key: encode(secret1) + "&" + encode(secret2)
    key = escape(client_secret or "") + "&" + escape(token_secret or "")

    # Compute HMAC-SHA256 digest
    signature = hmac.new(
        to_bytes(key),
        to_bytes(base_string),
        hashlib.sha256,
    )

    # Base64 encode
    sig = binascii.b2a_base64(signature.digest())[:-1]  # strip trailing newline
    return to_unicode(sig)


def sign_hmac_sha256(client, request):
    """Sign a HMAC-SHA256 signature."""
    base_string = generate_signature_base_string(request)
    return hmac_sha256_signature(base_string, client.client_secret, client.token_secret)
