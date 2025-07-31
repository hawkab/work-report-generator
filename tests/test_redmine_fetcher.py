from unittest.mock import patch, MagicMock
from datetime import date
from report_generator.redmine_fetcher import fetch_redmine_activity


@patch("report_generator.redmine_fetcher.Redmine")
def test_fetch_redmine_activity_success(mock_redmine_cls):
    # Даты
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 5)

    # Подставим time_entry
    mock_time_entry = MagicMock()
    mock_time_entry.spent_on = start_date
    mock_time_entry.hours = 4
    mock_time_entry.comments = "Работа над задачей"

    mock_time_entries = [mock_time_entry]

    # Подставим issue + journals
    mock_journal = MagicMock()
    mock_journal.created_on = start_date
    mock_journal.user.id = 123
    mock_journal.details = [{
        "property": "attr",
        "name": "status_id",
        "old_value": "1",
        "new_value": "2"
    }]
    mock_journal.notes = "Комментарий к задаче"

    mock_issue = MagicMock()
    mock_issue.id = 42
    mock_issue.journals = [mock_journal]

    # Кеш Redmine статусов
    from report_generator import config
    config.REDMINE_STATUS_CACHE.clear()
    config.REDMINE_STATUS_CACHE["1"] = "Open"
    config.REDMINE_STATUS_CACHE["2"] = "Closed"

    # Мокаем методы клиента
    mock_redmine = MagicMock()
    mock_redmine.time_entry.filter.return_value = mock_time_entries
    mock_redmine.issue.filter.return_value = [mock_issue]

    mock_redmine_cls.return_value = mock_redmine

    # Подставим ENV
    import os
    os.environ["REDMINE_URL"] = "https://redmine.example.com"
    os.environ["REDMINE_API_KEY"] = "key"
    os.environ["REDMINE_USER_ID"] = "123"

    # Выполнение
    activities = fetch_redmine_activity(start_date, end_date)

    # Проверки
    assert isinstance(activities, list)
    assert len(activities) == 3  # 1 time_entry + 1 status change + 1 comment
    assert any("трудозатрат" in a["details"] for a in activities)
    assert any("Изменил статус задачи" in a["details"] for a in activities)
    assert any("Комментарий к задаче" in a["details"] for a in activities)

    # Убедимся, что методы вызваны
    mock_redmine.time_entry.filter.assert_called_once()
    mock_redmine.issue.filter.assert_called_once()

