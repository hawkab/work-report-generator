from unittest.mock import patch, MagicMock
from datetime import date
from report_generator.confluence_fetcher import fetch_confluence_activity


@patch("report_generator.confluence_fetcher.Confluence")
def test_fetch_confluence_activity_success(mock_confluence_cls):
    # Задаём даты
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 5)

    # Эмулируем страницы с нужными изменениями
    mock_page1 = {
        "id": "123",
        "title": "Страница 1",
        "version": {"when": "2025-07-01T10:00:00.000+0000"},
        "history": {"lastUpdated": {"by": {"displayName": "Test User"}}},
        "_links": {"base": "https://confluence.example.com", "webui": "/pages/viewpage.action?pageId=123"}
    }

    mock_page2 = {
        "id": "124",
        "title": "Страница 2",
        "version": {"when": "2025-07-05T18:30:00.000+0000"},
        "history": {"lastUpdated": {"by": {"displayName": "Другой Пользователь"}}},
        "_links": {"base": "https://confluence.example.com", "webui": "/pages/viewpage.action?pageId=124"}
    }

    mock_confluence = MagicMock()
    mock_confluence.get_all_pages_by_label.side_effect = [[mock_page1], [mock_page2]]
    mock_confluence_cls.return_value = mock_confluence

    # Подменяем окружение
    import os
    os.environ["CONFLUENCE_URL"] = "https://confluence.example.com"
    os.environ["CONFLUENCE_USER"] = "testuser"
    os.environ["CONFLUENCE_TOKEN"] = "token"
    os.environ["CONFLUENCE_SPACES"] = "DEV,OPS"
    os.environ["CONFLUENCE_USERNAME"] = "Test User"

    # Выполняем
    activity = fetch_confluence_activity(start_date, end_date)

    # Проверки
    assert isinstance(activity, list)
    assert len(activity) == 1  # только одна страница от нужного пользователя
    assert "Страница 1" in activity[0]["details"]
    assert "https://confluence.example.com/pages/viewpage.action?pageId=123" in activity[0]["details"]

    # Убедимся, что запросы по каждому пространству выполнены
    assert mock_confluence.get_all_pages_by_label.call_count == 2

