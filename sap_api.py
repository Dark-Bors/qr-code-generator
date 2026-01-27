# ─────────────────────────────────────────────────────────────
# sap_api.py — Fetch Production Data (FPD) v6.0.0
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
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup module-level logger
logger = logging.getLogger(__name__)

# ───────────── Detect config.yaml path
if getattr(sys, "frozen", False):
    # Running as compiled EXE
    base_path = Path(sys.executable).parent
else:
    base_path = Path(__file__).resolve().parent

CONFIG_PATH = base_path / "config.yaml"
logger.info(f"[SAP] Loading config from: {CONFIG_PATH}")

# ───────────── Load YAML config
def _load_config() -> Dict[str, Any]:
    """Load configuration safely."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"[SAP] ⚠️ Failed to load config.yaml: {e}")
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
    """Custom exception for SAP communication errors."""
    pass


# ───────────── Core Request Logic
def _get_json(sn: str, endpoint_template: str, timeout: int) -> Dict[str, Any]:
    """
    Executes the HTTP GET request to SAP and parses JSON response.
    
    Args:
        sn: Serial Number
        endpoint_template: URL template containing {sn}
        timeout: Request timeout in seconds

    Returns:
        JSON dictionary from the response.

    Raises:
        ValueError: If SN is empty.
        SAPError: If request fails or response is invalid.
    """
    if not sn or not str(sn).strip():
        raise ValueError("SN required.")

    clean_sn = str(sn).strip()
    url = endpoint_template.format(sn=clean_sn)
    logger.info(f"[SAP] Fetching → {url}")

    try:
        r = requests.get(url, verify=VERIFY_ARG, timeout=timeout)
        r.raise_for_status()

        try:
            data = r.json()
        except json.JSONDecodeError:
            raise SAPError("SAP returned non-JSON data (HTML or empty).")

        # Parse expected "SN" list wrapper
        arr = data.get("SN")
        if not isinstance(arr, list) or not arr or not isinstance(arr[0], dict):
            # Debug: sometimes SAP might return direct dict? Handle carefully if needed.
            raise SAPError("Unexpected SAP response format (expected 'SN' list).")
        
        return arr[0]

    except requests.exceptions.RequestException as e:
        logger.error(f"[SAP] Network/HTTP Error: {e}")
        raise SAPError(f"Network error: {e}")
    except Exception as e:
        logger.error(f"[SAP] ⚠️ Request failed: {e}")
        raise SAPError(str(e))


# ───────────── Unified Fetch Function
def fetch_certs(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, str]:
    """
    Fetches all certificate- and key-related fields for the device SN.
    
    Returns a merged dictionary containing keys like:
    AUTH_PUBLIC_KEY, AUTH_PRIVATE_KEY, BLE_ID, PKEY, MKEY, PATIENT_BLE_PWD.
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
        logger.warning(f"[SAP] ⚠️ {e}")
        # Optional: Offline fallback for testing
        # To disable fallback in prod, remove this block or use a flag.
        logger.warning("[SAP] Using fallback mock data for offline mode.")
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
    """
    Legacy function kept for backward compatibility.
    Fetches only key-related fields.
    """
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("BLE_ID", "PKEY", "MKEY", "PATIENT_BLE_PWD")
    return {k: str(rec[k]).strip() for k in wanted if k in rec and rec[k]}


def fetch_device_data(sn: str) -> Dict[str, str]:
    """Wrapper for GUI compatibility."""
    return fetch_certs(sn)

