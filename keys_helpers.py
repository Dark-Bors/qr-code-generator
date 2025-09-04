# keys_helpers.py
# PBKDF2 derivation for Key_3 / Key_4 and small glue helpers.

from __future__ import annotations
import hashlib
from typing import Tuple

PBKDF2_ITERS = 310_000
PBKDF2_SALT_HEX = "C30AF78E2C3EE53B5D52E2FD93B3513A"

def derive_key_bytes(password: str) -> bytes:
    """PBKDF2-HMAC-SHA256(password, fixed salt/iters, dklen=32) -> raw 32 bytes."""
    salt = bytes.fromhex(PBKDF2_SALT_HEX)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS, dklen=32)

def derive_key_hex(password: str) -> str:
    return derive_key_bytes(password).hex()
