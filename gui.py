# gui.py — Fetch Production Data (FPD)
# Author: Boris Eldar

import os
import platform
import pyperclip
import yaml
import qrcode
import time
from datetime import datetime
from tkinter import filedialog, messagebox, BooleanVar, StringVar
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import traceback

from version import VERSION
from sap_api import fetch_certs, fetch_keys
from certificate_utils import verify_cert_pair
from keys_helpers import save_all_keys
from utils import load_autofill
from converters import (
    pkey_base36_to_bytes32, bytes32_to_pkey_base36,
    mkey_base64_to_bytes32, bytes32_to_base64
)

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FPDApp(ctk.CTk):
    """Main GUI window for Fetch Production Data (FPD)."""

    def __init__(self):
        super().__init__()
        self.title(f"🔧 Fetch Production Data (FPD) {VERSION}")
        self.geometry("1180x900")
        self.resizable(False, False)

        self.sap_data = {}
        self.autofill = load_autofill()
        self.current_sn = ""
        self.output_dir = ""

        # State variables
        self.qr_rtv = BooleanVar(value=True)
        self.qr_newton = BooleanVar(value=True)
        self.qr_davinci = BooleanVar(value=True)
        self.qr_custom_rtv = BooleanVar(value=False)
        self.qr_custom_patient = BooleanVar(value=False)

        # Custom entries
        self.custom_rtv = StringVar(value="")
        self.custom_patient = StringVar(value="")

        # Build full GUI
        self._build_ui()
        self.after(300, self._log_env)
        
    def _show_info(self):
        """Display detailed app, algorithm, and QR structure information."""
        info_text = (
            "───────────────────────────────\n"
            "🔧  Fetch Production Data (FPD)\n"
            f"📦  Version: {VERSION}\n"
            "───────────────────────────────\n\n"
            
            "🧮  Algorithms:\n"
            "• PKEY  →  Base36 (50 chars) ↔ 32 bytes (little-endian)\n"
            "• MKEY  →  Base64 ↔ 32 bytes\n"
            "• BLE_ID & PATIENT_BLE_PWD → PBKDF2-HMAC-SHA256\n"
            "     Salt: C30AF78E2C3EE53B5D52E2FD93B3513A\n"
            "     Iterations: 310,000\n\n"

            "🔗  QR Code Base Profiles:\n"
            "• Newton   →  a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com\n"
            "• Davinci  →  a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com\n"
            "• Custom RTV & Patient App →  User-defined payloads\n\n"

            "🧰  Conversion Summary:\n"
            "• PKEY ⇄ 32-byte raw via Base36 ↔ Hex\n"
            "• MKEY ⇄ 32-byte raw via Base64\n"
            "• BLE_ID / PATIENT_BLE_PWD → Derived 32-byte key via PBKDF2\n"
            "• Combined file → keys_2_3_4_<SN>.bin (MKEY + BLE + PWD)\n\n"

            "📱  App & Environment:\n"
            f"• Platform: {platform.system()} {platform.release()}\n"
            f"• Python: {platform.python_version()}\n"
            "• GUI Framework: CustomTkinter (Dark Theme)\n"
            "• Author: Boris Eldar\n"
            "───────────────────────────────\n"
            "💡  Tip: Use 'Verify & Save All' to fetch + save everything in one click."
        )

        messagebox.showinfo("About FPD Tool", info_text)

        

    # ─────────────── OUTPUT FOLDER ───────────────
    def _create_output_folder(self, sn: str) -> str:
        """
        Ask the user to select a base folder (interactive) and
        create a timestamped subfolder for all outputs.
        """
        # Prompt user to select root save directory
        base_dir = filedialog.askdirectory(
            title="Select root folder to save the output package"
        )

        if not base_dir:
            self._log("⚠️ No folder selected. Operation cancelled.", "error")
            raise RuntimeError("User cancelled folder selection.")

        # Create timestamped subfolder
        timestamp = time.strftime("%Y%m%d_%H%M")
        folder = os.path.join(base_dir, f"{sn}_{timestamp}")
        os.makedirs(folder, exist_ok=True)

        # Log and return
        self._log(f"📁 Created output folder: {folder}", "info")
        return folder


    # ─────────────── UI STRUCTURE ───────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_device_panel()
        self._build_cert_panel()
        self._build_keys_panel()
        self._build_qr_panel()
        self._build_log_panel()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text=f"Fetch Production Data (FPD) {VERSION}",
            font=("Segoe UI", 28, "bold"),
        ).grid(row=0, column=0, pady=10)
        
        ctk.CTkButton(self, text="ℹ️ Info", width=80, command=self._show_info)\
            .place(x=1060, y=25)


    def _build_device_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Device Serial Number:", font=("Segoe UI", 14)).grid(
            row=0, column=0, padx=10, pady=10
        )
        self.sn_entry = ctk.CTkEntry(frame, width=200)
        self.sn_entry.grid(row=0, column=1, padx=5)

        ctk.CTkButton(frame, text="🛰️ Fetch SAP Data", command=self._fetch_sap).grid(
            row=0, column=2, padx=10
        )
        ctk.CTkButton(
            frame, text="💾 Verify & Save All", command=self._verify_and_save_all
        ).grid(row=0, column=3, padx=10)

    def _build_cert_panel(self):
        self.cert_frame = ctk.CTkFrame(self)
        self.cert_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.cert_frame.grid_remove()

        self.cert_status = ctk.CTkLabel(
            self.cert_frame,
            text="Status: Not verified",
            text_color="orange",
            font=("Segoe UI", 14),
        )
        self.cert_status.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    def _build_keys_panel(self):
        """Keys panel with live validation, converters, and save buttons."""
        self.keys_frame = ctk.CTkFrame(self)
        self.keys_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        title = ctk.CTkLabel(
            self.keys_frame,
            text="🔑 Keys Panel (click to expand/collapse)",
            font=("Segoe UI", 16, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=10)
        title.bind("<Button-1>", lambda e: self._toggle_keys())

        self.keys_inner = ctk.CTkFrame(self.keys_frame)
        self.keys_inner.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.entries = {}
        self.preview_labels = {}

        fields = ["PKEY", "MKEY", "BLE_ID", "PATIENT_BLE_PWD"]

        for i, f in enumerate(fields):
            # Field label
            ctk.CTkLabel(self.keys_inner, text=f"{f}:", font=("Segoe UI", 13)).grid(
                row=i, column=0, sticky="w", padx=5, pady=3
            )

            # Text entry
            entry = ctk.CTkEntry(self.keys_inner, width=360)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entry.bind("<KeyRelease>", lambda e, k=f: self._validate_key_live(k))
            self.entries[f] = entry

            # Small preview text (below each entry)
            self.preview_labels[f] = ctk.CTkLabel(self.keys_inner, text="", font=("Consolas", 10))
            self.preview_labels[f].grid(row=i, column=1, sticky="s", pady=(0, 4))

            # 💾 Save button
            ctk.CTkButton(
                self.keys_inner,
                text="💾 Save",
                width=80,
                command=lambda k=f: self._save_single_key(k),
            ).grid(row=i, column=2, padx=5)

            # Conversion / Derive buttons
            if f == "PKEY":
                ctk.CTkButton(
                    self.keys_inner,
                    text="⇄ Convert PKEY",
                    width=140,
                    command=self._smart_convert_pkey,
                ).grid(row=i, column=3, padx=5)
            elif f == "MKEY":
                ctk.CTkButton(
                    self.keys_inner,
                    text="⇄ Convert MKEY",
                    width=140,
                    command=self._convert_mkey_format,
                ).grid(row=i, column=3, padx=5)
            elif f in ("BLE_ID", "PATIENT_BLE_PWD"):
                ctk.CTkButton(
                    self.keys_inner,
                    text="➡️ Derive Key",
                    width=140,
                    command=lambda k=f: self._derive_key_field(k),
                ).grid(row=i, column=3, padx=5)
                
            ctk.CTkButton(self.keys_inner, text="⚙️ Fill All", command=self._fill_all_fields)\
                .grid(row=0, column=4, padx=10, pady=(4,0))

        self.keys_visible = True


    # ─────────────── QR PANEL ───────────────
    def _build_qr_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(
            frame, text="QR Code Options", font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # checkboxes
        ctk.CTkCheckBox(frame, text="RTV", variable=self.qr_rtv).grid(
            row=1, column=0, sticky="w", padx=20
        )
        ctk.CTkCheckBox(frame, text="Newton", variable=self.qr_newton).grid(
            row=1, column=1, sticky="w", padx=20
        )
        ctk.CTkCheckBox(frame, text="Davinci", variable=self.qr_davinci).grid(
            row=1, column=2, sticky="w", padx=20
        )
        ctk.CTkCheckBox(frame, text="Custom RTV", variable=self.qr_custom_rtv).grid(
            row=1, column=3, sticky="w", padx=20
        )
        ctk.CTkCheckBox(
            frame, text="Custom Patient App", variable=self.qr_custom_patient
        ).grid(row=1, column=4, sticky="w", padx=20)

        # Custom fields
        ctk.CTkLabel(frame, text="Custom RTV:", font=("Segoe UI", 13)).grid(
            row=2, column=0, sticky="w", padx=20
        )
        self.custom_rtv_entry = ctk.CTkEntry(
            frame, textvariable=self.custom_rtv, width=800
        )
        self.custom_rtv_entry.grid(row=2, column=1, columnspan=4, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Custom Patient App:", font=("Segoe UI", 13)).grid(
            row=3, column=0, sticky="w", padx=20
        )
        self.custom_patient_entry = ctk.CTkEntry(
            frame, textvariable=self.custom_patient, width=800
        )
        self.custom_patient_entry.grid(row=3, column=1, columnspan=4, padx=10, pady=5)

        ctk.CTkButton(
            frame, text="🔳 Generate QR Codes", command=self._generate_qrs
        ).grid(row=4, column=0, padx=20, pady=10, sticky="w")

    def _build_log_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame, text="📜 Activity Log", font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10)
        self.log_box = ctk.CTkTextbox(frame, width=1120, height=230)
        self.log_box.grid(row=1, column=0, padx=10, pady=10)
        self.log_box.configure(state="disabled")

    # ─────────────── LOGGING ───────────────
    def _log(self, msg: str, level: str = "info"):
        colors = {
            "info": "#3a8bff",
            "success": "#00b050",
            "error": "#ff4040",
        }
        ts = datetime.now().strftime("[%H:%M:%S] ")

        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{ts}{msg}\n", level)
        self.log_box.tag_config(level, foreground=colors.get(level, "white"))
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _log_env(self):
        self._log(f"🧩 Launching Fetch Production Data (FPD) ({VERSION})", "info")
        self._log(f"💻 Platform : {platform.system()} {platform.release()}", "info")
        self._log(f"🐍 Python   : {platform.python_version()}", "info")
        self._log(f"📂 Working  : {os.getcwd()}", "info")
        self._log("──────────────────────────────────────────────", "info")

    # ─────────────── SAP HANDLERS ───────────────
    def _fetch_sap(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showwarning("Missing SN", "Enter a serial number first.")
            return
        self._log(f"ℹ️ Fetching SAP data for SN={sn} ...", "info")
        try:
            cert_data = fetch_certs(sn)
            key_data = fetch_keys(sn)
            self.sap_data = {**cert_data, **key_data}
            self.current_sn = sn
            self._log(f"✅ SAP data fetched successfully for {sn}", "success")
            # Auto-fill keys panel once SAP data fetched
            for field in ("PKEY", "MKEY", "BLE_ID", "PATIENT_BLE_PWD"):
                val = self.sap_data.get(field, "")
                if field in self.entries:
                    self.entries[field].delete(0, "end")
                    self.entries[field].insert(0, val)
            self._log("⚙️ Keys panel auto-filled from SAP data.", "info")

        except Exception as e:
            self._log(f"❌ SAP fetch failed: {e}", "error")
            traceback.print_exc()

    def _verify_and_save_all(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            self._log("❌ Please enter a valid serial number.", "error")
            return

        try:
            self._log(f"🔍 Verifying and fetching SAP data for SN={sn} ...", "info")

            cert_data = fetch_certs(sn)
            key_data = {}
            try:
                key_data = fetch_keys(sn)
            except Exception as e:
                self._log(f"⚠️ Key fetch failed: {e}", "error")

            data = {**cert_data, **key_data}
            folder = self._create_output_folder(sn)
            self._log(f"💾 Saving certs and keys to: {folder}", "info")

            # Save certificates
            cert_text = data.get("AUTH_PUBLIC_KEY", "")
            key_text = data.get("AUTH_PRIVATE_KEY", "")
            if cert_text and key_text:
                cert_path = os.path.join(folder, "IoTCore_certificate_final.pem.crt")
                key_path = os.path.join(folder, "private_final.pem.key")
                with open(cert_path, "w", encoding="utf-8") as f:
                    f.write(cert_text.strip())
                with open(key_path, "w", encoding="utf-8") as f:
                    f.write(key_text.strip())
                self._log(f"📁 Certificate saved → {cert_path}", "success")
                self._log(f"📁 Private key saved → {key_path}", "success")
            else:
                self._log("⚠️ Missing certificate or private key in SAP data.", "error")

            # Save .bin key files
            save_all_keys(
                folder,
                sn,
                data.get("PKEY", ""),
                data.get("MKEY", ""),
                data.get("BLE_ID", ""),
                data.get("PATIENT_BLE_PWD", ""),
            )

            self._log(f"✅ All certs and key files saved to {folder}", "success")

        except Exception as e:
            self._log(f"❌ Fatal error: {e}", "error")
            traceback.print_exc()

    # ─────────────── QR GENERATION ───────────────
    def _generate_qrs(self, folder=None):
        if not folder:
            folder = filedialog.askdirectory(title="Select folder for QR output")
            if not folder:
                return
        qr_dir = os.path.join(folder, "QR Code")
        os.makedirs(qr_dir, exist_ok=True)

        sn = self.current_sn or self.sn_entry.get().strip()
        if not sn:
            messagebox.showwarning("Missing SN", "Enter a serial number first.")
            return

        payloads = []

        if self.qr_rtv.get():
            payloads.append(("RTV", f"bleSerial:{sn};blePassword:{self.entries['BLE_ID'].get()};name:Patient;govId:123456789"))
        if self.qr_newton.get():
            payloads.append(("Newton", f"bleSerial:{sn};blePassword:{self.entries['PATIENT_BLE_PWD'].get()};cloudUrl:a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com;mqttPrefix:newton/dev/things"))
        if self.qr_davinci.get():
            payloads.append(("Davinci", f"bleSerial:{sn};blePassword:{self.entries['PATIENT_BLE_PWD'].get()};cloudUrl:a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com;mqttPrefix:davinci/dev/things"))
        if self.qr_custom_rtv.get():
            payloads.append(("Custom_RTV", self.custom_rtv.get()))
        if self.qr_custom_patient.get():
            payloads.append(("Custom_PatientApp", self.custom_patient.get()))

        qr_imgs = []
        for name, payload in payloads:
            img = qrcode.make(payload)
            img_path = os.path.join(qr_dir, f"QR_{name}_{sn}.png")
            txt_path = os.path.join(qr_dir, f"QR_{name}_{sn}.txt")
            img.save(img_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(payload)
            qr_imgs.append((name, img))
            self._log(f"✅ QR {name} saved → {img_path}", "success")

        # ─────────────────────────────
        # 🖼️ Combine into QR Bundle Image
        # ─────────────────────────────

        total_height = sum(img.size[1] + 100 for _, img in qr_imgs) + 140
        width = max(img.size[0] for _, img in qr_imgs) + 200
        bundle = Image.new("RGB", (width, total_height), "white")
        draw = ImageDraw.Draw(bundle)

        # Try to use Arial font; fallback to default
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 36)
            font_label = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font_title = font_label = ImageFont.load_default()

        def text_size(draw_obj, text, font):
            """Cross-compatible text size."""
            try:
                bbox = draw_obj.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                w, h = draw_obj.textsize(text, font=font)
            return w, h

        # Header
        title = f"Fetch Production Data – SN: {sn}"
        subtitle = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        tw, th = text_size(draw, title, font_title)
        sw, sh = text_size(draw, subtitle, font_label)

        draw.text(((width - tw) / 2, 20), title, fill=(0, 102, 204), font=font_title)
        draw.text(((width - sw) / 2, 70), subtitle, fill=(80, 80, 80), font=font_label)

        # Paste QRs centered with colored labels
        y = 140
        for name, img in qr_imgs:
            label = f"QR: {name}"
            lw, lh = text_size(draw, label, font_label)
            draw.text(((width - lw) / 2, y), label, fill=(0, 51, 102), font=font_label)

            qr_x = (width - img.size[0]) // 2
            bundle.paste(img, (qr_x, y + 40))
            y += img.size[1] + 100

        # Save bundle
        bundle_path = os.path.join(qr_dir, f"QR_Bundle_{sn}.png")
        bundle.save(bundle_path)
        self._log(f"🖼️ QR bundle created → {bundle_path}", "success")


    # ─────────────── UTILS ───────────────
    def _fill_all_fields(self):
        """Fill all entries from config.yaml -> 'autofill' section."""
        data = self.autofill or {}
        if not data:
            self._log("⚠️ No autofill data found in config.yaml.", "error")
            return

        # Fill SN
        if data.get("sn"):
            self.sn_entry.delete(0, "end")
            self.sn_entry.insert(0, data["sn"])

        # Fill PKEY, MKEY, BLE_ID, PATIENT_BLE_PWD
        for key in ("PKEY", "MKEY", "BLE_ID", "PATIENT_BLE_PWD"):
            if key in self.entries:
                self.entries[key].delete(0, "end")
                self.entries[key].insert(0, data.get(key, ""))

        # Fill QR custom fields
        patient_name = data.get("patientName", "Patient")
        gov_id = data.get("govId") or str(__import__("random").randint(100000000, 999999999))

        self.custom_rtv_entry.delete(0, "end")
        self.custom_rtv_entry.insert(0,
            f"bleSerial:{data.get('sn')};blePassword:{data.get('BLE_ID')};name:{patient_name};govId:{gov_id}"
        )

        self.custom_patient_entry.delete(0, "end")
        self.custom_patient_entry.insert(0,
            f"bleSerial:{data.get('sn')};blePassword:{data.get('PATIENT_BLE_PWD')};cloudUrl:a1y5k9515f72z8-ats.iot.eu-central-1.amazonaws.com;mqttPrefix:newton/dev/things"
        )

        self._log("⚙️ All fields auto-filled from config.yaml.", "success")


# ───────────────────────────────────────────────
    # SMART CONVERSION + VALIDATION LOGIC
    # ───────────────────────────────────────────────
    def _smart_convert_pkey(self):
        """
        Auto-detect Base36 or HEX for PKEY, using converters.py.
        Converts Base36<->HEX (little-endian), shows SHA256 preview.
        """
        from converters import pkey_base36_to_bytes32, bytes32_to_pkey_base36
        import hashlib

        pkey = self.entries["PKEY"].get().strip().upper()
        if not pkey:
            messagebox.showwarning("Missing PKEY", "Enter or fetch a PKEY first.")
            return

        try:
            # Heuristics: Base36 (50 chars A-Z0-9) vs HEX (64 chars 0-9A-F)
            if len(pkey) == 50 and all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in pkey):
                raw = pkey_base36_to_bytes32(pkey)
                new_val = raw.hex().upper()
                direction = "Base36 → HEX"
            elif len(pkey) == 64 and all(c in "0123456789ABCDEF" for c in pkey):
                raw = bytes.fromhex(pkey)
                new_val = bytes32_to_pkey_base36(raw)
                direction = "HEX → Base36"
            else:
                raise ValueError("Unrecognized PKEY format (expected 50-char Base36 or 64-char HEX)")

            # Update field
            self.entries["PKEY"].delete(0, "end")
            self.entries["PKEY"].insert(0, new_val)

            # Show SHA256 + byte length
            h = hashlib.sha256(raw).hexdigest()[:8].upper()
            preview = f"Decoded length: {len(raw)} bytes | SHA256: {h}..."
            self.preview_labels["PKEY"].configure(text=preview, text_color="#66FF99")
            self._log(f"🔄 Converted PKEY ({direction}). {preview}", "success")

        except Exception as e:
            self.preview_labels["PKEY"].configure(text="⚠️ Invalid or incomplete PKEY", text_color="#FF6666")
            self._log(f"❌ Conversion failed: {e}", "error")


    # ───────────────────────────────────────────────
    # GENERIC CONVERSION + SAVE HELPERS
    # ───────────────────────────────────────────────
    def _convert_mkey_format(self):
        """Toggle between Base64 and HEX for MKEY using converters.py."""
        from converters import mkey_base64_to_bytes32, bytes32_to_base64
        import hashlib

        mkey = self.entries["MKEY"].get().strip()
        if not mkey:
            messagebox.showwarning("Missing MKEY", "Enter or fetch an MKEY first.")
            return

        try:
            if len(mkey) == 44 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in mkey):
                raw = mkey_base64_to_bytes32(mkey)
                new_val = raw.hex().upper()
                direction = "Base64 → HEX"
            elif len(mkey) == 64 and all(c in "0123456789ABCDEFabcdef" for c in mkey):
                raw = bytes.fromhex(mkey)
                new_val = bytes32_to_base64(raw)
                direction = "HEX → Base64"
            else:
                raise ValueError("Unrecognized MKEY format (expected Base64 or 64-char HEX)")

            self.entries["MKEY"].delete(0, "end")
            self.entries["MKEY"].insert(0, new_val)

            h = hashlib.sha256(raw).hexdigest()[:8].upper()
            self.preview_labels["MKEY"].configure(text=f"Decoded length: {len(raw)} bytes | SHA256: {h}...", text_color="#66FF99")
            self._log(f"🔄 Converted MKEY ({direction})", "success")

        except Exception as e:
            self.preview_labels["MKEY"].configure(text="⚠️ Invalid MKEY", text_color="#FF6666")
            self._log(f"❌ Conversion failed: {e}", "error")


    def _derive_key_field(self, key_name):
        """Derive BLE_ID or PATIENT_BLE_PWD → PBKDF2-HMAC-SHA256."""
        from keys_helpers import derive_key_hex
        val = self.entries[key_name].get().strip()
        if not val:
            messagebox.showwarning("Missing Value", f"Enter {key_name} first.")
            return
        try:
            derived = derive_key_hex(val).upper()
            self.entries[key_name].delete(0, "end")
            self.entries[key_name].insert(0, derived)
            self._log(f"🔐 Derived {key_name} → PBKDF2-HMAC-SHA256", "success")
        except Exception as e:
            self._log(f"❌ Derivation failed: {e}", "error")

    def _save_single_key(self, key_name):
        """Save any individual key entry as a .bin file."""
        val = self.entries[key_name].get().strip()
        sn = self.sn_entry.get().strip() or "UNKNOWN_SN"
        if not val:
            self._log(f"⚠️ Cannot save empty {key_name}.", "error")
            return

        folder = filedialog.askdirectory(title=f"Select folder to save {key_name}")
        if not folder:
            return

        path = os.path.join(folder, f"{key_name}_{sn}.bin")
        try:
            if all(c in "0123456789ABCDEFabcdef" for c in val) and len(val) % 2 == 0:
                data = bytes.fromhex(val)
            else:
                data = val.encode("utf-8")

            with open(path, "wb") as f:
                f.write(data)

            self._log(f"💾 Saved {key_name} → {path}", "success")
        except Exception as e:
            self._log(f"❌ Save failed for {key_name}: {e}", "error")


    # ───────────────────────────────────────────────
    # LIVE VALIDATION FOR ALL FIELDS
    # ───────────────────────────────────────────────
    def _validate_key_live(self, key_name: str):
        """Validate and show short hash previews for all key fields."""
        import hashlib, base64
        val = self.entries[key_name].get().strip()
        label = self.preview_labels[key_name]

        if not val:
            label.configure(text="")
            return

        try:
            # Determine decoding logic
            if key_name == "PKEY":
                # Try Base36 or Hex
                if all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in val.upper()) and len(val) < 50:
                    raw = int(val, 36).to_bytes(32, "big")
                else:
                    raw = bytes.fromhex(val)
            elif key_name == "MKEY":
                raw = base64.b64decode(val)
            else:
                # BLE_ID and PATIENT_BLE_PWD → PBKDF2 derived 32 bytes
                from keys_helpers import derive_key_bytes
                raw = derive_key_bytes(val)

            # Compute SHA256 + length
            h = hashlib.sha256(raw).hexdigest().upper()[:8]
            label.configure(
                text=f"Decoded length: {len(raw)} bytes | SHA256: {h}...",
                text_color="#66FF99",
            )

        except Exception:
            label.configure(text="⚠️ Invalid format", text_color="#FF6666")


    def _clear_pkey_preview(self):
        """Legacy helper — safe to keep for backward compatibility."""
        self.preview_labels["PKEY"].configure(text="")


    def _toggle_keys(self):
        self.keys_visible = not self.keys_visible
        if self.keys_visible:
            self.keys_inner.grid()
        else:
            self.keys_inner.grid_remove()


if __name__ == "__main__":
    app = FPDApp()
    app.mainloop()
