# ─────────────────────────────────────────────────────────────
#  gui.py — Fetch Production Data (FPD) Tool  
#  Author: Boris Eldar
#  Description:
#     Modern CustomTkinter GUI for fetching GLD device production
#     data from SAP, verifying and normalizing certificates,
#     generating QR codes, and saving PEM files.
# ─────────────────────────────────────────────────────────────

import os
import platform
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Local imports
from version import VERSION
from sap_api import fetch_keys, fetch_certs
from qr_generator import generate_qr_from_sn
from certificate_utils import (
    verify_cert_pair,
    save_cert_files,
    normalize_pem_string,
)

# ─────────────────────────────────────────────────────────────
#  GUI SETUP
# ─────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FPDApp(ctk.CTk):
    """Main window for the Fetch Production Data tool."""

    def __init__(self):
        super().__init__()

        # Force Windows title bar dark mode
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)),
                ctypes.sizeof(ctypes.c_int(1))
            )
        except Exception as e:
            print("⚠️ Could not set dark titlebar:", e)

        # Window properties
        self.title(f"🔧 Fetch Production Data (FPD)  {VERSION}")
        self.geometry("1150x720")
        self.resizable(False, False)

        # Internal state
        self.current_sn = ""
        self.sap_data = {}
        self.status_color = "gray"

        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Build UI
        self._build_header()
        self._build_device_frame()
        self._build_sap_card()
        self._build_cert_card()
        self._build_log_frame()
        self._build_status_led()

        # Log startup info
        self.after(200, self._log_startup_info)

    # ─────────────── HEADER ───────────────
    def _build_header(self):
        header = ctk.CTkLabel(
            self,
            text=f"Fetch Production Data (FPD) {VERSION}",
            font=("Segoe UI", 26, "bold")
        )
        header.grid(row=0, column=0, pady=(10, 0))

        info_btn = ctk.CTkButton(
            self, text="ℹ️ Info", width=60, command=self._show_info
        )
        info_btn.place(x=1050, y=15)

    # ─────────────── DEVICE INPUT ───────────────
    def _build_device_frame(self):
        self.device_frame = ctk.CTkFrame(self, corner_radius=15)
        self.device_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            self.device_frame,
            text="Device Serial Number (SN):",
            font=("Segoe UI", 14)
        ).grid(row=0, column=0, padx=10, pady=10)

        self.sn_entry = ctk.CTkEntry(
            self.device_frame,
            width=220,
            placeholder_text="Enter SN or load YAML"
        )
        self.sn_entry.grid(row=0, column=1, padx=10, pady=10)

        yaml_btn = ctk.CTkButton(
            self.device_frame, text="📂 Load YAML", command=self._load_yaml
        )
        yaml_btn.grid(row=0, column=2, padx=5)

        fetch_btn = ctk.CTkButton(
            self.device_frame,
            text="🛰️ Fetch from SAP",
            fg_color="#0078ff",
            hover_color="#3399ff",
            command=self._fetch_from_sap
        )
        fetch_btn.grid(row=0, column=3, padx=5)

    # ─────────────── SAP DATA PANEL ───────────────
    def _build_sap_card(self):
        self.sap_card = ctk.CTkFrame(self, corner_radius=15)
        self.sap_card.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.sap_card.grid_remove()  # hidden initially

        self.sap_title = ctk.CTkLabel(
            self.sap_card, text="SAP Data ▾", font=("Segoe UI", 18, "bold")
        )
        self.sap_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.sap_info = ctk.CTkTextbox(self.sap_card, height=100, width=800)
        self.sap_info.grid(row=1, column=0, padx=10, pady=(0, 10))
        self.sap_info.insert("end", "Waiting for SAP fetch...\n")
        self.sap_info.configure(state="disabled")

    # ─────────────── CERTIFICATE PANEL ───────────────
    def _build_cert_card(self):
        self.cert_card = ctk.CTkFrame(self, corner_radius=15)
        self.cert_card.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.cert_card.grid_remove()  # hidden until SAP data arrives

        self.cert_title = ctk.CTkLabel(
            self.cert_card,
            text="Certificate Tools ▾",
            font=("Segoe UI", 18, "bold")
        )
        self.cert_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        btn_frame = ctk.CTkFrame(self.cert_card)
        btn_frame.grid(row=1, column=0, pady=10)

        self.verify_btn = ctk.CTkButton(
            btn_frame,
            text="🔒 Verify Certificate",
            width=180,
            command=self._verify_certificate
        )
        self.verify_btn.grid(row=0, column=0, padx=10)

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save PEMs",
            width=150,
            command=self._save_pems
        )
        self.save_btn.grid(row=0, column=1, padx=10)

        self.qr_btn = ctk.CTkButton(
            btn_frame,
            text="🔳 Generate QR",
            width=150,
            command=self._generate_qr
        )
        self.qr_btn.grid(row=0, column=2, padx=10)

        self.cert_status_label = ctk.CTkLabel(
            self.cert_card,
            text="Status: Not verified",
            text_color="orange",
            font=("Segoe UI", 14)
        )
        self.cert_status_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    # ─────────────── ACTIVITY LOG ───────────────
    def _build_log_frame(self):
        self.log_frame = ctk.CTkFrame(self, corner_radius=15)
        self.log_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="nsew")

        ctk.CTkLabel(
            self.log_frame,
            text="📜 Activity Log",
            font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.log_box = ctk.CTkTextbox(self.log_frame, width=1080, height=250, corner_radius=10)
        self.log_box.grid(row=1, column=0, padx=10, pady=5)
        self.log_box.configure(state="disabled")

    # ─────────────── STATUS LED ───────────────
    def _build_status_led(self):
        self.led_canvas = ctk.CTkCanvas(self, width=20, height=20, bg="#1a1a1a", highlightthickness=0)
        self.led = self.led_canvas.create_oval(5, 5, 15, 15, fill="gray")
        self.led_canvas.place(x=1110, y=685)

    # ─────────────── LOGGING UTILS ───────────────
    def log_msg(self, level, msg):
        """Write color-coded message to the activity log."""
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        emoji = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️", "debug": "🧩"}.get(level, "ℹ️")
        color = {
            "success": "#00b050",
            "error": "#ff4040",
            "warning": "#ffa500",
            "info": "#3a8bff",
            "debug": "#808080"
        }.get(level, "white")

        line = f"{timestamp}{emoji} {msg}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.tag_add(level, "end-2l", "end-1l")
        self.log_box.tag_config(level, foreground=color)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")
        self._update_led(level)

    def _update_led(self, level):
        color = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "yellow",
            "debug": "gray"
        }.get(level, "gray")
        self.led_canvas.itemconfig(self.led, fill=color)

    # ─────────────── STARTUP LOG INFO ───────────────
    def _log_startup_info(self):
        self.log_msg("debug", f"🧩 Launching Fetch Production Data (FPD) ({VERSION})")
        self.log_msg("debug", f"💻 Platform : {platform.system()} {platform.release()}")
        self.log_msg("debug", f"🐍 Python   : {platform.python_version()}")
        self.log_msg("debug", f"📂 Working  : {os.getcwd()}")
        self.log_msg("debug", "──────────────────────────────────────────────")

    # ─────────────── BUTTON ACTIONS ───────────────
    def _load_yaml(self):
        yaml_path = filedialog.askopenfilename(title="Select YAML", filetypes=[("YAML Files", "*.yaml")])
        if not yaml_path:
            self.log_msg("warning", "YAML load cancelled.")
            return
        sn = os.path.basename(yaml_path).split(".")[0]
        self.sn_entry.delete(0, "end")
        self.sn_entry.insert(0, sn)
        self.log_msg("success", f"Loaded SN from YAML: {sn}")

    def _fetch_from_sap(self):
        """Fetch production data (keys + certs) from SAP."""
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showwarning("Missing SN", "Please enter a Serial Number or load from YAML.")
            self.log_msg("error", "Fetch failed – no SN provided.")
            return

        self.log_msg("info", f"Fetching SAP data for SN={sn} ...")
        try:
            keys = fetch_keys(sn)
            try:
                certs = fetch_certs(sn)
                self.sap_data = {**keys, **certs}
                self.log_msg("success", f"SAP data (with PEM) received for {sn}")
            except Exception as e:
                self.sap_data = keys
                self.log_msg("warning", f"No certificate fields in SAP: {e}")

            self.sap_card.grid()
            self.cert_card.grid()
            self._display_sap_data(self.sap_data)

        except Exception as e:
            self.log_msg("error", f"Failed to fetch from SAP: {e}")

    def _display_sap_data(self, data):
        """Display SAP data in textbox."""
        self.sap_info.configure(state="normal")
        self.sap_info.delete("1.0", "end")
        for key, val in data.items():
            short = val if len(val) < 120 else val[:117] + "..."
            self.sap_info.insert("end", f"{key}: {short}\n")
        self.sap_info.configure(state="disabled")

    def _verify_certificate(self):
        """Verify/normalize certificate pair."""
        self.log_msg("info", "Verifying certificate data...")
        try:
            cert_pem = self.sap_data.get("AUTH_PUBLIC_KEY", "")
            key_pem  = self.sap_data.get("AUTH_PRIVATE_KEY", "")

            if not cert_pem or not key_pem:
                self.cert_status_label.configure(
                    text="Status: Missing PEM ❌", text_color="#ff4040"
                )
                self.log_msg("warning", "No PEM certificate fields in SAP data — skipping verification.")
                return

            # ❗ Pass raw SAP strings — normalization happens inside verify_cert_pair
            verified = verify_cert_pair(cert_pem, key_pem)

            if verified:
                self.cert_status_label.configure(text="Status: Verified ✅", text_color="#00b050")
                self.log_msg("success", "Certificate verified successfully.")
            else:
                self.cert_status_label.configure(text="Status: Invalid ❌", text_color="#ff4040")
                self.log_msg("error", "Certificate verification failed.")

        except Exception as e:
            self.log_msg("error", f"Verification error: {e}")



    def _save_pems(self):
        """Save PEM files locally."""
        out_dir = filedialog.askdirectory(title="Select output folder for PEM files")
        if not out_dir:
            self.log_msg("warning", "Save cancelled by user.")
            return
        try:
            save_cert_files(self.sap_data, out_dir)
            self.log_msg("success", f"PEM files saved successfully to: {out_dir}")
        except Exception as e:
            self.log_msg("error", f"PEM save failed: {e}")

    def _generate_qr(self):
        """Generate QR code for SN."""
        if not self.current_sn:
            self.current_sn = self.sn_entry.get().strip()
        if not self.current_sn:
            self.log_msg("error", "Cannot generate QR — SN missing.")
            return
        try:
            qr_path = generate_qr_from_sn(self.current_sn)
            self.log_msg("success", f"QR code generated at: {qr_path}")
        except Exception as e:
            self.log_msg("error", f"QR generation failed: {e}")

    def _show_info(self):
        """Show tool information popup."""
        messagebox.showinfo(
            "Tool Information",
            "Fetch Production Data (FPD) Tool\n\n"
            "Functions:\n"
            "• Fetch SAP keys & certificates\n"
            "• Normalize and verify PEM data\n"
            "• Save PEM files & generate QR\n\n"
            f"Developed by Boris Eldar — {VERSION}"
        )


# ─────────────── APP ENTRY POINT ───────────────
if __name__ == "__main__":
    app = FPDApp()
    app.mainloop()
