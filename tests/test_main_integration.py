from unittest.mock import patch, MagicMock
from datetime import date
import os


@patch("report_generator.main.fetch_gitlab_events", return_value=[])
@patch("report_generator.main.fetch_jira_activity", return_value=[])
@patch("report_generator.main.fetch_redmine_activity", return_value=[])
@patch("report_generator.main.fetch_confluence_activity", return_value=[])
@patch("report_generator.main.generate_pdf", return_value="/tmp/dummy.pdf")
@patch("report_generator.main.send_pdf_by_email", return_value=True)
def test_main_integration_all_mocks(
    mock_send_email,
    mock_generate_pdf,
    mock_fetch_confluence,
    mock_fetch_redmine,
    mock_fetch_jira,
    mock_fetch_gitlab,
):
    # Импорт main после моков
    from report_generator.main import main

    # Подготовка переменных окружения
    os.environ["WEEK_START"] = "2025-07-01"
    os.environ["WEEK_END"] = "2025-07-05"
    os.environ["SMTP_SERVER"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "465"
    os.environ["SMTP_USERNAME"] = "test@example.com"
    os.environ["SMTP_PASSWORD"] = "password"
    os.environ["REPORT_RECIPIENT"] = "recipient@example.com"
    os.environ["EMAIL_FROM"] = "test@example.com"
    os.environ["REPORT_SUBJECT"] = "Отчёт {period}"
    os.environ["REPORT_BODY"] = "Тело письма для {period}"
    os.environ["REPORTS_ARCHIVE_URL"] = "https://example.com/reports"

    # Вызов main()
    try:
        main()
    except SystemExit:
        # main может вызвать sys.exit(), подавим его
        pass

    # Проверки
    mock_fetch_gitlab.assert_called_once()
    mock_fetch_jira.assert_called_once()
    mock_fetch_redmine.assert_called_once()
    mock_fetch_confluence.assert_called_once()
    mock_generate_pdf.assert_called_once()
    mock_send_email.assert_called_once()

