import qrcode
from PIL import Image
from qrcode.image.svg import SvgImage

def generate_qr_code(data: str) -> Image.Image:
    """Bitmap QR (PIL Image)."""
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_code.add_data(data)
    qr_code.make(fit=True)
    return qr_code.make_image(fill_color="black", back_color="white")

def generate_qr_svg(data: str) -> str:
    """Return SVG XML as a string."""
    img = qrcode.make(data, image_factory=SvgImage, box_size=10)
    return img.to_string().decode("utf-8") if hasattr(img.to_string(), "decode") else img.to_string()
