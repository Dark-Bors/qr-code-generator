import yaml
import time
import os
from tkinter import filedialog
from PIL import ImageGrab

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

def load_cloud_profiles(yaml_path: str = "config.yaml"):
    """Return (profiles:dict, default_key:str). Falls back to sensible defaults."""
    if not os.path.exists(yaml_path):
        return _DEFAULT_PROFILES, "davinci"
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        profiles = cfg.get("cloudProfiles") or _DEFAULT_PROFILES
        default_key = cfg.get("defaultProfile") or "davinci"
        # minimal validation
        for k in ("newton", "davinci", "manual"):
            profiles.setdefault(k, _DEFAULT_PROFILES[k])
        return profiles, default_key
    except Exception:
        return _DEFAULT_PROFILES, "davinci"

# Recursive function to search for BLE_ID or LD_Serial_Number in a nested YAML structure
def find_sn_in_yaml(data):
    if isinstance(data, dict):
        # Check if BLE_ID or LD_Serial_Number exists in the current level
        if 'BLE_ID' in data:
            return data['BLE_ID']
        elif 'LD_Serial_Number' in data:
            return data['LD_Serial_Number']
        # If not found, search deeper
        for key, value in data.items():
            result = find_sn_in_yaml(value)
            if result:
                return result
    elif isinstance(data, list):
        # If the data is a list, check each element
        for item in data:
            result = find_sn_in_yaml(item)
            if result:
                return result
    return None

# Function to load and extract the SN from a nested YAML structure
def load_yaml_sn():
    # Open a file dialog for the user to select the YAML file
    file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
    
    if not file_path:  # User cancels the dialog
        return None
    
    # Load the YAML file and search for BLE_ID or LD_Serial_Number
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            
            # Search for BLE_ID or LD_Serial_Number using the recursive function
            sn = find_sn_in_yaml(data)
            
            if sn:
                return sn
            else:
                print("SN not found in BLE_ID or LD_Serial_Number fields.")
                return None

    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
        return None
    
# utils.py (append or place near the top-level helpers)
def load_autofill(yaml_path: str = "config.yaml") -> dict:
    """Read optional autofill block from config.yaml.
       Example:
       autofill:
         sn: "259710800"
         blePassword: "ABCDEFGHIJ"
         patientName: "John"
         govId: "123456789"
         PKEY: "5B76CJH6O34VWMJ0072G35BYI6VZMU0YQE2X0BUFDLBQ97O9UU"   # Base36 (50)
         MKEY: "Tm0moGY/ELrThRKC5a2k6JIRXFKNDh0M6KTQpqqBlic="        # Base64 (32)
         BLE_ID: "Q84XNWWJM3"
         PATIENT_BLE_PWD: "W7AXTB99HL"
    """
    try:
        if not os.path.exists(yaml_path):
            return {}
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("autofill") or {}
    except Exception:
        return {}


# Function to save a screenshot of the current application window
def save_screenshot(root, default_filename="QR_Code.png"):
    # Capture the current window using ImageGrab
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=default_filename,
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )

    if file_path:
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(file_path)
        print(f"Screenshot saved as {file_path}")
