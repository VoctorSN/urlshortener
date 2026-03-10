import io

import qrcode
from qrcode.image.pil import PilImage


def generate_qr_code(data: str, size: int = 10, border: int = 2) -> bytes:
    """Generate a QR code PNG image as bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img: PilImage = qr.make_image(fill_color="black", back_color="white")  # type: ignore[assignment]
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
