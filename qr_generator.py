# qr_generator.py
"""
QR Generator helper for FPD GUI
"""

import qrcode
from pathlib import Path

def generate_qr_from_sn(sn: str, output_dir: str = "output") -> str:
    """
    Generates a QR code PNG for the provided serial number (SN).
    Returns the path to the saved file.
    """
    if not sn:
        raise ValueError("Serial number required for QR generation.")
    
    Path(output_dir).mkdir(exist_ok=True)
    qr_path = Path(output_dir) / f"{sn}_qr.png"

    img = qrcode.make(sn)
    img.save(qr_path)
    print(f"✅ QR saved: {qr_path}")
    return str(qr_path)
