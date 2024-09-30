# ISO 7064 Mod 10,11 (for SN checksum)
def mod_11_10(number):
    check = 10
    for n in number:
        check = (check % 11 + int(n)) % 10
        if check == 0:
            check = 10
        check = (check * 2) % 11
    return str((11 - check) % 11) if check != 1 else '0'

# ISO 7064 Mod 37,36 (for BLE_Password checksum)
def calc_check_digit(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    modulus = len(alphabet)
    check = modulus // 2
    for n in number:
        check = (((check or modulus) * 2) % (modulus + 1) + alphabet.index(n)) % modulus
    return alphabet[(1 - ((check or modulus) * 2) % (modulus + 1)) % modulus]
