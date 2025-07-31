from report_generator.pdf_builder import generate_qr_code
from io import BytesIO
from PIL import Image


def test_generate_qr_code_valid_url():
    url = "https://example.com/archive"
    qr_buf = generate_qr_code(url)

    # Проверка типа и содержимого
    assert isinstance(qr_buf, BytesIO)
    assert qr_buf.getbuffer().nbytes > 0

    # Проверка, что это корректное изображение
    try:
        img = Image.open(qr_buf)
        img.verify()  # Проверяет, что файл не повреждён
    except Exception:
        assert False, "QR-код не является корректным изображением"

