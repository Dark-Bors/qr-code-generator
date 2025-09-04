import base36

SN = '250401745'
mKey = "o8IJaYQKCUsDdnXEmHBSV9+qAPULKii5GE3CaRN3aW4="
pKey = '5DZ2J4Y60YCDWOEW6R9FVJ4WYN265DMYOVU7ZD17MK4X70G9J4'

# Decode the Base36 string to bytes
decoded_base36_bytes = base36.loads(mKey)

# Decode the Base36 string to bytes
# decoded_base36_bytes = base36.loads(pKey)

# print(decoded_base64_bytes)
# print(decoded_base36_bytes)
# with open(f'mkey_{SN}.bin', 'wb') as f:
#     f.write(decoded_base36_bytes)


def base36_to_bytes(base36_str):
    # Convert Base36 string to an integer
    number = int(base36_str, 36)

    # Convert the integer to a 32-byte array
    byte_array = number.to_bytes(32, byteorder='little')

    return byte_array


# Example usage
# base36_str = '1z141z3'  # Example Base36 string
mkey_byte_array = base36_to_bytes(mKey)
print(mkey_byte_array)

pkey_byte_array = base36_to_bytes(pKey)
print(pkey_byte_array)

with open(f'mkey_{SN}.bin', 'wb') as f:
    f.write(mkey_byte_array)

with open(f'pkey_{SN}.bin', 'wb') as f:
    f.write(pkey_byte_array)