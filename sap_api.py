# ─────────────────────────────────────────────────────────────
# sap_api.py — Fetch Production Data (FPD) v4.1.0
# Author: Boris Eldar
# Description:
#   Handles SAP endpoint requests for device credentials and certificates.
#   Compatible with both Python and compiled EXE execution.
# ─────────────────────────────────────────────────────────────

from __future__ import annotations
import requests
import yaml
import sys
import json
from typing import Dict, Any
from pathlib import Path

# ───────────── Detect config.yaml path
if getattr(sys, "frozen", False):
    # Running as compiled EXE
    base_path = Path(sys.executable).parent
else:
    base_path = Path(__file__).resolve().parent

CONFIG_PATH = base_path / "config.yaml"
print(f"[SAP] Loading config from: {CONFIG_PATH}")

# ───────────── Load YAML config
def _load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[SAP] ⚠️ Failed to load config.yaml: {e}")
        return {}

_cfg = _load_config().get("sap", {})

DEFAULT_ENDPOINT = _cfg.get(
    "endpoint",
    "https://tlvm7aapps032.cfrf.medtronic.com/sap/bc/zws_g_get_sn?sap-client=300&SN={sn}",
)
VERIFY_ARG = bool(_cfg.get("verifyTLS", False))
DEFAULT_TIMEOUT = int(_cfg.get("timeout", 10))


# ───────────── Exceptions
class SAPError(RuntimeError):
    pass


# ───────────── Core Request Logic
def _get_json(sn: str, endpoint_template: str, timeout: int) -> Dict[str, Any]:
    if not sn or not str(sn).strip():
        raise ValueError("SN required.")

    url = endpoint_template.format(sn=str(sn).strip())
    print(f"[SAP] Fetching → {url}")

    try:
        r = requests.get(url, verify=VERIFY_ARG, timeout=timeout)
        r.raise_for_status()

        try:
            data = r.json()
        except json.JSONDecodeError:
            raise SAPError("SAP returned non-JSON data (HTML or empty).")

        arr = data.get("SN")
        if not isinstance(arr, list) or not arr or not isinstance(arr[0], dict):
            raise SAPError("Unexpected SAP response format.")
        return arr[0]

    except Exception as e:
        print(f"[SAP] ⚠️ Request failed: {e}")
        raise SAPError(str(e))


# ───────────── Unified Fetch Function
def fetch_certs(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, str]:
    """
    Fetches all certificate- and key-related fields for the device SN.
    Returns a merged dictionary (AUTH_PUBLIC_KEY, AUTH_PRIVATE_KEY,
    BLE_ID, PATIENT_BLE_PWD, etc.).
    """
    try:
        rec = _get_json(sn, endpoint_template, timeout)
        wanted = (
            "AUTH_PUBLIC_KEY",
            "AUTH_PRIVATE_KEY",
            "BLE_ID",
            "PKEY",
            "MKEY",
            "PATIENT_BLE_PWD",
        )
        data = {k: str(rec[k]).strip() for k in wanted if k in rec and rec[k]}
        if not data:
            raise SAPError("Missing certificate or key fields in SAP response.")
        return data

    except SAPError as e:
        print(f"[SAP] ⚠️ {e}")
        # Optional: Offline fallback for testing
        print("[SAP] Using fallback mock data for offline mode.")
        return {
            "BLE_ID": "ABCDEFGHIJ",
            "PATIENT_BLE_PWD": "ABCDEFGHIJ",
            "PKEY": "2FDIU7I6KPZX4H9QOS6EQLDJGHD2UT5HX0E8BEKM0BKWIAX3DT",
            "MKEY": "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=",
            "AUTH_PUBLIC_KEY": "-----BEGIN CERTIFICATE-----\nMIIDWTCCAkGgAwIBAgIUXXAkRUu...snipped...\n-----END CERTIFICATE-----\n",
            "AUTH_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAtzUnG...snipped...\n-----END RSA PRIVATE KEY-----\n",
        }


# ───────────── Legacy compatibility
def fetch_keys(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, str]:
    """Legacy function kept for backward compatibility."""
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("BLE_ID", "PKEY", "MKEY", "PATIENT_BLE_PWD")
    return {k: str(rec[k]).strip() for k in wanted if k in rec and rec[k]}


def fetch_device_data(sn: str) -> Dict[str, str]:
    """Wrapper for GUI compatibility."""
    return fetch_certs(sn)
