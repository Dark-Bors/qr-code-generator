import base64

# Function to decode Base36 to bytes
def base36_to_bytes(base36_str):
    decoded_int = int(base36_str, 36)
    num_bytes = (decoded_int.bit_length() + 7) // 8
    return decoded_int.to_bytes(num_bytes, byteorder='big')

# Function to convert reversed bytes to Base64
def reversed_bytes_to_base64(byte_data):
    reversed_bytes = byte_data[::-1]
    return base64.b64encode(reversed_bytes).decode('utf-8')

# Function to handle Base64 decoded bytes and get 32-char string
def base64_to_32char_string(base64_str):
    # Decode the Base64 string back to bytes
    base64_bytes = base64.b64decode(base64_str)
    
    # Perform some consistent operation to extract a 32-character string
    # We will take the first 32 bytes and convert them to a readable ASCII string
    return ''.join([chr(b % 128) for b in base64_bytes[:32]])

# Function to process the input Base36 string and generate outputs
def process_base36_string(base36_str):
    # Step 1: Convert Base36 to bytes
    base36_bytes = base36_to_bytes(base36_str)
    
    # Step 2: Convert the Base36 bytes to Base64 (with reversal)
    base64_result = reversed_bytes_to_base64(base36_bytes)
    
    # Step 3: Convert the Base64 string to a 32-character string
    result_32char = base64_to_32char_string(base64_result)
    
    # Output the results
    print(f"Input Base36 String: {base36_str}")
    print(f"Base36 to Base64: {base64_result}")
    print(f"Base64 to 32-char string: {result_32char}")

# Main execution
if __name__ == "__main__": 
    # Example Base36 input (you can replace this with any Base36 string)
    base36_input = input("Enter a Base36 string: ") 

    # Process the input Base36 string 
    process_base36_string(base36_input)


'''
195TLW3QJZNKFXZ37GJB43XZGE7B9UYYI57ZGSQFA9CNBT7VWP (Base36) 
to
SVZIUDJCVlVWUFEyMTM5Vk1ESVZRSVJTSE1YVDY3VTI= (base64) I
to
32-char string: IVHP2BVUVPQ2139VMDIVQIRSHMXT67U2
'''
