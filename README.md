# Fetching Production Data and QR Generator (v3.0.0)

Desktop GUI (Tk / CustomTkinter) to:
- **Fetch production data from SAP** (keys + certificates)
- **Convert & save keys** in binary form
- **Generate QR codes** for Kit / HCP (RTV & Patient App) flows
- **Export certificates** (CRT/KEY + original one-line text) and copy the **Root CA**

> **Heads-up:** `config.yaml` is **local** and ignored by Git. Commit `config.example.yaml` for others.

---

## Features

### 1) SAP fetch (one click)
- Input **SN** → **Fetch keys + certificates** from SAP
- Creates a folder: `Production_data_{SN}_{YYYYmmdd-HHMMSS}/`
  - Keys: `pkey_{SN}.bin`, `mkey_{SN}.bin`, `key3_{SN}.bin`, `key4_{SN}.bin`, and bundle `keys_2_3_4.bin`
  - Certificates:
    - `{SN}-certificate.pem.crt` (AUTH_PUBLIC_KEY → proper PEM)
    - `{SN}-private.pem.key` (AUTH_PRIVATE_KEY → proper PEM)
    - `cert_string_{SN}.txt` (AUTH_PUBLIC_KEY as one line with `\n`)
    - `AWS_StarfieldCA_C2_And_G2.pem` (Root CA, copied from project root if present)
  - QR exports (when you generate later): `QR-Code/QR_{KIT|RTV|PatientApp}_{SN}_{ts}.{png,txt}`

### 2) Keys panel (with conversions)
- **Key_1 (PKEY)**  
  - *Long* (SAP): **Base36, 50 chars**  
  - *Short* (raw 32 bytes): shown as **ASCII if printable**, else **HEX** (you can force HEX or Base64 via the dropdown)
  - Upload `.bin` ↔ convert to Long/Short
- **Key_2 (MKEY)**  
  - *Long* (SAP): **Base64 → 32 bytes**
  - *Short* (raw 32 bytes): same display rules as above
  - Upload `.bin` ↔ convert to Long/Short
- **Key_3 (BLE_ID) / Key_4 (PATIENT_BLE_PWD)**  
  - Derived via **PBKDF2-HMAC-SHA256**, `iterations=310000`,  
    `salt=0xC30AF78E2C3EE53B5D52E2FD93B3513A`  
  - **One-way**: only derive HEX from the SAP strings (cannot reverse a `.bin` to the SAP string)

### 3) QR generation
- Types:
  - **Kit QR** → `21{SN+mod11,10}^]91{BLE+mod37,36}^]92{Key1_short(Base64)}^]`
  - **HCP / RTV** → `bleSerial:{...};blePassword:{...};name:{...};govId:{...}`
  - **HCP / Patient App** → `bleSerial:{...};blePassword:{...};cloudUrl:{...};mqttPrefix:{...}`
- BLE password check digit: **ISO 7064 Mod 37,36** (computed on lowercase but appended **uppercase**)
- SN check digit: **ISO 7064 Mod 11,10**
- Saves **PNG + TXT** with a friendly name:
  - `QR_{KIT|RTV|PatientApp}_{SN}_{YYYYmmdd-HHMMSS}.{png,txt}`
  - Saved under `Production_data_{SN}_{ts}/QR-Code/` if you fetched first, or in a folder you choose.

### 4) Cloud profiles
- Radios: **newton**, **davinci**, **manual**  
- Values loaded from `config.yaml` → `cloudProfiles` & `defaultProfile`  
- Manual profile lets you edit URL/prefix inline

---


## Install

```bash
# create and activate a virtual env
python -m venv .venv

# Windows PowerShell
. .venv/Scripts/activate

# macOS/Linux
# source .venv/bin/activate

# install deps
pip install -r requirements.txt
````

---


**Root CA**
Place `AWS_StarfieldCA_C2_And_G2.pem` in the project root. When you fetch/save certs,
the app copies it into your production output folder.

> `config.yaml` is **local**;

---

## Run

```bash
# from the project folder, with your venv activated
python main.py
```

---

## Usage (quick)

1. **Enter SN** (or “SN from .yaml”)
2. **Fill All** (pulls defaults from `config.yaml:autofill`)
3. **Fetch keys from SAP** → creates `Production_data_{SN}_{YYYYmmdd-HHMMSS}/` with:

   * `pkey_{SN}.bin`, `mkey_{SN}.bin`, `key3_{SN}.bin`, `key4_{SN}.bin`, `keys_2_3_4.bin`
   * `{SN}-certificate.pem.crt`, `{SN}-private.pem.key`, `cert_string_{SN}.txt`
   * `AWS_StarfieldCA_C2_And_G2.pem`
4. **Generate QR Code**

   * Saves **PNG + TXT** to:

     * `Production_data_{SN}_{ts}/QR-Code/` (if fetched first), or
     * a folder you choose (if no production folder yet).
   * Filename: `QR_{KIT|RTV|PatientApp}_{SN}_{YYYYmmdd-HHMMSS}.{png,txt}`

**Short display mode (Key\_1/Key\_2):**
Use the dropdown to view 32-byte “short” values as:

* `auto` → ASCII if printable, otherwise HEX
* `hex`  → always 64-hex
* `b64`  → Base64 of the 32 bytes

**Key\_3 / Key\_4:**
Derived from **BLE\_ID** / **PATIENT\_BLE\_PWD** via PBKDF2-HMAC-SHA256
(310,000 iterations; salt `C30AF78E2C3EE53B5D52E2FD93B3513A`). One-way by design.

---

## Output layout

```
Production_data_{SN}_{YYYYmmdd-HHMMSS}/
├─ pkey_{SN}.bin
├─ mkey_{SN}.bin
├─ key3_{SN}.bin
├─ key4_{SN}.bin
├─ keys_2_3_4.bin
├─ {SN}-certificate.pem.crt
├─ {SN}-private.pem.key
├─ cert_string_{SN}.txt
├─ AWS_StarfieldCA_C2_And_G2.pem
└─ QR-Code/
   ├─ QR_KIT_{SN}_{ts}.png
   ├─ QR_KIT_{SN}_{ts}.txt
   ├─ QR_RTV_{SN}_{ts}.png
   └─ QR_RTV_{SN}_{ts}.txt
```

---

## Troubleshooting

* **“Short looks like HEX, not letters”** → The 32 bytes aren’t printable ASCII.
  Switch the dropdown to `b64` if you prefer Base64 view.
* **Key\_3/Key\_4 upload?** → Not supported; PBKDF2 is one-way. Enter the SAP strings; the app derives hex.
* **BLE check digit appears lowercase** → The digit is computed on lowercase but appended **uppercase** in the UI/QR.