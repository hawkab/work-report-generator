from unittest.mock import patch, MagicMock
from report_generator.uploader import send_pdf_by_email
import tempfile
import os


@patch("smtplib.SMTP_SSL")
def test_send_pdf_by_email_success(mock_smtp_ssl):
    # Создаём временный PDF-файл
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf.write(b"%PDF-1.4 test content")
        tmp_pdf_path = tmp_pdf.name

    # Подменяем SMTP-сессию
    mock_server = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = mock_server

    # Подменяем окружение
    os.environ["SMTP_SERVER"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "465"
    os.environ["SMTP_USERNAME"] = "user@example.com"
    os.environ["SMTP_PASSWORD"] = "password"
    os.environ["REPORT_RECIPIENT"] = "recipient@example.com"
    os.environ["EMAIL_FROM"] = "user@example.com"
    os.environ["REPORT_SUBJECT"] = "Test Report {period}"
    os.environ["REPORT_BODY"] = "This is a test for {period}."

    # Выполняем
    result = send_pdf_by_email(tmp_pdf_path, "01.07.2025–05.07.2025")

    # Проверки
    assert result is True
    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()

    # Очистка
    os.remove(tmp_pdf_path)

