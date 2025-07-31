from datetime import date
from report_generator.week_generator import get_week_ranges


def test_get_week_ranges_basic():
    # Период с понедельника по пятницу включительно
    start = date(2025, 7, 1)   # Вторник
    end = date(2025, 7, 31)    # Среда

    weeks = get_week_ranges(start, end)

    # Проверка, что возвращены только недели с понедельников
    assert all(week[0].weekday() == 0 for week in weeks)  # Понедельник
    assert all((week[1] - week[0]).days <= 4 for week in weeks)  # <= 5 дней

    # Проверка, что диапазоны входят в указанный интервал
    assert weeks[0][0] >= date(2025, 7, 1)
    assert weeks[-1][1] <= date(2025, 7, 31)
    assert isinstance(weeks, list)
    assert all(isinstance(t, tuple) and len(t) == 2 for t in weeks)

