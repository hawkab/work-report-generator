import textwrap
from datetime import datetime, timedelta


def shorten_name_auto(name: str, max_len: int = 7) -> str:
    """
    Автоматически обрезает имя, если оно превышает max_len символов.
    """
    return name[:max_len] if len(name) > max_len else name


def wrap_text(text: str, width: int = 80) -> str:
    """
    Переносит длинный текст по ширине для лучшей читаемости в PDF.
    """
    return '\n'.join(textwrap.wrap(text, width))


def get_last_week_dates() -> tuple[datetime.date, datetime.date]:
    """
    Возвращает понедельник и пятницу предыдущей недели.
    """
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_friday = last_monday + timedelta(days=4)
    return last_monday.date(), last_friday.date()


def daterange(start_date: datetime.date, end_date: datetime.date):
    """
    Генератор дат в интервале [start_date, end_date].
    """
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

