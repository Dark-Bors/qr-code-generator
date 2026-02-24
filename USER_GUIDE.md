# Simple User Guide for FPD App

This guide will help you use the **Fetch Production Data (FPD)** application quickly and easily.

## 1. How to Start the App
1. Open the application folder.
2. Double-click the file named **`run_app.bat`**.
   - A black window will appear (this is normal), followed by the main application window.

## 2. How to Use It
Follow these 3 simple steps:

### Step 1: Enter Serial Number
- In the top "Device Data" section, look for the **Serial Number (SN)** box.
- Type in the 10-digit Serial Number of the device (or verify the auto-filled one).
- Click the **"Fill All"** button if you want to auto-fill other fields from settings.

### Step 2: Fetch Data
- Click the big blue button: **"Fetch Keys from SAP"**.
- Wait a moment for the success message.
- This downloads all the necessary keys and certificates for that device.

### Step 3: Generate QR Codes
- Click the **"Generate QR Codes"** button (bottom right).
- This creates the QR code images needed for the Kit, RTV, or Patient App.

## 3. Where are my files?
After you finish Step 2 & 3, look in the application folder.
You will see a new folder named like this:
📂 `Production_data_{SN}_{Date-Time}`

Inside this folder you will find:
- **Keys & Certificates**: `.bin`, `.crt`, `.key` files.
- **QR Codes**: Inside the `QR-Code` subfolder (Images and Text files).

## 4. Common Questions

**Q: The "Short" key looks like numbers and letters mixed up?**
A: That is normal. If the key cannot be read as text, the app shows it in HEX code (numbers and letters).

**Q: The app does not open?**
A: Make sure you have the `venv` folder set up. If you just downloaded this tool, you might need to install it first (ask your technical lead or run the install commands). 
