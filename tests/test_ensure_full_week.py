from datetime import date, timedelta
from report_generator.week_generator import ensure_full_week
from collections import defaultdict


def test_ensure_full_week_adds_days():
    # Пустой словарь событий
    grouped_by_date = {}

    # Тестовая неделя: с 01.07.2025 (вт) по 05.07.2025 (сб)
    week_start = date(2025, 6, 30)  # понедельник
    week_end = date(2025, 7, 4)     # пятница

    ensure_full_week(grouped_by_date, week_start, week_end, vacations=[])

    # Проверим, что рабочие дни (пн–пт) добавлены
    expected_days = [(week_start + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(5)]
    for day in expected_days:
        assert day in grouped_by_date
        assert isinstance(grouped_by_date[day], defaultdict)

    # Проверка наличия ежедневных меток (например, планёрки)
    for day in expected_days:
        assert "Ежедневная планёрка" in grouped_by_date[day]
        assert "Мониторинг" in grouped_by_date[day]

