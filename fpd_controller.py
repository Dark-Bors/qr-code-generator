# fpd_controller.py
"""
Controller for Fetch Production Data (FPD).
Handles business logic, state management, and interaction with helper modules.
"""

import os
import time
import traceback
import platform
import qrcode
from datetime import datetime
from datetime import datetime
import json
from PIL import Image, ImageDraw, ImageFont

# Helper modules
from sap_api import fetch_certs, fetch_keys
from keys_helpers import save_all_keys, derive_key_hex, derive_key_bytes
from converters import (
    pkey_base36_to_bytes32, bytes32_to_pkey_base36,
    mkey_base64_to_bytes32, bytes32_to_base64
)
from algorithms import mod_11_10, calc_check_digit
from utils import load_autofill

HISTORY_FILE = "history.json"

class FPDController:
    def __init__(self, log_callback=None):
        """
        :param log_callback: Function(msg, level) to send logs to the UI/Console
        """
        self.log_callback = log_callback
        self.sap_data = {}
        self.current_sn = ""
        self.autofill_data = load_autofill()
        self._load_history()

    def validate_sn_format(self, sn: str) -> bool:
        """
        Validates SN format.
        Current Rule: 9 digits (Medtronic/Covidien legacy format often 9 digits).
        Adjust logic as needed.
        """
        if not sn: return False
        import re
        # Example strict rule: ^\d{9}$ (Exactly 9 digits)
        # Modify this regex if your SNs follow different patterns.
        # Based on example inputs: 253000069 (9 digits)
        return bool(re.match(r"^\d{9}$", sn.strip()))

    def _load_history(self):
        self.history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def _append_history(self, sn, folder):
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sn": sn,
            "path": folder
        }
        self.history.insert(0, record)
        self.history = self.history[:50] # Keep last 50
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=2)
            self._log("📜 History updated.")
        except:
            pass

    def get_history(self):
        return self.history

    def get_config(self):
        from sap_api import _load_config
        return _load_config()

    def save_config(self, new_config):
        from sap_api import CONFIG_PATH
        import yaml
        try:
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(new_config, f)
            self._log("⚙️ Config saved.", "success")
        except Exception as e:
            self._log(f"❌ Config save failed: {e}", "error")

    def _log(self, msg, level="info"):
        if self.log_callback:
            self.log_callback(msg, level)
        else:
            print(f"[{level.upper()}] {msg}")

    # ─────────────────────────────────────────────
    # SAP FETCHING
    # ─────────────────────────────────────────────
    def fetch_sap_data(self, sn: str) -> dict:
        """
        Fetch data from SAP for the given SN.
        Updates internal state and returns the data dict.
        """
        if not sn:
            raise ValueError("Serial Number is required.")
        
        self._log(f"ℹ️ Fetching SAP data for SN={sn} ...")
        
    def fetch_sap_data(self, sn: str) -> dict:
        """
        Fetch data from SAP for the given SN.
        Updates internal state and returns the data dict.
        """
        if not sn:
            raise ValueError("Serial Number is required.")
        
        self._log(f"ℹ️ Fetching SAP data for SN={sn} ...")
        
        try:
            # OPTIMIZATION: One call gets all certificates and keys
            self.sap_data = fetch_certs(sn)
            self.current_sn = sn
            self._log(f"✅ SAP data fetched successfully for {sn}", "success")
            return self.sap_data
        except Exception as e:
            self._log(f"❌ SAP fetch failed: {e}", "error")
            raise

    # ─────────────────────────────────────────────
    # SAVE / VERIFY
    # ─────────────────────────────────────────────
    def verify_and_save_all(self, sn: str, base_folder: str = None) -> str:
        """
        Fetches data (if needed), verifies, and saves all files to a timestamped folder.
        Returns the path to the created folder.
        """
        if not sn:
            raise ValueError("Serial number is required.")

        # 1. Fetch Data
        self._log(f"🔍 Verifying and fetching SAP data for SN={sn} ...")
        data = self.fetch_sap_data(sn) # Reuse fetch logic

        # 2. Create Folder
        if not base_folder:
            raise ValueError("No output folder selected.")
        
        timestamp = time.strftime("%Y%m%d_%H%M")
        folder = os.path.join(base_folder, f"{sn}_{timestamp}")
        os.makedirs(folder, exist_ok=True)
        self._log(f"📁 Created output folder: {folder}")

        # 3. Save Certificates
        cert_text = data.get("AUTH_PUBLIC_KEY", "")
        key_text = data.get("AUTH_PRIVATE_KEY", "")
        
        if cert_text and key_text:
            cert_path = os.path.join(folder, "IoTCore_certificate_final.pem.crt")
            key_path = os.path.join(folder, "private_final.pem.key")
            with open(cert_path, "w", encoding="utf-8") as f:
                f.write(cert_text.strip())
            with open(key_path, "w", encoding="utf-8") as f:
                f.write(key_text.strip())
            self._log(f"📁 Certs saved.", "success")
        else:
            self._log("⚠️ Missing certificate or private key in SAP data.", "error")

        # 4. Save Keys (.bin)
        save_all_keys(
            folder, sn,
            data.get("PKEY", ""),
            data.get("MKEY", ""),
            data.get("BLE_ID", ""),
            data.get("PATIENT_BLE_PWD", "")
        )
        self._log(f"✅ All files saved to {folder}", "success")
        
        self._append_history(sn, folder)
        return folder

    def save_single_key(self, key_name: str, val: str, sn: str, folder: str):
        """Save a single key value to a .bin file."""
        if not val or not folder:
            return
        
        fname = f"{key_name}_{sn or 'UNKNOWN'}.bin"
        path = os.path.join(folder, fname)
        
        try:
            # Hex or Raw?
            if all(c in "0123456789ABCDEFabcdef" for c in val) and len(val) % 2 == 0:
                data = bytes.fromhex(val)
            else:
                data = val.encode("utf-8")
                
            with open(path, "wb") as f:
                f.write(data)
            self._log(f"💾 Saved {key_name} → {path}", "success")
        except Exception as e:
            self._log(f"❌ Save failed: {e}", "error")

    # ─────────────────────────────────────────────
    # AUTO-RUN
    # ─────────────────────────────────────────────
    def auto_run(self, sn: str, output_base: str, options: dict) -> str:
        """
        Executes the full workflow: Fetch -> Save -> Generate QRs.
        Returns the path of the generated folder.
        """
        if not sn or not output_base:
            raise ValueError("SN and Output Folder are required.")

        self._log(f"⚡ Auto-Run started for SN={sn}...", "info")
        
        # 1. Fetch & Save
        folder = self.verify_and_save_all(sn, output_base)
        
        # 2. Get Keys
        keys = {
            "BLE_ID": self.sap_data.get("BLE_ID", ""),
            "PATIENT_BLE_PWD": self.sap_data.get("PATIENT_BLE_PWD", "")
        }
        
        # 3. Generate QRs
        self.generate_qrs(sn, keys, options, folder)
        
        self._log("⚡ Auto-Run complete!", "success")
        return folder

    # ─────────────────────────────────────────────
    # KEY CONVERSIONS
    # ─────────────────────────────────────────────
    def derive_key(self, val: str) -> str:
        """Wrapper for key derivation."""
        return derive_key_hex(val).upper()
        
    def convert_pkey(self, current_val: str) -> tuple[str, str]:
        """
        Smart convert PKEY (Base36 <-> Hex).
        Returns (new_value, log_message).
        """
        val = current_val.strip().upper()
        if not val:
            raise ValueError("Empty PKEY")

        # Heuristics
        if len(val) == 50 and all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in val):
            raw = pkey_base36_to_bytes32(val)
            new_val = raw.hex().upper()
            msg = "Base36 → HEX"
        elif len(val) == 64 and all(c in "0123456789ABCDEF" for c in val):
            raw = bytes.fromhex(val)
            new_val = bytes32_to_pkey_base36(raw)
            msg = "HEX → Base36"
        else:
            raise ValueError("Unrecognized PKEY format (expected 50-char Base36 or 64-char HEX)")
            
        return new_val, msg

    def convert_mkey(self, current_val: str) -> tuple[str, str]:
        """
        Smart convert MKEY (Base64 <-> Hex).
        Returns (new_value, log_message).
        """
        val = current_val.strip()
        if not val:
            raise ValueError("Empty MKEY")
            
        if len(val) == 44 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in val):
            raw = mkey_base64_to_bytes32(val)
            new_val = raw.hex().upper()
            msg = "Base64 → HEX"
        elif len(val) == 64 and all(c in "0123456789ABCDEFabcdef" for c in val):
            raw = bytes.fromhex(val)
            new_val = bytes32_to_base64(raw)
            msg = "HEX → Base64"
        else:
            raise ValueError("Unrecognized MKEY format (expected Base64 or 64-char HEX)")
            
        return new_val, msg

    # ─────────────────────────────────────────────
    # QR GENERATION
    # ─────────────────────────────────────────────
    def generate_qrs(self, sn: str, keys: dict, options: dict, final_folder: str = None) -> str:
        """
        Generate QRs based on options.
        keys dict must contain: BLE_ID, PATIENT_BLE_PWD
        options dict: {rtv: bool, newton: bool, davinci: bool, custom_rtv: str, custom_patient: str}
        """
        if not sn:
            raise ValueError("Serial number required.")
        
        if not final_folder:
            raise ValueError("Output folder required.") # Controller expects path to be passed

        qr_dir = os.path.join(final_folder, "QR Code")
        os.makedirs(qr_dir, exist_ok=True)
        
        # 1. Calculate Checksums
        try:
            sn_check = mod_11_10(sn)
            sn_full = f"{sn}{sn_check}"
        except Exception as e:
            self._log(f"⚠️ SN checksum failed: {e}", "error")
            sn_full = sn

        ble_id_val = keys.get("BLE_ID", "").strip()
        ble_pwd_val = keys.get("PATIENT_BLE_PWD", "").strip()
        
        try:
            # BLE_ID Checksum
            if ble_id_val:
                c1 = calc_check_digit(ble_id_val.lower())
                ble_id_full = f"{ble_id_val}{c1.upper()}"
            else:
                ble_id_full = ""
                
            # PATIENT_BLE_PWD Checksum
            if ble_pwd_val:
                c2 = calc_check_digit(ble_pwd_val.lower())
                ble_pwd_full = f"{ble_pwd_val}{c2.upper()}"
            else:
                ble_pwd_full = ""
        except Exception:
            self._log("⚠️ Key checksum failed, using raw values.", "error")
            ble_id_full = ble_id_val
            ble_pwd_full = ble_pwd_val

        # 2. Build Payloads
        payloads = []
        if options.get("rtv"):
            payloads.append(("RTV", f"bleSerial:{sn_full};blePassword:{ble_id_full};name:Patient;govId:123456789"))
        if options.get("newton"):
            payloads.append(("Newton", f"bleSerial:{sn_full};blePassword:{ble_pwd_full};cloudUrl:a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com;mqttPrefix:newton/dev/things"))
        if options.get("davinci"):
            payloads.append(("Davinci", f"bleSerial:{sn_full};blePassword:{ble_pwd_full};cloudUrl:a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com;mqttPrefix:davinci/dev/things"))
        
        # Custom payloads
        if options.get("custom_rtv_enabled") and options.get("custom_rtv_text"):
             payloads.append(("Custom_RTV", options["custom_rtv_text"]))
        if options.get("custom_patient_enabled") and options.get("custom_patient_text"):
             payloads.append(("Custom_PatientApp", options["custom_patient_text"]))

        # 3. Generate Images
        qr_imgs = []
        for name, payload in payloads:
            img = qrcode.make(payload)
            img_path = os.path.join(qr_dir, f"QR_{name}_{sn}.png")
            txt_path = os.path.join(qr_dir, f"QR_{name}_{sn}.txt")
            img.save(img_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(payload)
            qr_imgs.append((name, img))
            self._log(f"✅ QR {name} saved.", "success")

        # 4. Create Bundle
        if qr_imgs:
            self._create_qr_bundle(sn, qr_imgs, qr_dir)

        return qr_dir

    def _create_qr_bundle(self, sn: str, qr_imgs: list, output_dir: str):
        """Helper to create the combined image."""
        total_height = sum(img.size[1] + 100 for _, img in qr_imgs) + 140
        width = max(img.size[0] for _, img in qr_imgs) + 200
        bundle = Image.new("RGB", (width, total_height), "white")
        draw = ImageDraw.Draw(bundle)

        try:
            font_title = ImageFont.truetype("arialbd.ttf", 36)
            font_label = ImageFont.truetype("arial.ttf", 28)
        except:
            font_title = font_label = ImageFont.load_default()

        def text_size(text, font):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                return draw.textsize(text, font=font)

        # Header
        title = f"Fetch Production Data – SN: {sn}"
        subtitle = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        tw, th = text_size(title, font_title)
        sw, sh = text_size(subtitle, font_label)
        
        draw.text(((width - tw) / 2, 20), title, fill=(0, 102, 204), font=font_title)
        draw.text(((width - sw) / 2, 70), subtitle, fill=(80, 80, 80), font=font_label)

        # QRs
        y = 140
        for name, img in qr_imgs:
            label = f"QR: {name}"
            lw, lh = text_size(label, font_label)
            draw.text(((width - lw) / 2, y), label, fill=(0, 51, 102), font=font_label)
            
            # Unwrap qrcode's PilImage wrapper if necessary
            real_img = getattr(img, "_img", img)
            
            qr_x = (width - img.size[0]) // 2
            bundle.paste(real_img, (qr_x, y + 40))
            y += img.size[1] + 100

        bundle_path = os.path.join(output_dir, f"QR_Bundle_{sn}.png")
        bundle.save(bundle_path)
        self._log(f"🖼️ QR bundle created → {bundle_path}", "success")

    # ─────────────────────────────────────────────
    # BATCH PROCESSING
    # ─────────────────────────────────────────────
    def batch_process_file(self, file_path: str, output_base: str, options: dict, progress_callback=None) -> dict:
        """
        Process a list of SNs from a file (txt).
        Returns summary dict: {'total': int, 'success': int, 'failed': int, 'errors': list}
        """
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path.")

        with open(file_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        total = len(lines)
        success = 0
        failed = 0
        errors = []

        self._log(f"🚀 Starting batch output for {total} devices...", "info")

        for i, sn in enumerate(lines, 1):
            if progress_callback:
                progress_callback(i, total)
                
            try:
                self._log(f"--- Processing {i}/{total}: {sn} ---")
                # 1. Fetch & Save
                folder = self.verify_and_save_all(sn, output_base)
                
                # 2. Key Checks (needed for QR)
                # verify_and_save_all updates self.sap_data, so we can use it
                keys = {
                    "BLE_ID": self.sap_data.get("BLE_ID", ""),
                    "PATIENT_BLE_PWD": self.sap_data.get("PATIENT_BLE_PWD", "")
                }
                
                # 3. Generate QRs
                self.generate_qrs(sn, keys, options, folder)
                success += 1
                
            except Exception as e:
                failed += 1
                msg = f"Failed SN={sn}: {str(e)}"
                errors.append(msg)
                self._log(f"❌ {msg}", "error")

        summary = {
            "total": total,
            "success": success,
            "failed": failed,
            "errors": errors
        }
        self._log(f"🏁 Batch Complete: {success}/{total} successful.", "success")
        return summary
