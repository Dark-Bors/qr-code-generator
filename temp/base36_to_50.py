from math import ceil

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
        # Converts byte array (data) to Base-36 encoded string
        inputLength = len(data)
        encodedResultLength = self._encoded_result_length(inputLength)
        
        # Convert the byte array to an integer
        value = int.from_bytes(data, byteorder="big")
        result = []
        while value > 0:
            result.append(self._radixCharacters[value % self._radixLength])
            value //= self._radixLength
        result.reverse()
        return ''.join(result).zfill(encodedResultLength)  # Ensure correct length by zero-padding if necessary

    def _encoded_result_length(self, inputLength):
        return int(ceil((inputLength * 8) / self._bitsPerDigit))

# Constants for Base-36 encoding (similar to RadixEncodingConstants in the original project)
BASE36_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Function to encode a binary variable to Base-36 and return a 50-char string
def encode_bytes_to_base36_50chars(binary_data):
    # Step 1: Initialize the encoder with Base-36 characters
    encoder = RadixEncoder(BASE36_CHARS)

    # Step 2: Encode the binary data to a Base-36 string
    encoded_str = encoder.encode(binary_data)

    # Step 3: Ensure the string is exactly 50 characters long (truncate or pad)
    if len(encoded_str) > 50:
        return encoded_str[:50]
    else:
        return encoded_str.zfill(50)  # Pad with leading zeros if necessary

# Example usage:
binary_data = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'  # Replace with your actual byte data
encoded_key = encode_bytes_to_base36_50chars(binary_data)
print(encoded_key)
