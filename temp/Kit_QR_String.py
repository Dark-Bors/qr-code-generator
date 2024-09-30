import re

# ISO7064 Mod 37,36 (for BLE_Password checksum)
def calc_check_digit(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Calculate the checksum for BLE_Password using mod 37,36."""
    modulus = len(alphabet)
    check = modulus // 2
    for n in number:
        check = (((check or modulus) * 2) % (modulus + 1) + alphabet.index(n)) % modulus
    return alphabet[(1 - ((check or modulus) * 2) % (modulus + 1)) % modulus]

# ISO7064 Mod 10,11 (for SN checksum)
def mod_11_10(number):
    """Calculate the check digit using MOD 11,10 (ISO 7064) algorithm for SN."""
    check = 10
    for n in number:
        check = (check % 11 + int(n)) % 10
        if check == 0:
            check = 10
        check = (check * 2) % 11
    return str((11 - check) % 11) if check != 1 else '0'

# Function to generate the formatted string
def generate_custom_string():
    # Input for SN (9 digits + 1 checksum digit)
    sn_base = input("Enter the first 9 digits of SN: ").strip()
    if len(sn_base) != 9 or not sn_base.isdigit():
        print("SN must be 9 digits!")
        return
    sn_checksum = mod_11_10(sn_base)
    sn = sn_base + sn_checksum
    
    # Input for BLE_Password (10 chars + 1 checksum digit)
    ble_password_base = input("Enter the first 10 chars of BLE_Password (base 32): ").strip().lower()
    if len(ble_password_base) != 10 or not re.match(r'^[a-z0-9]{10}$', ble_password_base):
        print("BLE_Password must be 10 base32 characters (lowercase, 0-9, a-z)!")
        return
    ble_checksum = calc_check_digit(ble_password_base)
    ble_password = ble_password_base + ble_checksum

    # Input for key (50 chars, Base 36)
    key = input("Enter the 50-character key (Base 36): ").strip().upper()
    if len(key) != 50 or not re.match(r'^[0-9A-Z]{50}$', key):
        print("Key must be exactly 50 Base 36 characters!")
        return

    # Construct the string
    result = f"21{sn}\\^]91{ble_password}\\^]92{key}\\^]"
    print(f"Generated string: {result}")

# Call the function
generate_custom_string()
