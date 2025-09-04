# sap_api.py
from __future__ import annotations
import requests
from typing import Dict, Any

DEFAULT_ENDPOINT = (
    "https://tlvm7aappd040.cfrf.medtronic.com/sap/bc/zws_g_get_sn?sap-client=300&SN={sn}"
)

# TLS verification explicitly disabled per request.
VERIFY_ARG = False

class SAPError(RuntimeError):
    pass

def _get_json(sn: str, endpoint_template: str, timeout: int) -> Dict[str, Any]:
    if not sn or not str(sn).strip():
        raise ValueError("SN required.")
    url = endpoint_template.format(sn=str(sn).strip())
    # Do NOT verify TLS (user requested to skip checking their Root CA)
    r = requests.get(url, verify=VERIFY_ARG, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    arr = data.get("SN")
    if not isinstance(arr, list) or not arr or not isinstance(arr[0], dict):
        raise SAPError("Unexpected SAP response format.")
    return arr[0]

def fetch_keys(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = 10) -> Dict[str, str]:
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("BLE_ID", "PKEY", "MKEY", "PATIENT_BLE_PWD")
    missing = [k for k in wanted if k not in rec]
    if missing:
        raise SAPError(f"Missing fields in SAP response: {missing}")
    return {k: str(rec[k]).strip() for k in wanted}

def fetch_certs(sn: str, endpoint_template: str = DEFAULT_ENDPOINT, timeout: int = 10) -> Dict[str, str]:
    rec = _get_json(sn, endpoint_template, timeout)
    wanted = ("AUTH_PUBLIC_KEY", "AUTH_PRIVATE_KEY")
    missing = [k for k in wanted if k not in rec]
    if missing:
        raise SAPError(f"Missing certificate fields: {missing}")
    return {k: str(rec[k]) for k in wanted}
