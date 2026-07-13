"""
Password hashing for admin logins, using PBKDF2-HMAC-SHA256 from Python's
standard library (hashlib) — no extra dependency needed, and unlike a
plain hash this is deliberately slow (100k iterations) to resist brute
force / rainbow tables. A random salt is generated per password and
stored alongside the hash as "salt$hash" (both hex-encoded).
"""

import hashlib
import hmac
import os

_ITERATIONS = 100_000


def hash_password(plain_password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt_hex, derived_hex = stored_hash.split("$", 1)
    except ValueError:
        return False  # malformed hash

    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(derived_hex)
    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _ITERATIONS)
    return hmac.compare_digest(actual, expected)
