"""Verificación opcional de PIN individual mediante PBKDF2 y comparación constante."""

from __future__ import annotations

import hashlib
import hmac
import secrets

DEFAULT_ITERATIONS = 450_000


def hash_pin(pin: str, *, iterations: int = DEFAULT_ITERATIONS, salt_hex: str | None = None) -> str:
    if len(pin) < 6:
        raise ValueError("Utiliza un PIN de al menos 6 caracteres.")
    salt = bytes.fromhex(salt_hex) if salt_hex is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if not (100_000 <= iterations <= 2_000_000):
            return False
        digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), bytes.fromhex(salt_hex), iterations)
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False
