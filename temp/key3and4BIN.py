from hashlib import pbkdf2_hmac

key3_RTV_BLE_PWD = 'ABCDEFGHIJ'
key4_PATIENT_BLE_PWD = 'ABCDEFGHIJ'

iterations = 310000
nonce_hex = 'C30AF78E2C3EE53B5D52E2FD93B3513A'
salt = bytes.fromhex(nonce_hex)

def derive_and_save(password: str, filename: str):
    """Derive PBKDF2-HMAC-SHA256 key and save to .bin file"""
    key = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
    print(f"{filename}: {key.hex()}")
    with open(filename, "wb") as f:
        f.write(key)

# Derive and save both
derive_and_save(key3_RTV_BLE_PWD, "key3_RTV.bin")
derive_and_save(key4_PATIENT_BLE_PWD, "key4_PATIENT.bin")
