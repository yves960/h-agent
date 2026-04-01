"""
h_agent/bridge/jwt_utils.py - JWT Authentication for Bridge

Provides JWT-based authentication for secure bridge communication.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional


class JWTAuth:
    """
    Simple JWT-like auth for bridge communication.

    Not a full JWT implementation - just enough for local bridge security.
    Uses HS256-like signature with a shared secret.
    """

    def __init__(self, secret: str = "h-agent-bridge-secret"):
        self.secret = secret.encode()

    def create_token(self, payload: dict, expires_in: int = 3600) -> str:
        """
        Create a simple signed token.

        Args:
            payload: Data to encode
            expires_in: Token lifetime in seconds

        Returns:
            Base64-encoded signed token
        """
        import base64

        header = {"alg": "HS256", "typ": "JWT"}
        payload["exp"] = int(time.time()) + expires_in

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        signature = hmac.new(
            self.secret,
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a token.

        Args:
            token: The token to verify

        Returns:
            Decoded payload if valid, None if invalid/expired
        """
        import base64

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header_b64, payload_b64, sig_b64 = parts

            # Verify signature
            expected_sig = hmac.new(
                self.secret,
                f"{header_b64}.{payload_b64}".encode(),
                hashlib.sha256
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

            if not hmac.compare_digest(sig_b64, expected_sig_b64):
                return None

            # Decode payload
            # Add padding back
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload = json.loads(base64.urlsafe_b64decode(payload_b64))

            # Check expiration
            if payload.get("exp", 0) < int(time.time()):
                return None

            return payload

        except Exception:
            return None
