class RadixDecoder:
    def __init__(self, radix_chars):
        self._radixCharacters = radix_chars
        self._radixLength = len(radix_chars)
        self._char_to_value_map = {char: idx for idx, char in enumerate(self._radixCharacters)}

    def decode(self, base36_string):
        # Convert the Base-36 string to an integer
        value = 0
        for char in base36_string:
            value = value * self._radixLength + self._char_to_value_map[char]
        
        # Convert the integer to bytes
        byte_length = (value.bit_length() + 7) // 8  # Calculate the number of bytes needed
        return value.to_bytes(byte_length, byteorder='big')

# Constants for Base-36 encoding (similar to RadixEncodingConstants in the original project)
BASE36_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Function to decode a 50-character Base-36 string back to binary data
def decode_base36_to_bytes(base36_string):
    # Step 1: Initialize the decoder with Base-36 characters
    decoder = RadixDecoder(BASE36_CHARS)
    
    # Step 2: Decode the Base-36 string back to binary data
    return decoder.decode(base36_string)

# Example usage:
base36_string = "2FDIU7I6KPZX4H9QOS6EQLDJGHD2UT5HX0E8BEKM0BKWIAX3DT"  # Your 50-char Base-36 string
decoded_bytes = decode_base36_to_bytes(base36_string)
print(decoded_bytes)
