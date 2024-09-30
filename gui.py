import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
from algorithms import mod_11_10, calc_check_digit
from qr_generator import generate_qr_code
from utils import save_screenshot, load_yaml_sn
from converters import decode_base36_to_bytes, encode_bytes_to_base36_50chars
from converters import calc_check_digit, mod_11_10

import random
import yaml

class QRCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator v1.0")
        
        # Set the initial size of the app window
        self.root.geometry("650x580")

        # Load Azure theme
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Azure-ttk-theme", "azure.tcl")
        if os.path.exists(r"C:\Users\eldarb2\OneDrive - Medtronic PLC\Boris_Automation\Azure-ttk-theme\azure.tcl"):
            self.root.tk.call("source", r"C:\Users\eldarb2\OneDrive - Medtronic PLC\Boris_Automation\Azure-ttk-theme\azure.tcl")
            self.root.tk.call("set_theme", "dark")  # You can also use "light" here if you want a light theme

        # Add canvas and scrollbar for scrolling support
        self.canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self.enable_mouse_wheel_scrolling()

        # Create Toggle for Kit QR and HCP QR
        self.toggle_var = tk.StringVar(value="Kit QR")
        self.create_toggle()

        # Fill All Button at the top right in the first row
        self.fill_all_btn = ttk.Button(self.toggle_frame, text="Fill All", command=self.fill_all_fields)
        self.fill_all_btn.pack(side="right", padx=5, anchor="e")
        
        # Create Form Inputs
        self.create_form()

        # Placeholder for QR Code Image Label
        self.qr_label = None

    def enable_mouse_wheel_scrolling(self):
        # Scroll canvas vertically with mouse wheel
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        
        # For macOS, you may need to use these bindings
        self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)

    def on_mouse_wheel(self, event):
        # Windows and Linux scrolling
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # macOS scrolling
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def create_toggle(self):
        self.toggle_frame = ttk.Frame(self.scrollable_frame)
        self.toggle_frame.pack(pady=10)
        
        ttk.Label(self.toggle_frame, text="QR Type:").pack(side="left", padx=5)
        
        self.kit_qr = ttk.Radiobutton(self.toggle_frame, text="Kit QR", value="Kit QR", variable=self.toggle_var)
        self.hcp_qr = ttk.Radiobutton(self.toggle_frame, text="HCP QR", value="HCP QR", variable=self.toggle_var)
        
        self.kit_qr.pack(side="left", padx=5)
        self.hcp_qr.pack(side="left", padx=5)

    def create_form(self):
        self.form_frame = ttk.Frame(self.scrollable_frame)
        self.form_frame.pack(pady=10)

        ttk.Label(self.form_frame, text="Enter GLD SN:").grid(row=0, column=0, sticky="w")
        self.sn_field = ttk.Entry(self.form_frame)
        self.sn_field.grid(row=0, column=1)
        
        # Button to load SN from .yaml file
        self.load_yaml_btn = ttk.Button(self.form_frame, text="SN from .yaml", command=self.load_sn_from_yaml)
        self.load_yaml_btn.grid(row=0, column=3)
        
        ttk.Label(self.form_frame, text="Enter BLE Password:").grid(row=1, column=0, sticky="w")
        self.ble_password_field = ttk.Entry(self.form_frame)
        self.ble_password_field.grid(row=1, column=1)

        ttk.Label(self.form_frame, text="Patient Name:").grid(row=2, column=0, sticky="w")
        self.patient_name_field = ttk.Entry(self.form_frame)
        self.patient_name_field.grid(row=2, column=1)
        
        ttk.Label(self.form_frame, text="Patient Family Name:").grid(row=3, column=0, sticky="w")
        self.family_field = ttk.Entry(self.form_frame)
        self.family_field.grid(row=3, column=1)
        
        ttk.Label(self.form_frame, text="Patient govID:").grid(row=4, column=0, sticky="w")
        self.id_field = ttk.Entry(self.form_frame)
        self.id_field.grid(row=4, column=1)

        ttk.Label(self.form_frame, text="Key 1:").grid(row=5, column=0, sticky="w")
        self.key1_field = ttk.Entry(self.form_frame)
        self.key1_field.grid(row=5, column=1)
        
        # Upload Key_1 Button
        self.upload_key_btn = ttk.Button(self.form_frame, text="Upload Key_1", command=self.upload_key1_bin)
        self.upload_key_btn.grid(row=5, column=3)
        
        # Convert to Base36 Button
        self.convert_base36_btn = ttk.Button(self.form_frame, text="Convert to Base36", command=self.convert_to_base36)
        self.convert_base36_btn.grid(row=6, column=3, pady=10)

        # RadioButtons for RTV and Patient App
        self.step_var = tk.StringVar(value="None")
        self.rtv_radio = ttk.Radiobutton(self.form_frame, text="RTV", value="RTV", variable=self.step_var)
        self.patient_radio = ttk.Radiobutton(self.form_frame, text="Patient App", value="Patient App", variable=self.step_var)
        
        self.rtv_radio.grid(row=6, column=0, pady=5)
        self.patient_radio.grid(row=6, column=1, pady=5)
        
        # Generate QR Button
        self.generate_qr_btn = ttk.Button(self.form_frame, text="Generate QR Code", command=self.generate_qr_code)
        self.generate_qr_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Save Button
        self.save_btn = ttk.Button(self.form_frame, text="Save Screenshot", command=self.save_screenshot_handler)
        self.save_btn.grid(row=8, column=0, columnspan=2, pady=10)

        # Copy String Button
        self.copy_btn = ttk.Button(self.form_frame, text="Copy String", command=self.copy_string_handler)
        self.copy_btn.grid(row=8, column=2, columnspan=2, pady=10)

        # Add a Text widget to display the output string
        self.output_text = tk.Text(self.form_frame, height=5, wrap=tk.WORD)
        self.output_text.grid(row=9, column=0, columnspan=4, padx=15, pady=15)

        # Enable mouse right-click copy/paste
        self.enable_copy_paste()



    def fill_all_fields(self):
        # Fill the fields with the given values
        self.sn_field.delete(0, tk.END)
        self.sn_field.insert(0, "259710800")

        self.ble_password_field.delete(0, tk.END)
        self.ble_password_field.insert(0, "ABCDEFGHIJ")

        self.patient_name_field.delete(0, tk.END)
        self.patient_name_field.insert(0, "Test")

        self.family_field.delete(0, tk.END)
        self.family_field.insert(0, "Num")

        self.id_field.delete(0, tk.END)
        self.id_field.insert(0, ''.join([str(random.randint(0, 9)) for _ in range(9)]))  # Random 9-digit govID

        self.key1_field.delete(0, tk.END)
        self.key1_field.insert(0, "2FDIU7I6KPZX4H9QOS6EQLDJGHD2UT5HX0E8BEKM0BKWIAX3DT")

    def load_sn_from_yaml(self):
        self.sn_field.delete(0, tk.END)
        sn = load_yaml_sn()
        if sn:
            self.sn_field.insert(0, sn)

    def save_screenshot_handler(self):
        save_screenshot(self.root, default_filename="QR_Code.png")

    def generate_qr_code(self):
        sn = self.sn_field.get()
        ble_password = self.ble_password_field.get()
        patient_name = self.patient_name_field.get()
        patient_family = self.family_field.get()
        gov_id = self.id_field.get()
        key1 = self.key1_field.get()

        # Calculate the SN checksum (ISO 7064 Mod 10,11)
        sn_checksum = mod_11_10(sn)
        sn_full = sn + sn_checksum  # Full SN with checksum

        # Calculate the BLE password checksum (ISO 7064 Mod 37,36)
        ble_checksum = calc_check_digit(ble_password.lower())
        ble_password_full = ble_password + ble_checksum  # Full BLE password with checksum

        # Hardcoded values instead of loading from config.yaml
        cloud_url = "a1ngo0wsq2lw86-ats.iot.eu-central-1.amazonaws.com"
        mqtt_prefix = "dev/things"

        # Generate the string based on toggle and step selection
        if self.toggle_var.get() == "HCP QR":
            if self.step_var.get() == "Patient App":
                result = f"bleSerial:{sn_full};blePassword:{ble_password_full};cloudUrl:{cloud_url};mqttPrefix:{mqtt_prefix}"
            else:
                result = f"bleSerial:{sn_full};blePassword:{ble_password_full};name:{patient_name};govId:{gov_id}"
        else:
            # Kit QR format
            if self.step_var.get() == "RTV":
                result = f"21{sn_full}\\^]91{ble_password_full}\\^]92{key1}\\^]"
            elif self.step_var.get() == "Patient App":
                result = f"21{sn_full}\\^]91{ble_password_full}\\^]92{key1}\\^]"
            else:
                result = f"21{sn_full}\\^]91{ble_password_full}\\^]92{key1}\\^]"
        
        print(result)  # Output the string to verify

        # Insert the result into the Text widget
        self.output_text.delete(1.0, tk.END)  # Clear previous text
        self.output_text.insert(tk.END, result)  # Insert the new result
        
        # Generate and display the QR code
        qr_code_image = generate_qr_code(result)
        self.display_qr_code(qr_code_image)


    def display_qr_code(self, qr_code_image):
        if self.qr_label:
            self.qr_label.destroy()  # Clear the previous QR code if it exists

        # Resize the QR code if it's too large for display
        max_size = 600  # Max size for QR code display
        width, height = qr_code_image.size
        if width > max_size or height > max_size:
            qr_code_image = qr_code_image.resize((max_size, max_size), Image.LANCZOS)
        
        # Convert the PIL Image to an ImageTk.PhotoImage object for display in the Tkinter GUI
        qr_img = ImageTk.PhotoImage(qr_code_image)
        self.qr_label = tk.Label(self.scrollable_frame, image=qr_img)
        self.qr_label.image = qr_img  # Keep a reference to avoid garbage collection
        self.qr_label.pack(pady=10)

    def upload_key1_bin(self):
        file_path = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
        if file_path:
            try:
                # Read the binary file and convert it to Base36
                with open(file_path, 'rb') as f:
                    binary_data = f.read()
                    base36_key = encode_bytes_to_base36_50chars(binary_data)
                    self.key1_field.delete(0, tk.END)
                    self.key1_field.insert(0, base36_key)
            except Exception as e:
                print(f"Error loading Key_1: {e}")

    def convert_to_base36(self):
        # Convert the 50-character Base36 key to binary and save it as .bin
        key1_value = self.key1_field.get()
        if len(key1_value) == 50:
            try:
                # Decode Base36 to binary
                binary_data = decode_base36_to_bytes(key1_value)
                
                # Ask user where to save the .bin file
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".bin",
                    initialfile="key_1.bin",
                    filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
                )
                if file_path:
                    with open(file_path, 'wb') as f:
                        f.write(binary_data)
                    print(f"Binary data saved to {file_path}")
            except Exception as e:
                print(f"Error converting to binary: {e}")
        else:
            print("Key_1 field must contain exactly 50 characters!")

    def enable_copy_paste(self):
        # Create a context menu for the text widgets
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.root.focus_get().event_generate('<<Copy>>'))
        menu.add_command(label="Paste", command=lambda: self.root.focus_get().event_generate('<<Paste>>'))

        # Bind right-click event to display context menu
        def show_menu(event):
            widget = event.widget
            if widget in [self.sn_field, self.ble_password_field, self.patient_name_field,
                          self.family_field, self.id_field, self.key1_field, self.output_text]:
                menu.tk_popup(event.x_root, event.y_root)
        
        for widget in [self.sn_field, self.ble_password_field, self.patient_name_field,
                       self.family_field, self.id_field, self.key1_field, self.output_text]:
            widget.bind("<Button-3>", show_menu)

    def copy_string_handler(self):
        # Copy the content of the output_text to the clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get(1.0, tk.END))
        messagebox.showinfo("Copied", "QR String copied to clipboard!")

# Entry point for the application
if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeApp(root)
    root.mainloop()
