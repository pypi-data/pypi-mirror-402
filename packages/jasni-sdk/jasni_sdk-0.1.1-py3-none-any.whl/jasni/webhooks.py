"""
Webhook Utilities

Utilities for verifying webhook signatures and handling webhook payloads.
"""

import hashlib
import hmac
import time
from typing import Union


def verify_signature(
    payload: Union[str, bytes],
    signature: str,
    secret: str,
    tolerance: int = 300
) -> bool:
    """
    Verify a webhook signature.
    
    Jasni signs webhook payloads using HMAC-SHA256. The signature header
    contains a timestamp and signature in the format: "t=timestamp,v1=signature"
    
    Args:
        payload: The raw request body (string or bytes)
        signature: The X-Jasni-Signature header value
        secret: Your webhook secret (from webhook creation)
        tolerance: Maximum age of the signature in seconds. Default: 300 (5 minutes)
    
    Returns:
        True if the signature is valid, False otherwise
    
    Example:
        >>> from jasni.webhooks import verify_signature
        >>>
        >>> def handle_webhook(request):
        ...     payload = request.body
        ...     signature = request.headers.get("X-Jasni-Signature")
        ...
        ...     if verify_signature(payload, signature, webhook_secret):
        ...         # Process the webhook
        ...         data = json.loads(payload)
        ...         print(f"Received event: {data['event']}")
        ...     else:
        ...         return "Invalid signature", 401
    
    Note:
        The tolerance parameter helps protect against replay attacks by
        rejecting signatures that are too old.
    """
    if not signature:
        return False
    
    # Parse the signature header
    parts = {}
    for item in signature.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key] = value
    
    timestamp_str = parts.get("t")
    signature_hash = parts.get("v1")
    
    if not timestamp_str or not signature_hash:
        return False
    
    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return False
    
    # Check timestamp tolerance (protect against replay attacks)
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance:
        return False
    
    # Prepare payload
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload
    
    # Create the signed payload string: "timestamp.payload"
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using constant-time comparison
    return hmac.compare_digest(expected_signature, signature_hash)


def construct_event(
    payload: Union[str, bytes],
    signature: str,
    secret: str,
    tolerance: int = 300
) -> dict:
    """
    Construct and verify a webhook event.
    
    This is a convenience function that verifies the signature and
    returns the parsed payload as a dictionary.
    
    Args:
        payload: The raw request body (string or bytes)
        signature: The X-Jasni-Signature header value
        secret: Your webhook secret
        tolerance: Maximum age of the signature in seconds. Default: 300
    
    Returns:
        The parsed webhook event as a dictionary
    
    Raises:
        ValueError: If the signature is invalid or expired
    
    Example:
        >>> from jasni.webhooks import construct_event
        >>>
        >>> try:
        ...     event = construct_event(
        ...         payload=request.body,
        ...         signature=request.headers.get("X-Jasni-Signature"),
        ...         secret=webhook_secret
        ...     )
        ...     
        ...     if event["event"] == "email.received":
        ...         handle_new_email(event["data"])
        ... except ValueError as e:
        ...     print(f"Invalid webhook: {e}")
        ...     return "Invalid signature", 401
    """
    import json
    
    if not verify_signature(payload, signature, secret, tolerance):
        raise ValueError("Invalid webhook signature")
    
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    
    return json.loads(payload)


def generate_signature(
    payload: Union[str, bytes],
    secret: str,
    timestamp: int = None
) -> str:
    """
    Generate a webhook signature (for testing purposes).
    
    This function generates a valid signature for a given payload,
    which is useful for testing your webhook handlers.
    
    Args:
        payload: The payload to sign
        secret: The webhook secret
        timestamp: Unix timestamp. Uses current time if not provided.
    
    Returns:
        The signature string in the format "t=timestamp,v1=signature"
    
    Example:
        >>> from jasni.webhooks import generate_signature
        >>>
        >>> payload = '{"event": "email.received", "data": {}}'
        >>> signature = generate_signature(payload, "whsec_test_secret")
        >>> print(signature)
        't=1234567890,v1=abc123...'
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload
    
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    
    signature_hash = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature_hash}"
