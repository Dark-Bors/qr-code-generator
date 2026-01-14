"""
===============================================================================
 Fetch Production Data (FPD) Tool (v6.0.0)
-------------------------------------------------------------------------------
 Author : Boris Eldar
 Purpose: Main launcher for the FPD GUI tool
          (Fetches SAP production data, verifies certificates,
           and manages device provisioning for GLD and related platforms)
 New in v6.0: Batch Processing, One-Click Auto-Run, Threading, EXE Build
===============================================================================
"""

import os
import sys
import traceback
import platform
import importlib.util
import textwrap  # 🆕
import tkinter.messagebox as mbox  # 🆕

# ─────────────────────────────────────────────────────────────────────────────
# 🧰 Environment & Path Setup
# ─────────────────────────────────────────────────────────────────────────────
from version import VERSION as APP_VERSION
APP_NAME = "Fetch Production Data (FPD)"

# Detect correct working directory (handles .exe vs. dev run)
if getattr(sys, 'frozen', False):  # running from compiled exe
    ROOT_DIR = os.path.dirname(sys.executable)
else:  # running from source
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

VENV_DIR = os.path.join(ROOT_DIR, "venv")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.yaml")


# Add project root to sys.path if not already
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Optional: Check that CustomTkinter is installed
# ─────────────────────────────────────────────────────────────────────────────
def ensure_dependencies():
    try:
        import customtkinter  # noqa
    except ImportError:
        print("❌ ERROR: 'customtkinter' not found in current environment.")
        print("👉 Run: python -m pip install customtkinter")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 🆕 Ensure config.yaml exists (create default if missing)
# ─────────────────────────────────────────────────────────────────────────────
def ensure_config_yaml():
    """Create default config.yaml if it doesn't exist."""
    if os.path.exists(CONFIG_PATH):
        print("✅ Found existing config.yaml")
        return

    default_yaml = textwrap.dedent("""\
        # ─────────────────────────────────────────────
        # Fetch Production Data (FPD) - Configuration
        # Version: 4.2.0
        # Author: Boris Eldar
        # ─────────────────────────────────────────────

        sap:
          base_url: "https://tlvm7aappd040.cfrf.medtronic.com/sap/bc"
          client: "300"
          cert_endpoint: "zws_g_get_sn"
          key_endpoint: "zws_g_get_keys"

        paths:
          output_root: "C:/Users/eldarb2/Downloads"
          temp: "./temp"
          certs: "./certs"

        certificates:
          iot_cert_name: "IoTCore_certificate_final.pem.crt"
          private_key_name: "private_final.pem.key"
          combined_name: "combined.pem"

        qr:
          newton_cloud_url: "a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com"
          davinci_cloud_url: "a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com"
          mqtt_prefix_newton: "newton/dev/things"
          mqtt_prefix_davinci: "davinci/dev/things"

        logging:
          enable_debug: true
          log_to_file: true
          log_file: "./fpd_debug.log"

        ui:
          theme: "dark"
          default_width: 1180
          default_height: 900
          font: "Segoe UI"
          version: "v4.2.0"

        autofill:
          sn: "259710800"
          patientName: "Test"
          govId: ""
          PKEY: "2FDIU7I6KPZX4H9QOS6EQLDJGHD2UT5HX0E8BEKM0BKWIAX3DT"
          MKEY: "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI="
          BLE_ID: "ABCDEFGHIJ"
          PATIENT_BLE_PWD: "ABCDEFGHIJ"
    """)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(default_yaml)

    print(f"🆕 Created default config.yaml → {CONFIG_PATH}")

    try:
        mbox.showinfo(
            "Configuration Created",
            "A default 'config.yaml' has been generated.\nYou can edit it if needed before rerunning the app."
        )
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# 🪄 Optional: Print System Info for Debugging
# ─────────────────────────────────────────────────────────────────────────────
def print_startup_info():
    print("──────────────────────────────────────────────")
    print(f"🧩  Launching {APP_NAME}  ({APP_VERSION})")
    print(f"💻  Platform : {platform.system()} {platform.release()}")
    print(f"🐍  Python   : {platform.python_version()}")
    print(f"📂  Working  : {ROOT_DIR}")
    print("──────────────────────────────────────────────\n")

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    try:
        ensure_dependencies()
        ensure_config_yaml()  # 🆕 Make sure config.yaml exists
        print_startup_info()

        from gui import FPDApp  # lazy import GUI class
        app = FPDApp()
        app.mainloop()

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception:
        print("❌ Fatal error while launching GUI:")
        print(traceback.format_exc())
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 🏁 Run
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
