# gui.py
import os, base64, random, time, tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import shutil

import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from converters import (
    pkey_base36_to_bytes32, bytes32_to_pkey_base36,
    mkey_base64_to_bytes32, bytes32_to_base64,
)
from keys_helpers import derive_key_hex, derive_key_bytes
from sap_api import fetch_keys, fetch_certs
from algorithms import mod_11_10, calc_check_digit
from qr_generator import generate_qr_code
from utils import save_screenshot, load_yaml_sn, load_cloud_profiles, load_autofill

APP_VERSION = "v3.0.0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CA_FILENAME = "AWS_StarfieldCA_C2_And_G2.pem"
CA_PATH = Path(__file__).with_name(CA_FILENAME)


# -------------------------- tiny tooltip --------------------------
class _ToolTip(tk.Toplevel):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.label = tk.Label(
            self, text=text, justify="left",
            background="#333333", foreground="white",
            relief="solid", borderwidth=1, padx=6, pady=4,
            font=("Segoe UI", 9)
        )
        self.label.pack()
        self.withdraw()

def attach_tooltip(widget, text: str):
    tip = _ToolTip(widget, text)
    def show(_e):
        tip.deiconify()
        x = widget.winfo_rootx() + 10
        y = widget.winfo_rooty() + widget.winfo_height() + 6
        tip.wm_geometry(f"+{x}+{y}")
    def hide(_e):
        tip.withdraw()
    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)


# -------------------------- main app --------------------------
class QRCodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Fetching Production Data and QR generator {APP_VERSION}")
        self.geometry("1280x980")

        self.prod_dir = None  # created only by “Fetch keys from SAP”

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.cloud_profiles, self.default_profile = load_cloud_profiles()

        self._build_topbar(self.scroll)
        self._build_qr_controls(self.scroll)
        self._build_keys_panel(self.scroll)
        self._build_status(self.scroll)   # log above
        self._build_qr_area(self.scroll)  # qr string + image below

        self.cloud_profile_var.set(self.default_profile)
        self._apply_cloud_profile()

    # ---------------------------- UI ----------------------------
    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent)
        bar.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(bar, text="SN:").pack(side="left", padx=(8, 4))
        self.sn_entry = ctk.CTkEntry(bar, width=220)
        self.sn_entry.pack(side="left")

        ctk.CTkButton(bar, text="SN from .yaml", command=self._load_sn_from_yaml)\
            .pack(side="left", padx=6)

        ctk.CTkButton(bar, text="Download certificates (SAP)", command=self._download_certs_only)\
            .pack(side="right", padx=6)

        self.fetch_btn = ctk.CTkButton(bar, text="Fetch keys from SAP", command=self._fetch_from_sap)
        self.fetch_btn.pack(side="right", padx=6)

        ctk.CTkButton(bar, text="Fill All", command=self._fill_all)\
            .pack(side="right", padx=6)

    def _build_qr_controls(self, parent):
        frm = ctk.CTkFrame(parent)
        frm.pack(fill="x", pady=6)

        # Left cluster: QR type + step
        left = ctk.CTkFrame(frm); left.grid(row=0, column=0, sticky="nw", padx=6, pady=6)
        ctk.CTkLabel(left, text="QR Type:").grid(row=0, column=0, sticky="w")
        self.qr_type = tk.StringVar(value="Kit QR")
        ctk.CTkRadioButton(left, text="Kit QR", value="Kit QR", variable=self.qr_type)\
            .grid(row=0, column=1, padx=4)
        ctk.CTkRadioButton(left, text="HCP QR", value="HCP QR", variable=self.qr_type)\
            .grid(row=0, column=2, padx=4)
        ctk.CTkLabel(left, text="Step:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.step = tk.StringVar(value="RTV")
        ctk.CTkRadioButton(left, text="RTV", value="RTV", variable=self.step)\
            .grid(row=1, column=1, padx=4, pady=(6,0))
        ctk.CTkRadioButton(left, text="Patient App", value="Patient App", variable=self.step)\
            .grid(row=1, column=2, padx=4, pady=(6,0))

        # Middle cluster: BLE / name / govid
        mid = ctk.CTkFrame(frm); mid.grid(row=0, column=1, sticky="nw", padx=6, pady=6)
        ctk.CTkLabel(mid, text="BLE Password:").grid(row=0, column=0, sticky="w")
        self.ble_entry = ctk.CTkEntry(mid, width=220); self.ble_entry.grid(row=0, column=1, padx=6)
        ctk.CTkLabel(mid, text="Patient Name:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.pname_entry = ctk.CTkEntry(mid, width=220); self.pname_entry.grid(row=1, column=1, padx=6, pady=(6,0))
        ctk.CTkLabel(mid, text="GovID:").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.govid_entry = ctk.CTkEntry(mid, width=220); self.govid_entry.grid(row=2, column=1, padx=6, pady=(6,0))

        # Right cluster: cloud profile radios + entries
        right = ctk.CTkFrame(frm); right.grid(row=0, column=2, sticky="nw", padx=6, pady=6)
        self.cloud_profile_var = tk.StringVar(value="davinci")
        ctk.CTkLabel(right, text="Cloud Profile:").grid(row=0, column=0, sticky="w")
        ctk.CTkRadioButton(right, text="newton", value="newton", variable=self.cloud_profile_var,
                           command=self._apply_cloud_profile).grid(row=0, column=1, padx=4)
        ctk.CTkRadioButton(right, text="davinci", value="davinci", variable=self.cloud_profile_var,
                           command=self._apply_cloud_profile).grid(row=0, column=2, padx=4)
        ctk.CTkRadioButton(right, text="manual", value="manual", variable=self.cloud_profile_var,
                           command=self._apply_cloud_profile).grid(row=0, column=3, padx=4)
        ctk.CTkLabel(right, text="Cloud URL:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.cloud_entry = ctk.CTkEntry(right, width=480); self.cloud_entry.grid(row=1, column=1, columnspan=3, padx=6, pady=(8,0))
        ctk.CTkLabel(right, text="MQTT Prefix:").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.mqtt_entry = ctk.CTkEntry(right, width=480); self.mqtt_entry.grid(row=2, column=1, columnspan=3, padx=6, pady=(6,0))

        # Actions row
        ctk.CTkButton(frm, text="Generate QR Code", command=self._generate_qr)\
            .grid(row=1, column=0, padx=6, pady=(10,0), sticky="we")
        ctk.CTkButton(frm, text="Save Screenshot", command=lambda: save_screenshot(self))\
            .grid(row=1, column=1, padx=6, pady=(10,0), sticky="we")
        # ctk.CTkButton(frm, text="Copy String", command=self._copy_string)\
        #     .grid(row=1, column=2, padx=6, pady=(10,0), sticky="we")

    def _build_keys_panel(self, parent):
        panel = ctk.CTkFrame(parent); panel.pack(fill="x", pady=6)

        # ------------------- Key 1 (PKEY) -------------------
        ctk.CTkLabel(panel, text="Key_1 (PKEY, Base36 from SAP)").grid(row=0, column=0, sticky="w")
        self.pkey_long = ctk.CTkEntry(panel, width=420, placeholder_text="Base36 (50 chars)")
        self.pkey_long.grid(row=0, column=1, padx=6, pady=4)
        ctk.CTkLabel(panel, text="Short (ASCII if printable, else hex)").grid(row=0, column=2, sticky="w")
        self.pkey_short = ctk.CTkEntry(panel, width=420); self.pkey_short.grid(row=0, column=3, padx=6, pady=4)
        attach_tooltip(self.pkey_short,
            "Key_1 Short shows the raw 32 bytes.\n"
            "If bytes are printable ASCII (e.g., 'aaaaaaaa…'), you see ASCII.\n"
            "Otherwise it shows 64-hex.\n"
            "Use Short→Long to convert back to Base36.")

        # Button row (aligned): Long→Short | Short→Long | Upload
        ctk.CTkButton(panel, text="Long→Short", command=self._pkey_long_to_short)\
            .grid(row=1, column=1, sticky="w", padx=6, pady=(0,8))
        ctk.CTkButton(panel, text="Short→Long", command=self._pkey_short_to_long)\
            .grid(row=1, column=2, sticky="w", padx=6, pady=(0,8))
        ctk.CTkButton(panel, text="Upload", command=self._upload_pkey_bin)\
            .grid(row=1, column=3, sticky="w", padx=6, pady=(0,8))

        # ------------------- Key 2 (MKEY) -------------------
        ctk.CTkLabel(panel, text="Key_2 (MKEY, Base64 from SAP)").grid(row=2, column=0, sticky="w")
        self.mkey_long = ctk.CTkEntry(panel, width=420, placeholder_text="Base64 (32 bytes)")
        self.mkey_long.grid(row=2, column=1, padx=6, pady=4)
        ctk.CTkLabel(panel, text="Short (ASCII if printable, else hex)").grid(row=2, column=2, sticky="w")
        self.mkey_short = ctk.CTkEntry(panel, width=420); self.mkey_short.grid(row=2, column=3, padx=6, pady=4)
        attach_tooltip(self.mkey_short,
            "Key_2 Short shows the raw 32 bytes (ASCII if printable, else 64-hex).\n"
            "Long field holds canonical Base64 from SAP.\n"
            "Use Short→Long to encode to Base64.")

        # Button row (aligned): Long→Short | Short→Long | Upload
        ctk.CTkButton(panel, text="Long→Short", command=self._mkey_long_to_short)\
            .grid(row=3, column=1, sticky="w", padx=6, pady=(0,8))
        ctk.CTkButton(panel, text="Short→Long", command=self._mkey_short_to_long)\
            .grid(row=3, column=2, sticky="w", padx=6, pady=(0,8))
        ctk.CTkButton(panel, text="Upload", command=self._upload_mkey_bin)\
            .grid(row=3, column=3, sticky="w", padx=6, pady=(0,8))

        # ------------------- Key 3 / Key 4 (derived only) -------------------
        ctk.CTkLabel(panel, text="Key_3 BLE_ID").grid(row=4, column=0, sticky="w", pady=(6,0))
        self.ble_id_entry = ctk.CTkEntry(panel, width=220)
        self.ble_id_entry.grid(row=4, column=1, sticky="w", padx=6, pady=(6,4))
        ctk.CTkLabel(panel, text="Derived Hex").grid(row=4, column=2, sticky="w", pady=(6,0))
        self.key3_hex = ctk.CTkEntry(panel, width=420)
        self.key3_hex.grid(row=4, column=3, sticky="w", padx=6, pady=(6,4))
        attach_tooltip(self.key3_hex,
            "Key_3 is PBKDF2-HMAC-SHA256 (salted, 310k rounds).\n"
            "It is one-way: derived Hex cannot be reversed to BLE_ID.")

        ctk.CTkLabel(panel, text="Key_4 PATIENT_BLE_PWD").grid(row=5, column=0, sticky="w")
        self.pble_entry = ctk.CTkEntry(panel, width=220)
        self.pble_entry.grid(row=5, column=1, sticky="w", padx=6, pady=4)
        ctk.CTkLabel(panel, text="Derived Hex").grid(row=5, column=2, sticky="w")
        self.key4_hex = ctk.CTkEntry(panel, width=420)
        self.key4_hex.grid(row=5, column=3, sticky="w", padx=6, pady=4)
        attach_tooltip(self.key4_hex,
            "Key_4 is PBKDF2-HMAC-SHA256 (salted, 310k rounds).\n"
            "It is one-way: derived Hex cannot be reversed to PATIENT_BLE_PWD.")

        # Actions for keys/certs
        ctk.CTkButton(panel, text="Save certificates", command=self._save_certs_button)\
            .grid(row=6, column=1, sticky="w", padx=6, pady=(4,6))
        ctk.CTkButton(panel, text="Save keys (.bin)", command=self._save_all_keys)\
            .grid(row=6, column=3, sticky="e", padx=6, pady=(4,6))

    def _build_qr_area(self, parent):
        self.output = ctk.CTkTextbox(parent, width=1100, height=100, wrap=tk.WORD)
        self.output.pack(pady=(4,10))
        self.qr_frame = ctk.CTkFrame(parent); self.qr_frame.pack(pady=(0,10))
        self.qr_label = ctk.CTkLabel(self.qr_frame, text=""); self.qr_label.pack()

    def _build_status(self, parent):
        self.status = ctk.CTkTextbox(parent, width=1100, height=120)
        self.status.pack(pady=(0,8))
        self._log("Ready.")

    # -------------------------- helpers --------------------------
    def _ts(self) -> str:
        return time.strftime("%Y%m%d-%H%M%S")

    def _log(self, msg: str):
        self.status.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.status.see(tk.END)

    def _apply_cloud_profile(self):
        key = self.cloud_profile_var.get()
        prof = self.cloud_profiles.get(key, {})
        url  = prof.get("cloudUrl", "")
        mqtt = prof.get("mqttPrefix", "")
        editable = (key == "manual")
        state = "normal" if editable else "disabled"
        self.cloud_entry.configure(state="normal"); self.cloud_entry.delete(0, tk.END); self.cloud_entry.insert(0, url)
        self.mqtt_entry.configure(state="normal");  self.mqtt_entry.delete(0, tk.END);  self.mqtt_entry.insert(0, mqtt)
        self.cloud_entry.configure(state=state); self.mqtt_entry.configure(state=state)

    def _pick_qr_save_dir(self, sn: str) -> str | None:
        # If a Production folder exists (created by Fetch), save under Production/QR-Code
        if self.prod_dir and os.path.isdir(self.prod_dir):
            qr_dir = os.path.join(self.prod_dir, "QR-Code")
            os.makedirs(qr_dir, exist_ok=True)
            return qr_dir
        # Otherwise ask the user where to save
        return filedialog.askdirectory(title="Choose folder to save the QR files (PNG + TXT)") or None

    def _ensure_prod_dir(self, sn: str) -> str:
        base_dir = filedialog.askdirectory(title="Choose destination folder for Production data")
        if not base_dir:
            raise RuntimeError("User canceled folder selection.")
        self.prod_dir = os.path.join(base_dir, f"Production_data_{sn}_{self._ts()}")
        os.makedirs(self.prod_dir, exist_ok=True)
        self._log(f"Created folder: {self.prod_dir}")
        return self.prod_dir

    def _choose_labeled_dir(self, sn: str, label: str) -> str:
        base = filedialog.askdirectory(title=f"Choose destination for {label}")
        if not base:
            raise RuntimeError("User canceled folder selection.")
        out = os.path.join(base, f"{label}_{sn}_{self._ts()}")
        os.makedirs(out, exist_ok=True)
        self._log(f"Created folder: {out}")
        return out

    def _one_line_with_escapes(self, s: str) -> str:
        return s.replace("\r\n", "\n").replace("\n", "\\n")

    def _normalize_pem(self, s: str) -> str:
        if "\\n" in s and "\n" not in s:
            s = s.replace("\\r\\n", "\n").replace("\\n", "\n")
        return s.replace("\r\n", "\n").strip() + ("\n" if not s.endswith("\n") else "")

    def _save_certs_files(self, sn: str, certs: dict, out_dir: str):
        pub_raw = certs.get("AUTH_PUBLIC_KEY", "")
        prv_raw = certs.get("AUTH_PRIVATE_KEY", "")
        # 1) raw one-liner with literal \n
        with open(os.path.join(out_dir, f"cert_string_{sn}.txt"), "w", encoding="utf-8") as f:
            f.write(self._one_line_with_escapes(pub_raw))
        # 2) proper PEM .crt
        with open(os.path.join(out_dir, f"{sn}-certificate.pem.crt"), "w", encoding="utf-8") as f:
            f.write(self._normalize_pem(pub_raw))
        # 3) proper PEM .key
        with open(os.path.join(out_dir, f"{sn}-private.pem.key"), "w", encoding="utf-8") as f:
            f.write(self._normalize_pem(prv_raw))
        # Root CA (project local)
        if CA_PATH.exists():
            try:
                shutil.copy(str(CA_PATH), os.path.join(out_dir, CA_FILENAME))
                self._log(f"{CA_FILENAME} copied.")
            except Exception as e:
                self._log(f"Warning: could not copy Root CA: {e}")
        legacy = Path(__file__).with_name("AmazonRootCA.pem")
        if legacy.exists():
            try:
                shutil.copy(str(legacy), os.path.join(out_dir, "AmazonRootCA.pem"))
                self._log("AmazonRootCA.pem copied.")
            except Exception as e:
                self._log(f"Warning: could not copy AmazonRootCA.pem: {e}")

    def _save_keys_files(self, sn: str, out_dir: str, pkey_raw: bytes, mkey_raw: bytes,
                         k3_raw: bytes, k4_raw: bytes):
        with open(os.path.join(out_dir, f"pkey_{sn}.bin"), "wb") as f: f.write(pkey_raw)
        with open(os.path.join(out_dir, f"mkey_{sn}.bin"), "wb") as f: f.write(mkey_raw)
        with open(os.path.join(out_dir, f"key3_{sn}.bin"), "wb") as f: f.write(k3_raw)
        with open(os.path.join(out_dir, f"key4_{sn}.bin"), "wb") as f: f.write(k4_raw)
        with open(os.path.join(out_dir, "keys_2_3_4.bin"), "wb") as f: f.write(mkey_raw + k3_raw + k4_raw)

    # ---------- short helpers ----------
    def _bytes_to_ascii_if_printable(self, raw: bytes) -> str | None:
        try:
            s = raw.decode("ascii")
        except UnicodeDecodeError:
            return None
        if all(32 <= b <= 126 for b in raw):
            return s
        return None

    def _short_str_to_bytes32(self, s: str) -> bytes:
        """Parse a 'short' value back to raw bytes (accept ASCII32, hex64, Base64)."""
        s = s.strip()
        if not s:
            raise ValueError("Short value is empty.")
        # ASCII 32
        if len(s) == 32 and all(32 <= ord(ch) <= 126 for ch in s):
            return s.encode("ascii")
        # hex 64
        if len(s) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in s):
            raw = bytes.fromhex(s)
            if len(raw) != 32:
                raise ValueError("Hex did not decode to 32 bytes.")
            return raw
        # Base64
        raw = base64.b64decode(s, validate=False)
        if len(raw) != 32:
            raise ValueError("Base64 did not decode to 32 bytes.")
        return raw

    # -------------------------- Actions --------------------------
    def _fill_all(self):
        """Strict YAML autofill. Regenerate govId on every Fill if YAML has empty/blank.
        Accept BLE_ID / ble_id / bleId variants (same for PATIENT_BLE_PWD).
        """
        data = load_autofill()
        if not data:
            messagebox.showerror("Autofill", "No 'autofill' block found in config.yaml.")
            self._log("No 'autofill' block in config.yaml.")
            return

        # clear fields
        for e in (self.sn_entry, self.ble_entry, self.pname_entry, self.govid_entry,
                  self.pkey_long, self.pkey_short, self.mkey_long, self.mkey_short,
                  self.ble_id_entry, self.key3_hex, self.pble_entry, self.key4_hex):
            e.delete(0, tk.END)

        sn      = data.get("sn")
        name    = data.get("patientName")
        gov_raw = (data.get("govId") or "").strip() if isinstance(data.get("govId"), str) else data.get("govId")
        pkey    = data.get("PKEY")
        mkey    = data.get("MKEY")

        # Accept common variants for BLE_ID and PATIENT_BLE_PWD
        def _pick(d, *keys):
            for k in keys:
                if k in d and d[k] not in (None, ""):
                    return d[k]
            return None

        ble_id = _pick(data, "BLE_ID", "ble_id", "bleId", "bleID")
        pble   = _pick(data, "PATIENT_BLE_PWD", "patient_ble_pwd", "patientBlePwd", "patientBLEPWD")
        ble_pw = data.get("blePassword")

        if sn:      self.sn_entry.insert(0, str(sn))
        if name:    self.pname_entry.insert(0, str(name))
        if ble_pw:  self.ble_entry.insert(0, str(ble_pw))

        # GovID: generate if blank/missing
        if not gov_raw:
            gov = "".join(str(random.randint(0, 9)) for _ in range(9))
            self.govid_entry.insert(0, gov)
            self._log("govId blank in YAML -> generated a new 9-digit value.")
        else:
            self.govid_entry.insert(0, str(gov_raw))

        # Key_1 and Key_2 via the same helpers as buttons
        if pkey:
            self._set_key1_from_long(pkey)
        if mkey:
            self._set_key2_from_long(mkey)

        # Key_3 / Key_4 (derived) + mirror BLE Password = BLE_ID
        if ble_id:
            self.ble_id_entry.insert(0, ble_id)
            self.ble_entry.delete(0, tk.END); self.ble_entry.insert(0, ble_id)
            try:
                self.key3_hex.insert(0, derive_key_hex(ble_id))
            except Exception as e:
                self._log(f"Warn: Key_3 derivation failed: {e}")
        if pble:
            self.pble_entry.insert(0, pble)
            try:
                self.key4_hex.insert(0, derive_key_hex(pble))
            except Exception as e:
                self._log(f"Warn: Key_4 derivation failed: {e}")

        self.prod_dir = None
        self._log("Fields filled from YAML (autofill).")

    def _load_sn_from_yaml(self):
        self.sn_entry.delete(0, tk.END)
        sn = load_yaml_sn()
        if sn:
            self.sn_entry.insert(0, sn)
            self._log("SN loaded from YAML.")

    def _fetch_from_sap(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showerror("Missing SN", "Enter a Serial Number first."); return
        self.fetch_btn.configure(state="disabled")
        try:
            rec = fetch_keys(sn)
            self._log("Fetched keys from SAP.")

            # Fill BLE + mirror BLE Password
            self.ble_id_entry.delete(0, tk.END);  self.ble_id_entry.insert(0, rec["BLE_ID"])
            self.ble_entry.delete(0, tk.END);     self.ble_entry.insert(0, rec["BLE_ID"])

            # Fill Key_1/Key_2 using the SAME helpers as the buttons
            self._set_key1_from_long(rec["PKEY"])
            self._set_key2_from_long(rec["MKEY"])

            # Keep raw bytes for saving .bin
            pkey_raw = pkey_base36_to_bytes32(rec["PKEY"])
            mkey_raw = mkey_base64_to_bytes32(rec["MKEY"])

            # Derived keys (Key_3 / Key_4)
            k3_raw = derive_key_bytes(rec["BLE_ID"])
            self.key3_hex.delete(0, tk.END); self.key3_hex.insert(0, k3_raw.hex())
            k4_raw = derive_key_bytes(rec["PATIENT_BLE_PWD"])
            self.key4_hex.delete(0, tk.END); self.key4_hex.insert(0, k4_raw.hex())

            # Save everything to Production_data
            out_dir = self._ensure_prod_dir(sn)
            self._save_keys_files(sn, out_dir, pkey_raw, mkey_raw, k3_raw, k4_raw)
            self._log("Keys saved into Production_data.")
            certs = fetch_certs(sn)
            self._log("Fetched certificates from SAP.")
            self._save_certs_files(sn, certs, out_dir)
            self._log("Certificates saved into Production_data.")
            messagebox.showinfo("Done", f"All production data saved in:\n{out_dir}")

        except Exception as e:
            messagebox.showerror("SAP Error", str(e))
            self._log(f"Fetch failed: {e}")
        finally:
            self.fetch_btn.configure(state="normal")

    def _download_certs_only(self):
        self._save_certs_button()

    def _save_certs_button(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showerror("Missing SN", "Enter a Serial Number first."); return
        try:
            certs = fetch_certs(sn)
            out_dir = self._choose_labeled_dir(sn, "certificates")
            self._save_certs_files(sn, certs, out_dir)
            messagebox.showinfo("Saved", f"Certificates saved in:\n{out_dir}")
            self._log("Certificates saved (standalone).")
        except Exception as e:
            messagebox.showerror("SAP Error", str(e))
            self._log(f"Save certificates failed: {e}")

    # ------- Key1 converters & upload -------
    def _pkey_long_to_short(self):
        self._set_key1_from_long(self.pkey_long.get().strip())

    def _pkey_short_to_long(self):
        try:
            raw = self._short_str_to_bytes32(self.pkey_short.get())
            self.pkey_long.delete(0, tk.END); self.pkey_long.insert(0, bytes32_to_pkey_base36(raw))
        except Exception as e:
            messagebox.showerror("Key_1", f"Short→Long failed: {e}")

    def _upload_pkey_bin(self):
        raw = self._read_32_from_file("Select Key_1 (PKEY) .bin")
        if raw is None: return
        ascii32 = self._bytes_to_ascii_if_printable(raw)
        self.pkey_short.delete(0, tk.END); self.pkey_short.insert(0, ascii32 if ascii32 is not None else raw.hex())
        try:
            self.pkey_long.delete(0, tk.END); self.pkey_long.insert(0, bytes32_to_pkey_base36(raw))
        except Exception as e:
            self._log(f"Note: could not back-fill PKEY Base36: {e}")

    # ------- Key2 converters & upload -------
    def _mkey_long_to_short(self):
        self._set_key2_from_long(self.mkey_long.get().strip())

    def _mkey_short_to_long(self):
        try:
            raw = self._short_str_to_bytes32(self.mkey_short.get())
            self.mkey_long.delete(0, tk.END); self.mkey_long.insert(0, bytes32_to_base64(raw))
        except Exception as e:
            messagebox.showerror("Key_2", f"Short→Long failed:\n{e}")

    def _upload_mkey_bin(self):
        raw = self._read_32_from_file("Select Key_2 (MKEY) .bin")
        if raw is None: return
        ascii32 = self._bytes_to_ascii_if_printable(raw)
        self.mkey_short.delete(0, tk.END); self.mkey_short.insert(0, ascii32 if ascii32 is not None else raw.hex())
        self.mkey_long.delete(0, tk.END);  self.mkey_long.insert(0, bytes32_to_base64(raw))

    # ------- shared read + save -------
    def _read_32_from_file(self, title: str) -> bytes | None:
        path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if not path: return None
        try:
            with open(path, "rb") as f:
                raw = f.read()
            if len(raw) != 32:
                raise ValueError(f"File has {len(raw)} bytes; expected 32.")
            return raw
        except Exception as e:
            messagebox.showerror("File error", str(e))
            return None

    def _save_all_keys(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showerror("Missing SN", "Enter a Serial Number first."); return
        try:
            pkey_raw = pkey_base36_to_bytes32(self.pkey_long.get().strip())
            mkey_raw = mkey_base64_to_bytes32(self.mkey_long.get().strip())
            k3_raw = bytes.fromhex(self.key3_hex.get().strip()) if self.key3_hex.get().strip() else derive_key_bytes(self.ble_id_entry.get().strip())
            k4_raw = bytes.fromhex(self.key4_hex.get().strip()) if self.key4_hex.get().strip() else derive_key_bytes(self.pble_entry.get().strip())
        except Exception as e:
            messagebox.showerror("Build keys", f"Error preparing keys: {e}")
            return

        try:
            out_dir = self._choose_labeled_dir(sn, "keys")
        except RuntimeError:
            return

        try:
            self._save_keys_files(sn, out_dir, pkey_raw, mkey_raw, k3_raw, k4_raw)
            messagebox.showinfo("Saved", f"Keys saved in:\n{out_dir}")
            self._log("Keys saved (standalone).")
        except Exception as e:
            messagebox.showerror("Save error", str(e))
            self._log(f"Save error: {e}")

    # ------- QR -------
    def _ble_with_checksum_upper(self, ble: str) -> str:
        if not ble: return ""
        return ble + calc_check_digit(ble.lower()).upper()

    def _qr_tag(self) -> str:
        if self.qr_type.get() == "Kit QR":
            return "KIT"
        return self.step.get().replace(" ", "")

    def _generate_qr(self):
        sn = self.sn_entry.get().strip()
        ble = self.ble_entry.get().strip()
        cloud = self.cloud_entry.get().strip()
        mqtt  = self.mqtt_entry.get().strip()
        name  = self.pname_entry.get().strip()
        govid = self.govid_entry.get().strip()
        key1_short = self.pkey_short.get().strip()

        if not sn:
            messagebox.showerror("Missing", "SN is required."); return

        sn_full  = sn + mod_11_10(sn)
        ble_full = self._ble_with_checksum_upper(ble) if ble else ""

        if self.qr_type.get() == "HCP QR":
            if self.step.get() == "Patient App":
                if not (ble and cloud and mqtt):
                    messagebox.showerror("Missing", "BLE, Cloud URL and MQTT Prefix are required for Patient App."); return
                result = f"bleSerial:{sn_full};blePassword:{ble_full};cloudUrl:{cloud};mqttPrefix:{mqtt}"
            else:
                if not (ble and name and govid):
                    messagebox.showerror("Missing", "BLE, Patient Name and GovID are required for HCP RTV."); return
                result = f"bleSerial:{sn_full};blePassword:{ble_full};name:{name};govId:{govid}"
        else:
            # Key_1 must be Base64(32) in the QR payload; convert from short (ASCII/hex/Base64) to Base64
            try:
                raw = self._short_str_to_bytes32(key1_short)
            except Exception:
                messagebox.showerror("Key_1", "Key_1 short must be 32 bytes in ASCII/HEX/Base64 form."); return
            key1_b64 = bytes32_to_base64(raw)
            if not ble:
                messagebox.showerror("Missing", "BLE Password is required for Kit QR."); return
            result = f"21{sn_full}\\^]91{ble_full}\\^]92{key1_b64}\\^]"

        self.output.delete("1.0", tk.END); self.output.insert(tk.END, result)

        img = generate_qr_code(result).convert("RGBA")
        ctk_img = CTkImage(light_image=img, size=(500, 500))
        self.qr_label.configure(image=ctk_img, text=""); self.qr_label.image = ctk_img

        save_dir = self._pick_qr_save_dir(sn)
        if not save_dir:
            self._log("QR save canceled by user."); return
        ts  = self._ts()
        tag = self._qr_tag()
        base = f"QR_{tag}_{sn}_{ts}"
        png_path = os.path.join(save_dir, f"{base}.png")
        txt_path = os.path.join(save_dir, f"{base}.txt")
        try:
            img.save(png_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(result)
            self._log(f"QR saved: {os.path.basename(png_path)}, {os.path.basename(txt_path)}")
        except Exception as e:
            self._log(f"Warning: could not save QR assets: {e}")

    # ------- long→short helpers (used by buttons, Fill, Fetch) -------
    def _set_key1_from_long(self, b36: str):
        """Fill Key_1 fields from Base36 (SAP) using the exact same logic everywhere."""
        self.pkey_long.delete(0, tk.END)
        self.pkey_short.delete(0, tk.END)
        if not b36:
            return
        try:
            raw = pkey_base36_to_bytes32(b36)
            self.pkey_long.insert(0, b36)  # keep SAP long as-is
            ascii32 = self._bytes_to_ascii_if_printable(raw)
            self.pkey_short.insert(0, ascii32 if ascii32 is not None else raw.hex())
        except Exception as e:
            self._log(f"Key_1 set-from-long failed: {e}")

    def _set_key2_from_long(self, b64: str):
        """Fill Key_2 fields from Base64 (SAP) using the exact same logic everywhere."""
        self.mkey_long.delete(0, tk.END)
        self.mkey_short.delete(0, tk.END)
        if not b64:
            return
        try:
            raw = mkey_base64_to_bytes32(b64)
            self.mkey_long.insert(0, bytes32_to_base64(raw))  # canonical
            ascii32 = self._bytes_to_ascii_if_printable(raw)
            self.mkey_short.insert(0, ascii32 if ascii32 is not None else raw.hex())
        except Exception as e:
            self._log(f"Key_2 set-from-long failed: {e}")

    def _copy_string(self):
        s = self.output.get("1.0", tk.END)
        self.clipboard_clear(); self.clipboard_append(s)
        messagebox.showinfo("Copied", "QR String copied to clipboard!")


if __name__ == "__main__":
    app = QRCodeApp()
    app.mainloop()
