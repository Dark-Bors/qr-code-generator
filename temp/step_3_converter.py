import base36
import base64

SN = '24490007'
pKey = '5B76CJH6O34VWMJ0072G35BYI6VZMU0YQE2X0BUFDLBQ97O9UU'
mKey = "Tm0moGY/ELrThRKC5a2k6JIRXFKNDh0M6KTQpqqBlic="


# Decode the Base36 string to bytes
decoded_base36_bytes = base36.loads(pKey)


def base36_to_bytes(base36_str):
    # Convert Base36 string to an integer
    number = int(base36_str, 36)

    # Convert the integer to a 32-byte array
    byte_array = number.to_bytes(32, byteorder='little')

    return byte_array


# Example usage
# base36_str = '1z141z3'  # Example Base36 string

pkey_byte_array = base36_to_bytes(pKey)
print(pkey_byte_array)


with open(f'pkey_{SN}.bin', 'wb') as f:
    f.write(pkey_byte_array)

# Decode the Base64 string to bytes
decoded_bytes = base64.b64decode(mKey)


print(decoded_bytes)
with open(f'mkey_{SN}.bin', 'wb') as f:
    f.write(decoded_bytes)