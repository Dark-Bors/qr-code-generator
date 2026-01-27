"""
===============================================================================
 Fetch Production Data (FPD) Tool (v6.0.0)
-------------------------------------------------------------------------------
 Author : Boris Eldar
 Purpose: Main launcher for the FPD GUI tool.
          Fetches SAP production data, verifies certificates, and manages 
          device provisioning.
===============================================================================
"""

import os
import sys
import shutil
import platform
import logging
import traceback
import tkinter.messagebox as mbox
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 🧰 Environment & Path Setup
# ─────────────────────────────────────────────────────────────────────────────
from version import VERSION as APP_VERSION

APP_NAME = "Fetch Production Data (FPD)"

# Detect correct working directory (handles .exe vs. dev run)
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).resolve().parent

CONFIG_PATH = ROOT_DIR / "config.yaml"
Example_CONFIG_PATH = ROOT_DIR / "config.example.yaml"
LOG_FILE = ROOT_DIR / "fpd_debug.log"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("Main")

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# ─────────────────────────────────────────────────────────────────────────────
# 🧩 Dependency Check
# ─────────────────────────────────────────────────────────────────────────────
def ensure_dependencies():
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        logger.error("'customtkinter' not found.")
        mbox.showerror("Missing Dependency", "The 'customtkinter' library is missing.\nPlease run: pip install customtkinter")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 🆕 Config Management
# ─────────────────────────────────────────────────────────────────────────────
def ensure_config_yaml():
    """Ensure config.yaml exists by copying example if available."""
    if CONFIG_PATH.exists():
        logger.info(f"✅ Config found: {CONFIG_PATH}")
        return

    logger.warning("⚠️ config.yaml not found. Attempting to create from template...")
    
    if Example_CONFIG_PATH.exists():
        try:
            shutil.copy(Example_CONFIG_PATH, CONFIG_PATH)
            logger.info("✅ Created config.yaml from config.example.yaml")
            mbox.showinfo("Configuration Created", "A default 'config.yaml' has been created.")
            return
        except Exception as e:
            logger.error(f"Failed to copy config example: {e}")
    
    # Fallback to minimal if example missing
    default_yaml = """
sap:
  endpoint: "https://tlvm7aapps032.cfrf.medtronic.com/sap/bc/zws_g_get_sn?sap-client=300&SN={sn}"
  verifyTLS: false
paths:
  output_root: "./output"
"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(default_yaml)
        logger.warning("⚠️ Created minimal config.yaml (template missing).")
    except Exception as e:
         logger.error(f"Failed to write config.yaml: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    try:
        logger.info(f"🚀 Launching {APP_NAME} {APP_VERSION} on {platform.system()}")
        ensure_dependencies()
        ensure_config_yaml()

        from gui import FPDApp
        app = FPDApp()
        app.mainloop()

    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user.")
        sys.exit(0)
    except Exception:
        err = traceback.format_exc()
        logger.critical(f"❌ Fatal error:\n{err}")
        try:
            mbox.showerror("Fatal Error", f"Application failed to start:\n{err}")
        except:
             pass # simple print if GUI fails
        sys.exit(1)

if __name__ == "__main__":
    main()

