# utils.py
"""
Utility functions for Fetch Production Data (FPD)
Author : Boris Eldar
Version: 4.3.0
Provides YAML loaders, screenshot capture, and profile helpers.
"""

import os
import yaml
from tkinter import filedialog
from PIL import ImageGrab

# ─────────────────────────────────────────────
# Default Cloud Profiles
# ─────────────────────────────────────────────
_DEFAULT_PROFILES = {
    "newton": {
        "cloudUrl": "a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com",
        "mqttPrefix": "newton/dev/things",
    },
    "davinci": {
        "cloudUrl": "a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com",
        "mqttPrefix": "davinci/dev/things",
    },
    "manual": {"cloudUrl": "", "mqttPrefix": ""},
}


# ─────────────────────────────────────────────
# Load Cloud Profiles from YAML
# ─────────────────────────────────────────────
def load_cloud_profiles(yaml_path: str = "config.yaml"):
    """
    Loads the cloudProfiles and defaultProfile sections from config.yaml.
    Returns (profiles_dict, default_profile_name)
    Falls back to defaults if file or fields missing.
    """
    if not os.path.exists(yaml_path):
        return _DEFAULT_PROFILES, "davinci"

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        profiles = cfg.get("cloudProfiles") or _DEFAULT_PROFILES
        default_key = cfg.get("defaultProfile") or "davinci"

        # Validation
        for k in ("newton", "davinci", "manual"):
            profiles.setdefault(k, _DEFAULT_PROFILES[k])

        return profiles, default_key

    except Exception as e:
        print(f"⚠️ Failed to load cloud profiles: {e}")
        return _DEFAULT_PROFILES, "davinci"


# ─────────────────────────────────────────────
# Load Auto-Fill Section
# ─────────────────────────────────────────────
def load_autofill(yaml_path: str = "config.yaml") -> dict:
    """
    Reads optional 'autofill' section from config.yaml
    Example:
      autofill:
        sn: "259710800"
        patientName: "Test"
        govId: "123456789"
        PKEY: "ABCDEF..."
        MKEY: "XXXX="
        BLE_ID: "ABCDEFGHIJ"
        PATIENT_BLE_PWD: "1234567890"
    """
    if not os.path.exists(yaml_path):
        return {}
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("autofill") or {}
    except Exception as e:
        print(f"⚠️ Failed to read autofill data: {e}")
        return {}


# ─────────────────────────────────────────────
# Recursive Search for SN in YAML
# ─────────────────────────────────────────────
def find_sn_in_yaml(data):
    """
    Search recursively for BLE_ID or LD_Serial_Number fields
    inside arbitrary nested YAML structures.
    """
    if isinstance(data, dict):
        if "BLE_ID" in data:
            return data["BLE_ID"]
        elif "LD_Serial_Number" in data:
            return data["LD_Serial_Number"]
        for _, v in data.items():
            r = find_sn_in_yaml(v)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = find_sn_in_yaml(item)
            if r:
                return r
    return None


# ─────────────────────────────────────────────
# Load YAML File and Extract SN
# ─────────────────────────────────────────────
def load_yaml_sn() -> str | None:
    """
    Opens a file dialog, loads YAML, and extracts SN from BLE_ID or LD_Serial_Number.
    Returns SN string or None if not found.
    """
    file_path = filedialog.askopenfilename(
        title="Select YAML file",
        filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
    )
    if not file_path:
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        sn = find_sn_in_yaml(data)
        if sn:
            return str(sn)
        print("⚠️ SN not found in YAML.")
        return None
    except Exception as e:
        print(f"⚠️ Failed to parse YAML: {e}")
        return None


# ─────────────────────────────────────────────
# Screenshot Capture (Optional)
# ─────────────────────────────────────────────
def save_screenshot(root, default_filename="FPD_Window.png"):
    """
    Captures a screenshot of the current Tkinter window and allows saving it.
    """
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=default_filename,
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )

    if not file_path:
        return

    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(file_path)
    print(f"🖼️ Screenshot saved → {file_path}")
