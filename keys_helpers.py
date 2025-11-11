# keys_helpers.py
"""
Key conversion and saving utilities for Fetch Production Data (FPD).

Responsibilities:
- Derive BLE_ID and PATIENT_BLE_PWD via PBKDF2-HMAC-SHA256.
- Use converters.py for all Base36/Base64 transformations.
- Save .bin files with consistent naming and correct endianness.
"""

from __future__ import annotations
import os
import hashlib
from typing import Dict

# ─────────────────────────────────────────────
# Imports from converters.py (the single source of truth)
# ─────────────────────────────────────────────
from converters import (
    pkey_base36_to_bytes32,
    bytes32_to_pkey_base36,
    mkey_base64_to_bytes32,
    bytes32_to_base64,
)

# ─────────────────────────────────────────────
# Constants for PBKDF2
# ─────────────────────────────────────────────
PBKDF2_ITERS = 310_000
PBKDF2_SALT_HEX = "C30AF78E2C3EE53B5D52E2FD93B3513A"


# ─────────────────────────────────────────────
# PBKDF2 Helpers (unchanged)
# ─────────────────────────────────────────────
def derive_key_bytes(password: str) -> bytes:
    """PBKDF2-HMAC-SHA256(password, fixed salt/iters, dklen=32) → 32 raw bytes."""
    salt = bytes.fromhex(PBKDF2_SALT_HEX)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS, dklen=32)


def derive_key_hex(password: str) -> str:
    """Return derived PBKDF2 bytes as uppercase hex string."""
    return derive_key_bytes(password).hex().upper()


# ─────────────────────────────────────────────
# File Write Helpers
# ─────────────────────────────────────────────
def save_key_bin(path: str, data: bytes):
    """Save raw key bytes to a .bin file."""
    with open(path, "wb") as f:
        f.write(data)


# ─────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────
def save_all_keys(
    output_dir: str,
    sn: str,
    pkey_base36: str,
    mkey_b64: str,
    ble_id: str,
    patient_ble_pwd: str,
) -> Dict[str, str]:
    """
    Converts and saves all key files in the selected folder.
    - key1_PKEY_<SN>.bin
    - key2_MKEY_<SN>.bin
    - key3_BLE_ID_<SN>.bin
    - key4_PATIENT_BLE_PWD_<SN>.bin
    - keys_2_3_4_<SN>.bin (concatenated)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Convert using the trusted converters.py
    key1 = pkey_base36_to_bytes32(pkey_base36)
    key2 = mkey_base64_to_bytes32(mkey_b64)
    key3 = derive_key_bytes(ble_id)
    key4 = derive_key_bytes(patient_ble_pwd)

    combined = key2 + key3 + key4

    paths = {
        "key1": os.path.join(output_dir, f"key1_PKEY_{sn}.bin"),
        "key2": os.path.join(output_dir, f"key2_MKEY_{sn}.bin"),
        "key3": os.path.join(output_dir, f"key3_BLE_ID_{sn}.bin"),
        "key4": os.path.join(output_dir, f"key4_PATIENT_BLE_PWD_{sn}.bin"),
        "combo": os.path.join(output_dir, f"keys_2_3_4_{sn}.bin"),
    }

    # Write all files
    save_key_bin(paths["key1"], key1)
    save_key_bin(paths["key2"], key2)
    save_key_bin(paths["key3"], key3)
    save_key_bin(paths["key4"], key4)
    save_key_bin(paths["combo"], combined)

    return paths


# ─────────────────────────────────────────────
# Debug / Standalone Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    sn = "253000391"
    out = "./_test_keys"
    os.makedirs(out, exist_ok=True)

    paths = save_all_keys(
        out,
        sn,
        pkey_base36="2FDIU7I6KPZX4H9QOS6EQLDJGHD2UT5HX0E8BEKM0BKWIAX3DT",
        mkey_b64="YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=",
        ble_id="ABCDEFGHIJ",
        patient_ble_pwd="ABCDEFGHIJ",
    )

    for k, v in paths.items():
        print(f"{k}: {v}")
