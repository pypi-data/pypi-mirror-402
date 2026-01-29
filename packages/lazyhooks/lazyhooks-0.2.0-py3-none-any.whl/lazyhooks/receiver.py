import hmac
import hashlib
import time

def verify_signature(payload_body: bytes, signature_header: str, secret: str, timestamp_header: str, tolerance: int = 300) -> bool:
    """
    Verifies that the signature header matches the HMAC-SHA256 of the payload body + timestamp.
    Also checks if the timestamp is within the tolerance window (default 5 minutes).
    
    :param payload_body: The raw bytes of the request body.
    :param signature_header: The value of 'X-Lh-Signature' (e.g., 'v1=...')
    :param secret: The shared secret key.
    :param timestamp_header: The value of 'X-Lh-Timestamp'.
    :param tolerance: Maximum age of the request in seconds.
    :return: True if valid, False otherwise.
    """
    if not signature_header or not timestamp_header:
        return False

    # 1. Verify Timestamp Freshness
    try:
        timestamp = int(timestamp_header)
    except ValueError:
        return False

    now = int(time.time())
    if now - timestamp > tolerance:
        return False # Too old (Replay Attack?)

    # 2. Verify Signature
    # reconstruct: "timestamp.body"
    if not signature_header.startswith("v1="):
        return False
        
    to_sign = f"{timestamp}.".encode() + payload_body
    
    expected_sig = hmac.new(
        secret.encode(),
        to_sign,
        hashlib.sha256
    ).hexdigest()

    incoming_sig = signature_header.split("v1=")[1]
    
    return hmac.compare_digest(expected_sig, incoming_sig)
