import qrcode
from PIL import Image

# Function to generate a QR code from the provided data (result string)
def generate_qr_code(data):
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_code.add_data(data)
    qr_code.make(fit=True)
    image = qr_code.make_image(fill_color="black", back_color="white")
    
    # Return the QR code image as a PIL Image object
    return image


