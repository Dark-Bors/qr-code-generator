# certificate_utils.py
"""
Certificate utility functions for Fetch Production Data (FPD)
Author: Boris Eldar
Version: v4.3.0
"""

import os
import hashlib
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


# ─────────────────────────────────────────────
# Normalize PEM
# ─────────────────────────────────────────────
def normalize_pem_string(pem_str: str) -> bytes:
    """Normalize PEM format from JSON/SAP strings to clean bytes."""
    if not pem_str:
        return b""

    # Convert \n escapes if needed
    if "\\n" in pem_str:
        pem_str = pem_str.encode("utf-8").decode("unicode_escape")

    pem_bytes = pem_str.replace("\r\n", "\n").replace("\r", "\n").encode("ascii")

    # Ensure newline at end
    if not pem_bytes.endswith(b"\n"):
        pem_bytes += b"\n"

    return pem_bytes


# ─────────────────────────────────────────────
# Verify PEM Pair
# ─────────────────────────────────────────────
def verify_cert_pair(cert_pem: str | bytes, key_pem: str | bytes) -> bool:
    """Verify that certificate and private key match."""
    try:
        if isinstance(cert_pem, str):
            cert_pem = normalize_pem_string(cert_pem)
        if isinstance(key_pem, str):
            key_pem = normalize_pem_string(key_pem)

        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        private_key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())

        cert_pub = cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_pub = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return cert_pub == key_pub
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


# ─────────────────────────────────────────────
# Save PEM files
# ─────────────────────────────────────────────
def save_cert_files(sap_data: dict, output_dir: str) -> dict:
    """
    Save AUTH_PUBLIC_KEY / AUTH_PRIVATE_KEY as PEMs directly under output_dir.
    Returns a dict with paths and fingerprints.
    """
    os.makedirs(output_dir, exist_ok=True)
    cert_path = os.path.join(output_dir, "IoTCore_certificate_final.pem.crt")
    key_path = os.path.join(output_dir, "private_final.pem.key")

    cert_pem = normalize_pem_string(sap_data.get("AUTH_PUBLIC_KEY", ""))
    key_pem = normalize_pem_string(sap_data.get("AUTH_PRIVATE_KEY", ""))

    with open(cert_path, "wb") as f:
        f.write(cert_pem)
    with open(key_path, "wb") as f:
        f.write(key_pem)

    cert_fp = hashlib.sha256(cert_pem).hexdigest()
    key_fp = hashlib.sha256(key_pem).hexdigest()

    print(f"📁 Certificate saved: {cert_path}")
    print(f"📁 Private key saved: {key_path}")
    print(f"🔍 Certificate SHA256: {cert_fp}")
    print(f"🔍 Key SHA256: {key_fp}")

    return {"cert": cert_path, "key": key_path, "cert_fp": cert_fp, "key_fp": key_fp}
