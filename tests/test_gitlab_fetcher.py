from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from report_generator.gitlab_fetcher import fetch_gitlab_events


@patch("gitlab.Gitlab")
def test_fetch_gitlab_events_success(mock_gitlab_cls):
    # Подставляем фиктивного пользователя и события
    mock_gitlab = MagicMock()
    mock_user = MagicMock()
    mock_event = MagicMock()
    mock_event.created_at = (date.today() - timedelta(days=1)).isoformat() + "T12:00:00Z"
    mock_event.action_name = "pushed to"
    mock_event.project_id = 123
    mock_event.push_data = {"commit_title": "Test commit", "commit_to": "abc123"}

    mock_user.events.list.side_effect = [[mock_event], []]  # Две страницы: одна с событием, одна пустая
    mock_gitlab.users.list.return_value = [mock_user]
    mock_gitlab_cls.return_value = mock_gitlab

    # Подменяем ENV-переменные
    import os
    os.environ["GITLAB_URL"] = "https://fake.gitlab"
    os.environ["GITLAB_TOKEN"] = "token"
    os.environ["GITLAB_USERNAME"] = "testuser"

    # Выполняем
    start = date.today() - timedelta(days=7)
    end = date.today()
    events = fetch_gitlab_events(start, end)

    # Проверка
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0].action_name == "pushed to"
    mock_gitlab.auth.assert_called_once()
    mock_gitlab.users.list.assert_called_once_with(username="testuser")

