import hmac
import hashlib

def verify_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Verifies that the signature header matches the HMAC-SHA256 of the payload body.
    
    :param payload_body: The raw bytes of the request body.
    :param signature_header: The value of the X-Hub-Signature-256 header (e.g., 'sha256=...')
    :param secret: The shared secret key.
    :return: True if valid, False otherwise.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_sig = hmac.new(
        secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    incoming_sig = signature_header.split("=")[1]
    
    return hmac.compare_digest(expected_sig, incoming_sig)
