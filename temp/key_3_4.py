key3_RTV_BLE_PWD = '9XMY6FDMXC'
key4_PATIENT_BLE_PWD = 'V4G74W6LW5'

from hashlib import pbkdf2_hmac
iterations = 310000
# nonce = {195, 10, 247, 142, 44, 62, 229, 59, 93, 82, 226, 253, 147, 179, 81, 58}
nonce_hex = 'C30AF78E2C3EE53B5D52E2FD93B3513A'
salt = bytes.fromhex(nonce_hex)
passwordtohash = key3_RTV_BLE_PWD
hash = pbkdf2_hmac('sha256',bytes(passwordtohash,'utf-8'), salt, iterations, dklen=32)
# print(f"pbkdf2:{iterations}:{salt.hex()}:{hash.hex()}")
print(f"RTV Key3:{hash.hex()}")

passwordtohash = key4_PATIENT_BLE_PWD
hash = pbkdf2_hmac('sha256',bytes(passwordtohash,'utf-8'), salt, iterations, dklen=32)
print(f"Patient APP Key4:{hash.hex()}")