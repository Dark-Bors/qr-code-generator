import yaml
import time
import os
from tkinter import filedialog
from PIL import ImageGrab

# Recursive function to search for BLE_ID or LD_Serial_Number in a nested YAML structure
def find_sn_in_yaml(data):
    if isinstance(data, dict):
        # Check if BLE_ID or LD_Serial_Number exists in the current level
        if 'BLE_ID' in data:
            return data['BLE_ID']
        elif 'LD_Serial_Number' in data:
            return data['LD_Serial_Number']
        # If not found, search deeper
        for key, value in data.items():
            result = find_sn_in_yaml(value)
            if result:
                return result
    elif isinstance(data, list):
        # If the data is a list, check each element
        for item in data:
            result = find_sn_in_yaml(item)
            if result:
                return result
    return None

# Function to load and extract the SN from a nested YAML structure
def load_yaml_sn():
    # Open a file dialog for the user to select the YAML file
    file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
    
    if not file_path:  # User cancels the dialog
        return None
    
    # Load the YAML file and search for BLE_ID or LD_Serial_Number
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            
            # Search for BLE_ID or LD_Serial_Number using the recursive function
            sn = find_sn_in_yaml(data)
            
            if sn:
                return sn
            else:
                print("SN not found in BLE_ID or LD_Serial_Number fields.")
                return None

    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
        return None

# Function to save a screenshot of the current application window
def save_screenshot(root, default_filename="QR_Code.png"):
    # Capture the current window using ImageGrab
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=default_filename,
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )

    if file_path:
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(file_path)
        print(f"Screenshot saved as {file_path}")
