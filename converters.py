from math import ceil
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


# Base36 to 50 converter
class RadixEncoder:
    def __init__(self, radix_chars):
        self._radixCharacters = radix_chars
        self._radixLength = len(radix_chars)
        self._bitsPerDigit = self._calculate_bits_per_digit()

    def _calculate_bits_per_digit(self):
        bits = 0
        while (1 << bits) < self._radixLength:
            bits += 1
        return bits

    def encode(self, data):
        inputLength = len(data)
        encodedResultLength = self._encoded_result_length(inputLength)
        value = int.from_bytes(data, byteorder="big")
        result = []
        while value > 0:
            result.append(self._radixCharacters[value % self._radixLength])
            value //= self._radixLength
        result.reverse()
        return ''.join(result).zfill(encodedResultLength)

    def _encoded_result_length(self, inputLength):
        return int(ceil((inputLength * 8) / self._bitsPerDigit))

# Base36 decoding (from 50 characters)
class RadixDecoder:
    def __init__(self, radix_chars):
        self._radixCharacters = radix_chars
        self._char_to_value_map = {char: idx for idx, char in enumerate(self._radixCharacters)}

    def decode(self, base36_string):
        value = 0
        for char in base36_string:
            value = value * len(self._radixCharacters) + self._char_to_value_map[char]
        byte_length = (value.bit_length() + 7) // 8
        return value.to_bytes(byte_length, byteorder='big')

# Wrapper function to encode bytes to Base36 (50 characters)
def encode_bytes_to_base36_50chars(data):
    encoder = RadixEncoder("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return encoder.encode(data)

# Wrapper function to decode Base36 back to bytes
def decode_base36_to_bytes(base36_string):
    decoder = RadixDecoder("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return decoder.decode(base36_string)
