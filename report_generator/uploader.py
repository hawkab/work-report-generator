import os
import smtplib
from ftplib import FTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from .config import logger


def upload_file_to_ftp(file_path: str):
    ftp_host = os.getenv("FTP_HOST")
    ftp_user = os.getenv("FTP_USER")
    ftp_pass = os.getenv("FTP_PASS")
    remote_path = os.getenv("FTP_PATH")

    try:
        with FTP(ftp_host) as ftp:
            ftp.login(user=ftp_user, passwd=ftp_pass)
            logger.info(f"Успешно подключились к FTP: {ftp_host}")

            remote_full_path = f"{remote_path}/{os.path.basename(file_path)}"
            ftp.voidcmd('TYPE I')  # бинарный режим

            with open(file_path, 'rb') as file:
                ftp.storbinary(f'STOR {remote_full_path}', file)

            logger.info(f"Файл успешно загружен: {remote_full_path}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке на FTP: {e}")


def send_pdf_by_email(pdf_file_path: str, period: str) -> bool:
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 465))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    email_from = os.getenv('EMAIL_FROM', smtp_username)
    email_to = os.getenv('REPORT_RECIPIENT')

    subject_template = os.getenv('REPORT_SUBJECT', '{period}')
    body_template = os.getenv('REPORT_BODY', '{period}')
    
    subject = subject_template.format(period=period)
    body = body_template.format(period=period)

    try:
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with open(pdf_file_path, 'rb') as pdf_file:
            part = MIMEApplication(pdf_file.read(), Name=os.path.basename(pdf_file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_file_path)}"'
        msg.attach(part)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(f"Письмо отправлено на {email_to}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        return False

