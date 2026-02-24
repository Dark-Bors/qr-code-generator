# gui.py — Fetch Production Data (FPD)
# Author: Boris Eldar
# (Refactored to MVC - View)

# gui.py
import tkinter as tk
import logging
from tkinter import filedialog, messagebox, BooleanVar, StringVar
import threading
import platform
import threading
import platform
import os
from datetime import datetime
from typing import Optional

import customtkinter as ctk
from PIL import Image

from version import VERSION
# Controller
from fpd_controller import FPDController


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

        # Initialize Controller
        self.controller = FPDController(log_callback=self._log_direct)

        # UI State
        self.qr_rtv = BooleanVar(value=True)
        self.qr_newton = BooleanVar(value=True)
        self.qr_davinci = BooleanVar(value=True)
        self.qr_custom_rtv = BooleanVar(value=False)
        self.qr_custom_patient = BooleanVar(value=False)
        self.custom_rtv = StringVar(value="")
        self.custom_patient = StringVar(value="")

        # Build UI
        self._build_ui()
        self.after(300, self._log_env)
        
    def _log_direct(self, msg: str, level: str = "info"):
        """Callback for controller to log messages."""
        self._log(msg, level)

    def _show_info(self):
        """Display detailed app, algorithm, and QR structure information."""
        info_text = (
            f"🔧  Fetch Production Data (FPD) {VERSION}\n"
            "───────────────────────────────\n"
            "Architecture: MVC Pattern\n"
            "Author: Boris Eldar\n"
            "───────────────────────────────\n\n"

            "🧮  Cryptographic Algorithms:\n"
            "• PKEY  →  Base36 (50 chars) ↔ 32 bytes (little-endian)\n"
            "• MKEY  →  Base64 ↔ 32 bytes\n"
            "• BLE Keys → PBKDF2-HMAC-SHA256 (Salt: ...3513A, 310k iter)\n"
            "• Checksums → ISO 7064 Mod 11,10 (SN) & Mod 37,36 (BLE)\n\n"

            "🚀  New Features (v4.3):\n"
            "• Batch Processing: Process multiple SNs from .txt file\n"
            "• History Log: Track and reopen last 50 jobs\n\n"

            "🔗  QR Code Profiles:\n"
            "• Newton/Davinci: IoT Cloud URLs (EU Central)\n"
            "• RTV/Patient: Custom payloads with checksums\n\n"
            
            "💡 Tip: Use 'Batch Processing' tab for bulk operations."
        )
        messagebox.showinfo("About FPD Tool", info_text)

    # ────────────────────── UI BUILDERS ──────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Log panel expands
        
        self._build_header()

        # Tab View
        self.tabs = ctk.CTkTabview(self, width=1140, height=550)
        self.tabs.grid(row=1, column=0, padx=20, pady=5)
        self.tabs.add("Single Device")
        self.tabs.add("Batch Processing")
        self.tabs.add("History")
        self.tabs.add("Settings")
        self.tabs.add("Step 2")        

        # Single Device Tab
        self.step2_tab = self.tabs.tab("Step 2")
        self.step2_tab.grid_columnconfigure(0, weight=1)
        self._build_step2_panel(self.step2_tab)

        # Single Device Tab
        self.single_tab = self.tabs.tab("Single Device")
        self.single_tab.grid_columnconfigure(0, weight=1)
        self._build_device_panel(self.single_tab)
        # self._build_cert_panel(self.single_tab) # Hidden
        self._build_keys_panel(self.single_tab)
        self._build_qr_panel(self.single_tab)

        # Batch Tab
        self.batch_tab = self.tabs.tab("Batch Processing")
        self.batch_tab.grid_columnconfigure(0, weight=1)
        self._build_batch_panel(self.batch_tab)

        # History Tab
        self.hist_tab = self.tabs.tab("History")
        self.hist_tab.grid_columnconfigure(0, weight=1)
        self.hist_tab.grid_rowconfigure(0, weight=1)
        self._build_history_panel(self.hist_tab)

        # Settings Tab
        self.settings_tab = self.tabs.tab("Settings")
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(1, weight=1)
        self._build_settings_panel(self.settings_tab)

        # Log Panel (Global)
        self._build_log_panel()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text=f"Fetch Production Data (FPD) {VERSION}",
            font=("Segoe UI", 28, "bold"),
        ).grid(row=0, column=0, pady=10)
        
        ctk.CTkButton(self, text="ℹ️ Info", width=80, command=self._show_info)\
            .place(x=1060, y=25)

    def _build_device_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Device Serial Number:", font=("Segoe UI", 14)).grid(
            row=0, column=0, padx=10, pady=10
        )
        self.sn_entry = ctk.CTkEntry(frame, width=200)
        self.sn_entry.grid(row=0, column=1, padx=5)
        # Live Validation Binding
        self.sn_entry.bind("<KeyRelease>", self._validate_sn_live)

        ctk.CTkButton(frame, text="🛰️ Fetch SAP Data", command=self._on_fetch_sap).grid(
            row=0, column=2, padx=10
        )
        ctk.CTkButton(
            frame, text="💾 Verify & Save All", command=self._on_verify_save_all
        ).grid(row=0, column=3, padx=10)

        ctk.CTkButton(
            frame, text="⚡ Auto-Run", fg_color="purple", command=self._on_auto_run
        ).grid(row=0, column=4, padx=10)

    def _build_keys_panel(self, parent):
        self.keys_frame = ctk.CTkFrame(parent)
        self.keys_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

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
            ctk.CTkLabel(self.keys_inner, text=f"{f}:", font=("Segoe UI", 13)).grid(
                row=i, column=0, sticky="w", padx=5, pady=3
            )
            entry = ctk.CTkEntry(self.keys_inner, width=360)
            entry.grid(row=i, column=1, padx=5, pady=3)
            # Live Validation (View logic)
            entry.bind("<KeyRelease>", lambda e, k=f: self._validate_key_live(k))
            self.entries[f] = entry

            self.preview_labels[f] = ctk.CTkLabel(self.keys_inner, text="", font=("Consolas", 10))
            self.preview_labels[f].grid(row=i, column=1, sticky="s", pady=(0, 4))

            # Save Button
            ctk.CTkButton(
                self.keys_inner, text="💾 Save", width=80,
                command=lambda k=f: self._on_save_single_key(k)
            ).grid(row=i, column=2, padx=5)

            # Convert/Derive buttons
            if f == "PKEY":
                ctk.CTkButton(self.keys_inner, text="⇄ Convert PKEY", width=140, command=self._on_convert_pkey)\
                    .grid(row=i, column=3, padx=5)
            elif f == "MKEY":
                ctk.CTkButton(self.keys_inner, text="⇄ Convert MKEY", width=140, command=self._on_convert_mkey)\
                    .grid(row=i, column=3, padx=5)
            elif f in ("BLE_ID", "PATIENT_BLE_PWD"):
                ctk.CTkButton(self.keys_inner, text="➡️ Derive Key", width=140, command=lambda k=f: self._on_derive_key(k))\
                    .grid(row=i, column=3, padx=5)

            ctk.CTkButton(self.keys_inner, text="⚙️ Fill All", command=self._on_fill_all)\
                .grid(row=0, column=4, padx=10, pady=(4,0))

        self.keys_visible = True

    def _build_qr_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame, text="QR Code Options", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        ctk.CTkCheckBox(frame, text="RTV", variable=self.qr_rtv).grid(row=1, column=0, sticky="w", padx=20)
        ctk.CTkCheckBox(frame, text="Newton", variable=self.qr_newton).grid(row=1, column=1, sticky="w", padx=20)
        ctk.CTkCheckBox(frame, text="Davinci", variable=self.qr_davinci).grid(row=1, column=2, sticky="w", padx=20)
        ctk.CTkCheckBox(frame, text="Custom RTV", variable=self.qr_custom_rtv).grid(row=1, column=3, sticky="w", padx=20)
        ctk.CTkCheckBox(frame, text="Custom Patient App", variable=self.qr_custom_patient).grid(row=1, column=4, sticky="w", padx=20)

        # Custom inputs
        ctk.CTkLabel(frame, text="Custom RTV:", font=("Segoe UI", 13)).grid(row=2, column=0, sticky="w", padx=20)
        self.custom_rtv_entry = ctk.CTkEntry(frame, textvariable=self.custom_rtv, width=800)
        self.custom_rtv_entry.grid(row=2, column=1, columnspan=4, padx=10, pady=5)

        ctk.CTkLabel(frame, text="Custom Patient App:", font=("Segoe UI", 13)).grid(row=3, column=0, sticky="w", padx=20)
        self.custom_patient_entry = ctk.CTkEntry(frame, textvariable=self.custom_patient, width=800)
        self.custom_patient_entry.grid(row=3, column=1, columnspan=4, padx=10, pady=5)

        ctk.CTkButton(frame, text="🔳 Generate QR Codes", command=self._on_generate_qrs).grid(
            row=4, column=0, padx=20, pady=10, sticky="w"
        )
    
    def _build_step2_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Step 2: Keys & RTV QR", font=("Segoe UI", 20, "bold")).pack(pady=10)

        # SN Entry
        sn_frame = ctk.CTkFrame(frame)
        sn_frame.pack(fill="x", padx=40, pady=10)
        ctk.CTkLabel(sn_frame, text="Device Serial Number:", font=("Segoe UI", 14)).pack(side="left", padx=10)
        self.step2_sn = ctk.CTkEntry(sn_frame, width=200)
        self.step2_sn.pack(side="left", padx=5)

        ctk.CTkButton(sn_frame, text="⚡ Generate & Fetch", command=self._on_step2_run).pack(side="left", padx=20)

        # Results Panel
        self.step2_results = ctk.CTkFrame(frame)
        self.step2_results.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = ["PKEY", "MKEY", "Key 3 (BLE_ID Derived)"]
        self.step2_entries = {}
        
        for i, f in enumerate(fields):
            row = ctk.CTkFrame(self.step2_results)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=f"{f}:", width=150, anchor="e").pack(side="left", padx=10)
            entry = ctk.CTkEntry(row, width=600)
            entry.pack(side="left", padx=5)
            # Make readonly later? For now editable or just for show.
            self.step2_entries[f] = entry

        # RTV String
        row_rtv = ctk.CTkFrame(self.step2_results)
        row_rtv.pack(fill="x", pady=5)
        ctk.CTkLabel(row_rtv, text="RTV String:", width=150, anchor="e").pack(side="left", padx=10)
        self.step2_rtv_str = ctk.CTkEntry(row_rtv, width=600)
        self.step2_rtv_str.pack(side="left", padx=5)
        
        # Output info
        self.step2_status = ctk.CTkLabel(frame, text="", text_color="green", font=("Segoe UI", 12))
        self.step2_status.pack(pady=10)


    def _build_batch_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Batch Processing", font=("Segoe UI", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Process a list of SNs from a text file (one SN per line).", font=("Segoe UI", 14)).pack(pady=5)
        
        # File picking
        self.batch_file_path = StringVar()
        f_frame = ctk.CTkFrame(frame)
        f_frame.pack(fill="x", padx=40, pady=10)
        ctk.CTkLabel(f_frame, text="SN List File (.txt):").pack(side="left", padx=10)
        ctk.CTkEntry(f_frame, textvariable=self.batch_file_path, width=400).pack(side="left", padx=5)
        ctk.CTkButton(f_frame, text="📂 Browse", width=80, command=self._select_batch_file).pack(side="left", padx=5)
        
        
        # Start Button
        self.btn_start_batch = ctk.CTkButton(frame, text="🚀 Start Batch Process", height=50, font=("Segoe UI", 16, "bold"), fg_color="green", command=self._on_start_batch)
        self.btn_start_batch.pack(pady=20)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(frame, width=600)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_label = ctk.CTkLabel(frame, text="Ready")
        self.progress_label.pack()
        
        ctk.CTkLabel(frame, text="Note: QRs will use options checked in the 'Single Device' tab.").pack(pady=10)

    def _build_history_panel(self, parent):
        # Refresh Button
        ctk.CTkButton(parent, text="🔄 Refresh History", command=self._refresh_history).pack(pady=10)
        
        # Scrollable Frame for items
        self.hist_list = ctk.CTkScrollableFrame(parent, width=1000, height=400)
        self.hist_list.pack(fill="both", expand=True, padx=20, pady=10)
        self._refresh_history()

    def _build_settings_panel(self, parent):
        ctk.CTkLabel(parent, text="⚙️ Configuration (config.yaml)", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=10)
        
        self.config_text = ctk.CTkTextbox(parent, width=1000, height=400, font=("Consolas", 12))
        self.config_text.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Load Config content text
        import yaml
        cfg = self.controller.get_config()
        self.config_text.insert("0.0", yaml.dump(cfg, default_flow_style=False))
        
        ctk.CTkButton(parent, text="💾 Save Configuration", command=self._on_save_settings).grid(row=2, column=0, pady=10)

    def _on_save_settings(self):
        import yaml
        try:
            raw = self.config_text.get("0.0", "end")
            new_cfg = yaml.safe_load(raw)
            self.controller.save_config(new_cfg)
            messagebox.showinfo("Settings", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Settings Error", f"Invalid YAML: {e}")

    def _refresh_history(self):
        # Clear old
        for widget in self.hist_list.winfo_children():
            widget.destroy()
            
        hist = self.controller.get_history()
        if not hist:
            ctk.CTkLabel(self.hist_list, text="No history yet.").pack(pady=20)
            return
            
        for i, item in enumerate(hist):
            row = ctk.CTkFrame(self.hist_list)
            row.pack(fill="x", padx=5, pady=2)
            
            txt = f"[{item['timestamp']}] SN: {item['sn']}"
            ctk.CTkLabel(row, text=txt, font=("Consolas", 12)).pack(side="left", padx=10)
            
            path = item['path']
            ctk.CTkButton(row, text="📂 Open", width=60, 
                          command=lambda p=path: os.startfile(p) if platform.system() == "Windows" else None)\
                .pack(side="right", padx=10)

    def _build_log_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew") # Row 2 because of Tabs
        ctk.CTkLabel(frame, text="📜 Activity Log", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=10
        )
        self.log_box = ctk.CTkTextbox(frame, width=1120, height=200)
        self.log_box.grid(row=1, column=0, padx=10, pady=10)
        self.log_box.configure(state="disabled")

    # ────────────────────── EVENT HANDLERS ──────────────────────
    def _on_fetch_sap(self):
        sn = self.sn_entry.get().strip()
        if not sn:
            messagebox.showwarning("Missing SN", "Enter a serial number.")
            return
        
        try:
            data = self.controller.fetch_sap_data(sn)
            # Update UI
            for field in ("PKEY", "MKEY", "BLE_ID", "PATIENT_BLE_PWD"):
                val = data.get(field, "")
                if field in self.entries:
                    self.entries[field].delete(0, "end")
                    self.entries[field].insert(0, val)
        except Exception:
            pass # Controller logs the error

    def _on_verify_save_all(self):
        sn = self.sn_entry.get().strip()
        base = filedialog.askdirectory(title="Select root folder")
        if not sn or not base:
            return
        self.controller.verify_and_save_all(sn, base)

    def _on_auto_run(self):
        sn = self.sn_entry.get().strip()
        base = filedialog.askdirectory(title="Select Output Folder")
        if not sn or not base:
            return
            
        options = {
            "rtv": self.qr_rtv.get(),
            "newton": self.qr_newton.get(),
            "davinci": self.qr_davinci.get(),
            "custom_rtv_enabled": self.qr_custom_rtv.get(),
            "custom_rtv_text": self.custom_rtv.get(),
            "custom_patient_enabled": self.qr_custom_patient.get(),
            "custom_patient_text": self.custom_patient.get()
        }
        
        try:
            folder = self.controller.auto_run(sn, base, options)
            if platform.system() == "Windows":
                os.startfile(folder)
        except Exception:
            pass # Logged by controller

    def _on_generate_qrs(self):
        sn = self.sn_entry.get().strip()
        base = filedialog.askdirectory(title="Select folder for QR output")
        if not sn or not base:
            return
            
        keys = {
            "BLE_ID": self.entries["BLE_ID"].get(),
            "PATIENT_BLE_PWD": self.entries["PATIENT_BLE_PWD"].get()
        }
        options = {
            "rtv": self.qr_rtv.get(),
            "newton": self.qr_newton.get(),
            "davinci": self.qr_davinci.get(),
            "custom_rtv_enabled": self.qr_custom_rtv.get(),
            "custom_rtv_text": self.custom_rtv.get(),
            "custom_patient_enabled": self.qr_custom_patient.get(),
            "custom_patient_text": self.custom_patient.get()
        }
        
        self.controller.generate_qrs(sn, keys, options, base)

    def _on_save_single_key(self, key_name):
        val = self.entries[key_name].get().strip()
        sn = self.sn_entry.get().strip()
        folder = filedialog.askdirectory(title=f"Save {key_name}")
        self.controller.save_single_key(key_name, val, sn, folder)

    def _on_convert_pkey(self):
        try:
            curr = self.entries["PKEY"].get()
            new_val, msg = self.controller.convert_pkey(curr)
            self.entries["PKEY"].delete(0, "end")
            self.entries["PKEY"].insert(0, new_val)
            self._log(f"🔄 Converted PKEY ({msg})", "success")
        except Exception as e:
            self._log(f"❌ {e}", "error")

    def _on_convert_mkey(self):
        try:
            curr = self.entries["MKEY"].get()
            new_val, msg = self.controller.convert_mkey(curr)
            self.entries["MKEY"].delete(0, "end")
            self.entries["MKEY"].insert(0, new_val)
            self._log(f"🔄 Converted MKEY ({msg})", "success")
        except Exception as e:
            self._log(f"❌ {e}", "error")

    def _on_derive_key(self, key_name):
        curr = self.entries[key_name].get().strip()
        if not curr: return
        try:
            res = self.controller.derive_key(curr)
            self.entries[key_name].delete(0, "end")
            self.entries[key_name].insert(0, res)
            self._log(f"🔐 Derived {key_name} → PBKDF2", "success")
        except Exception as e:
            self._log(f"❌ {e}", "error")

    def _on_fill_all(self):
        # Fill from Config via Controller logic or direct load
        # For MVC, controller usually holds this data
        data = self.controller.autofill_data
        if not data: return
        
        if data.get("sn"):
            self.sn_entry.delete(0, "end")
            self.sn_entry.insert(0, data["sn"])
            
        for key in ("PKEY", "MKEY", "BLE_ID", "PATIENT_BLE_PWD"):
            self.entries[key].delete(0, "end")
            self.entries[key].insert(0, data.get(key, ""))
            
        self._log("⚙️ Autofilled fields.", "info")

    def _select_batch_file(self):
        path = filedialog.askopenfilename(title="Select SN List", filetypes=[("Text Files", "*.txt")])
        if path:
            self.batch_file_path.set(path)
            
    def _on_start_batch(self):
        fpath = self.batch_file_path.get()
        if not fpath:
            messagebox.showwarning("No File", "Please select a text file with Serial Numbers.")
            return
            
        base = filedialog.askdirectory(title="Select Output Folder for Batch")
        if not base: return
        
        # Gather options (must do this in main thread)
        options = {
            "rtv": self.qr_rtv.get(),
            "newton": self.qr_newton.get(),
            "davinci": self.qr_davinci.get(),
            "custom_rtv_enabled": self.qr_custom_rtv.get(),
            "custom_rtv_text": self.custom_rtv.get(),
            "custom_patient_enabled": self.qr_custom_patient.get(),
            "custom_patient_text": self.custom_patient.get()
        }
        
        # Disable button
        self.btn_start_batch.configure(state="disabled", text="Processing... ⏳")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting...")
        
        # Run in thread
        t = threading.Thread(target=self._run_batch_thread, args=(fpath, base, options))
        t.start()
        
    def _run_batch_thread(self, fpath, base, options):
        def update_prog(curr, total):
            # Schedule UI update on main thread
            val = curr / total if total > 0 else 0
            self.after(0, lambda: self.progress_bar.set(val))
            self.after(0, lambda: self.progress_label.configure(text=f"Processing {curr}/{total}"))

        try:
            summary = self.controller.batch_process_file(fpath, base, options, progress_callback=update_prog)
            self.after(0, lambda: self._on_batch_complete(summary))
        except Exception as e:
            self.after(0, lambda: self._on_batch_error(str(e)))
            
    def _on_step2_run(self):
        sn = self.step2_sn.get().strip()
        if not sn:
            messagebox.showwarning("Missing SN", "Please enter a Serial Number.")
            return

        base = filedialog.askdirectory(title="Select Output Folder for Step 2")
        if not base: return
        
        try:
            # 1. Fetch SAP Data
            data = self.controller.fetch_sap_data(sn)
            
            # 2. Update Basic Fields
            self.step2_entries["PKEY"].delete(0, "end")
            self.step2_entries["PKEY"].insert(0, data.get("PKEY", ""))
            
            self.step2_entries["MKEY"].delete(0, "end")
            self.step2_entries["MKEY"].insert(0, data.get("MKEY", ""))

            # 3. Derive Key 3
            ble_id = data.get("BLE_ID", "")
            key3_val = ""
            if ble_id:
                try:
                    # Using controller helper
                    key3_val = self.controller.derive_key(ble_id)
                    # Also save it? The requirement says "create a key_3 ... as in main gui"
                    # Main GUI saves it. Implementation plan said "Ensure key3...bin exists".
                except Exception as e:
                    self._log(f"Key 3 derivation error: {e}", "error")

            self.step2_entries["Key 3 (BLE_ID Derived)"].delete(0, "end")
            self.step2_entries["Key 3 (BLE_ID Derived)"].insert(0, key3_val)

            # 4. Generate RTV QR Only
            # Build keys dict for controller
            keys = {
                "BLE_ID": ble_id,
                "PATIENT_BLE_PWD": data.get("PATIENT_BLE_PWD", "")
            }
            options = {
                "rtv": True,
                "newton": False,
                "davinci": False,
                "custom_rtv_enabled": False,
                "custom_patient_enabled": False
            }
            
            # Use dedicated Step 2 save method to avoid padding/certificate errors
            saved_folder = self.controller.save_step2_data(sn, base)
            
            # Now Generate QR
            self.controller.generate_qrs(sn, keys, options, saved_folder)
            
            # 5. Get RTV String to display
            # Re-calculate it here or ask controller? Controller calculates it inside generate_qrs but doesn't return it.
            # We can re-calculate it for display.
            from algorithms import mod_11_10, calc_check_digit
            sn_check = mod_11_10(sn)
            sn_full = f"{sn}{sn_check}"
            
            ble_id_full = ""
            if ble_id:
                c1 = calc_check_digit(ble_id.lower())
                ble_id_full = f"{ble_id}{c1.upper()}"
            
            rtv_str = f"bleSerial:{sn_full};blePassword:{ble_id_full};name:Patient;govId:123456789"
            self.step2_rtv_str.delete(0, "end")
            self.step2_rtv_str.insert(0, rtv_str)
            
            self.step2_status.configure(text=f"✅ Success! Saved to: {os.path.basename(saved_folder)}")
            messagebox.showinfo("Step 2 Complete", f"Keys and RTV QR generated in:\n{saved_folder}")

        except Exception as e:
            self.step2_status.configure(text=f"❌ Error: {e}", text_color="red")
            messagebox.showerror("Step 2 Error", str(e))

    def _on_batch_complete(self, summary):
        self.btn_start_batch.configure(state="normal", text="🚀 Start Batch Process")
        self.progress_label.configure(text="Done!")
        msg = (f"Batch Complete!\n\n"
               f"Total: {summary['total']}\n"
               f"✅ Success: {summary['success']}\n"
               f"❌ Failed: {summary['failed']}")
        messagebox.showinfo("Batch Report", msg)

    def _on_batch_error(self, err_msg):
        self.btn_start_batch.configure(state="normal", text="🚀 Start Batch Process")
        messagebox.showerror("Batch Error", err_msg)

    def _validate_sn_live(self, event):
        sn = self.sn_entry.get()
        if not sn:
            self.sn_entry.configure(border_color=["#979DA2", "#565B5E"]) # Default
            return
            
        is_valid = self.controller.validate_sn_format(sn)
        if is_valid:
            self.sn_entry.configure(border_color="#00b050") # Green
        else:
            self.sn_entry.configure(border_color="#ff4040") # Red

    # ────────────────────── UI HELPERS ──────────────────────
    def _log(self, msg: str, level: str = "info"):
        colors = {"info": "#3a8bff", "success": "#00b050", "error": "#ff4040"}
        ts = datetime.now().strftime("[%H:%M:%S] ")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{ts}{msg}\n", level)
        self.log_box.tag_config(level, foreground=colors.get(level, "white"))
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _log_env(self):
        self._log(f"🧩 MVC Refactored App ({VERSION}) Launched", "info")
        self._log(f"🐍 Python: {platform.python_version()}", "info")

    def _toggle_keys(self):
        self.keys_visible = not self.keys_visible
        if self.keys_visible:
            self.keys_inner.grid()
        else:
            self.keys_inner.grid_remove()

    def _validate_key_live(self, key_name):
        # Keep lightweight validation in UI or move to controller?
        # For instant feedback, keeping it here is fine, OR call a static validation helper.
        # Implemented simplified version here for brevity
        import hashlib, base64
        from keys_helpers import derive_key_bytes
        
        val = self.entries[key_name].get().strip()
        label = self.preview_labels[key_name]
        if not val:
            label.configure(text="")
            return
            
        try:
            # Reimplementing lightweight check or importing helpers?
            # Ideally, we import helpers.
            raw = b""
            if key_name == "PKEY":
                 if all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in val.upper()) and len(val) < 50:
                    raw = int(val, 36).to_bytes(32, "big")
                 else:
                    raw = bytes.fromhex(val)
            elif key_name == "MKEY":
                 raw = base64.b64decode(val)
            else:
                 raw = derive_key_bytes(val)
            
            h = hashlib.sha256(raw).hexdigest().upper()[:8]
            label.configure(text=f"SHA256: {h}...", text_color="#66FF99")
        except:
             label.configure(text="Invalid", text_color="#FF6666")

if __name__ == "__main__":
    app = FPDApp()
    app.mainloop()
