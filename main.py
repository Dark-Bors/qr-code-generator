"""
===============================================================================
 Fetch Production Data (FPD) Tool  |  v4.2.0
-------------------------------------------------------------------------------
 Author : Boris Eldar
 Purpose: Main launcher for the FPD GUI tool
          (Fetches SAP production data, verifies certificates,
           and manages device provisioning for GLD and related platforms)
===============================================================================
"""

import os
import sys
import traceback
import platform
import importlib.util


# ─────────────────────────────────────────────────────────────────────────────
# 🧰 Environment & Path Setup
# ─────────────────────────────────────────────────────────────────────────────
from version import VERSION as APP_VERSION
APP_NAME = "Fetch Production Data (FPD)"

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
        print("👉 Run: pip install customtkinter")
        sys.exit(1)

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
        print_startup_info()

        # Lazy import to prevent GUI initialization issues in headless mode
        from gui import FPDApp  # ← make sure your class in gui.py is named FPDApp

        app = FPDApp()
        app.mainloop()

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Exiting gracefully...")
        sys.exit(0)

    except Exception as e:
        print("❌ Fatal error while launching GUI:")
        print(traceback.format_exc())
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 🏁 Run
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
