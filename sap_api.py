# sap_api.py

from __future__ import annotations
import requests
import yaml
import sys
from typing import Dict, Any
from pathlib import Path

# Detect correct config path for both script and EXE builds
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    base_path = Path(sys.executable).parent
else:
    # Running as regular .py
    base_path = Path(__file__).resolve().parent

CONFIG_PATH = base_path / "config.yaml"
print(f"[SAP] Loading config from: {CONFIG_PATH}")  # for Debugging



def _load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_cfg = _load_config().get("sap", {})

DEFAULT_ENDPOINT = _cfg.get(
    "endpoint",
    "https://tlvm7aapps032.cfrf.medtronic.com/sap/bc/zws_g_get_sn?sap-client=300&SN={sn}"
)
VERIFY_ARG = bool(_cfg.get("verifyTLS", False))
DEFAULT_TIMEOUT = int(_cfg.get("timeout", 10))

# ----------------------------------------------------------------------
# Core logic
# ----------------------------------------------------------------------
class SAPError(RuntimeError):
    pass


def _get_json(sn: str, endpoint_template: str, timeout: int) -> Dict[str, Any]:
    if not sn or not str(sn).strip():
        raise ValueError("SN required.")
    url = endpoint_template.format(sn=str(sn).strip())
    r = requests.get(url, verify=VERIFY_ARG, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    arr = data.get("SN")
    if not isinstance(arr, list) or not arr or not isinstance(arr[0], dict):
        raise SAPError("Unexpected SAP response format.")
    return arr[0]


def fetch_keys(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, str]:
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("BLE_ID", "PKEY", "MKEY", "PATIENT_BLE_PWD")
    missing = [k for k in wanted if k not in rec]
    if missing:
        raise SAPError(f"Missing fields in SAP response: {missing}")
    return {k: str(rec[k]).strip() for k in wanted}


def fetch_certs(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, str]:
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("AUTH_PUBLIC_KEY", "AUTH_PRIVATE_KEY")
    missing = [k for k in wanted if k not in rec]
    if missing:
        raise SAPError(f"Missing certificate fields: {missing}")
    return {k: str(rec[k]) for k in wanted}
