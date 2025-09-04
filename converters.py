# converters.py
# Key conversions used by the GUI.
# - Key_1 (pkey): Base36 (50) <-> 32 bytes (little-endian)
# - Key_2 (mkey): Base64 <-> 32 bytes
# Text fields use Base64 for any 32-byte value; .bin files store raw 32 bytes.

from __future__ import annotations
import base64, re
from typing import Final

_ALPH: Final[str] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_B36_50 = re.compile(r"^[0-9A-Z]{50}$")

def _b36_to_int(s: str) -> int:
    u = (s or "").strip().upper()
    if not _B36_50.fullmatch(u):
        raise ValueError("pkey must be 50-char Base36 (0-9,A-Z).")
    return int(u, 36)

def pkey_base36_to_bytes32(pkey_b36: str) -> bytes:
    n = _b36_to_int(pkey_b36)
    return n.to_bytes(32, "little")

def bytes32_to_pkey_base36(raw: bytes) -> str:
    if len(raw) != 32: raise ValueError("Need 32 bytes.")
    n = int.from_bytes(raw, "little")
    s = ""
    if n == 0:
        s = "0"
    else:
        while n:
            n, r = divmod(n, 36)
            s = _ALPH[r] + s
    return s.rjust(50, "0")

def mkey_base64_to_bytes32(mkey_b64: str) -> bytes:
    raw = base64.b64decode((mkey_b64 or "").strip())
    if len(raw) != 32:
        raise ValueError(f"mkey Base64 decodes to {len(raw)} bytes; expected 32.")
    return raw

def bytes32_to_base64(raw: bytes) -> str:
    if len(raw) != 32: raise ValueError("Need 32 bytes.")
    return base64.b64encode(raw).decode("utf-8")
