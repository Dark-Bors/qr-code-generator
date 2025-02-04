import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import base64

# Derived XOR Keys
key_1_xor_key = bytes.fromhex("A8 7E 63 70 9A C9 94 0B 9F 2F CD 66 80 6E F9 61 EF 1B 94 23 E0 7F 83 18 78 22 DB A0 1B 9C 47 18")
key_2_xor_key = bytes.fromhex("7B 8D A0 E9 4B C8 1B 52 E1 89 13 63 51 D9 7D 22 9A 3E 21 23 7D AC F4 E1 A2 69 70 AE B8 60 7E 96")

# Helper Functions
def base36_to_bytes(base36_str):
    """Convert a Base36 string to bytes."""
    value = int(base36_str, 36)
    return value.to_bytes((value.bit_length() + 7) // 8, 'big')

def bytes_to_base36(byte_data):
    """Convert bytes to Base36 string."""
    value = int.from_bytes(byte_data, 'big')
    result = ''
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    while value:
        value, remainder = divmod(value, 36)
        result = chars[remainder] + result
    return result or '0'

def base64_to_bytes(base64_str):
    """Convert a Base64 string to bytes."""
    return base64.b64decode(base64_str)

def bytes_to_base64(byte_data):
    """Convert bytes to Base64 string."""
    return base64.b64encode(byte_data).decode('utf-8')

def apply_xor(byte_data, xor_key):
    """Apply XOR operation with a given key."""
    return bytes(a ^ b for a, b in zip(byte_data, xor_key * (len(byte_data) // len(xor_key) + 1)))

def convert_string_to_bin():
    """Convert user input string to a binary file."""
    input_text = input_box.get("1.0", tk.END).strip()
    if not input_text:
        log_message("No input string provided.")
        messagebox.showwarning("Warning", "Input string cannot be empty.")
        return

    try:
        # Check if input is Base36 or Base64
        if input_text.isalnum() and input_text.isupper():  # Base36
            log_message("Detected input type: Base36")
            binary_data = apply_xor(base36_to_bytes(input_text), key_1_xor_key)
            result_type = "Base36"
        else:  # Base64
            log_message("Detected input type: Base64")
            binary_data = apply_xor(base64_to_bytes(input_text), key_2_xor_key)
            result_type = "Base64"

        # Save the binary file
        save_path = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("BIN files", "*.bin")])
        if save_path:
            with open(save_path, "wb") as file:
                file.write(binary_data)
            log_message(f"Successfully saved {result_type} data to {save_path}")
            messagebox.showinfo("Success", f"File saved to: {save_path}")
    except Exception as e:
        log_message(f"Error converting string to binary: {str(e)}")
        messagebox.showerror("Error", f"Conversion failed: {str(e)}")

def open_bin_pkey():
    """Convert BIN file back to Base36."""
    file_path = filedialog.askopenfilename(filetypes=[("BIN files", "*.bin")])
    if not file_path:
        log_message("PKEY file selection cancelled.")
        return

    try:
        with open(file_path, "rb") as file:
            binary_data = file.read()
        log_message(f"Loaded BIN file for PKEY: {file_path}")
        result = bytes_to_base36(apply_xor(binary_data, key_1_xor_key))
        display_result(result)
        log_message(f"Converted PKEY file back to Base36.")
    except Exception as e:
        log_message(f"Error converting PKEY file: {str(e)}")
        messagebox.showerror("Error", f"Could not process PKEY file: {str(e)}")

def open_bin_mkey():
    """Convert BIN file back to Base64."""
    file_path = filedialog.askopenfilename(filetypes=[("BIN files", "*.bin")])
    if not file_path:
        log_message("MKEY file selection cancelled.")
        return

    try:
        with open(file_path, "rb") as file:
            binary_data = file.read()
        log_message(f"Loaded BIN file for MKEY: {file_path}")
        result = bytes_to_base64(apply_xor(binary_data, key_2_xor_key))
        display_result(result)
        log_message(f"Converted MKEY file back to Base64.")
    except Exception as e:
        log_message(f"Error converting MKEY file: {str(e)}")
        messagebox.showerror("Error", f"Could not process MKEY file: {str(e)}")

def display_result(result):
    """Display result in the output box."""
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, result)
    log_message("Result displayed successfully.")

def copy_result():
    """Copy the result to clipboard."""
    result = output_box.get("1.0", tk.END).strip()
    if result:
        root.clipboard_clear()
        root.clipboard_append(result)
        root.update()
        log_message("Result copied to clipboard.")
    else:
        log_message("No result to copy.")

def log_message(message):
    """Add a message to the debug log."""
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

# GUI Setup
root = tk.Tk()
root.title("Key Converter Tool")
root.geometry("800x700")
root.configure(bg="#1E1E1E")

# Input Section
tk.Label(root, text="String to BIN Conversion:", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(pady=5)
input_box = tk.Text(root, height=3, bg="#252526", fg="#DCDCDC", insertbackground="white")
input_box.pack(fill="x", padx=10, pady=5)
ttk.Button(root, text="Convert String to BIN", command=convert_string_to_bin).pack(pady=5)

# File Buttons
tk.Label(root, text="Convert BIN File Back:", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(pady=5)
button_frame = tk.Frame(root, bg="#1E1E1E")
button_frame.pack(pady=5)
ttk.Button(button_frame, text="Open BIN File for PKEY (Base36)", command=open_bin_pkey).pack(side="left", padx=5)
ttk.Button(button_frame, text="Open BIN File for MKEY (Base64)", command=open_bin_mkey).pack(side="left", padx=5)

# Output Section
tk.Label(root, text="Output Result:", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(pady=5)
output_box = tk.Text(root, height=3, bg="#252526", fg="#DCDCDC", insertbackground="white")
output_box.pack(fill="x", padx=10, pady=5)
ttk.Button(root, text="Copy Result", command=copy_result).pack(pady=5)

# Log Section
tk.Label(root, text="Debug Log:", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(pady=5)
log_box = tk.Text(root, height=10, bg="#252526", fg="#DCDCDC", insertbackground="white")
log_box.pack(fill="both", padx=10, pady=5, expand=True)

# Start GUI
log_message("Application started.")
root.mainloop()
