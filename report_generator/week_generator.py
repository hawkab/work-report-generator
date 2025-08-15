from collections import defaultdict
from datetime import datetime, timedelta
from random import choice, randint
from .config import RU_HOLIDAYS, vacations


def get_week_ranges(start_date, end_date, vacations_list=None):
    """
    Разбивает заданный период на рабочие недели (понедельник–пятница),
    исключая недели без рабочих дней.
    """
    if vacations_list is None:
        vacations_list = vacations

    weeks = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 0:  # понедельник
            week_start = current_date
            week_end = min(week_start + timedelta(days=4), end_date)

            is_working_week = any(
                d.weekday() < 5 and d not in RU_HOLIDAYS and not any(vs <= d <= ve for vs, ve in vacations_list)
                for d in (week_start + timedelta(days=i) for i in range(5))
            )
            if is_working_week:
                weeks.append((week_start, week_end))

            current_date += timedelta(days=7)
        else:
            current_date += timedelta(days=1)
    return weeks


def ensure_full_week(grouped_by_date, week_start, week_end, vacations_list=None):
    """
    Добавляет ежедневные плановые события и случайные активности для каждого рабочего дня недели.
    """
    if vacations_list is None:
        vacations_list = vacations

    all_days = [week_start + timedelta(days=i) for i in range(5)]
    work_days = [
        d for d in all_days
        if d.weekday() < 5 and d not in RU_HOLIDAYS and not any(start <= d <= end for start, end in vacations_list)
    ]
    formatted_days = [d.strftime("%d.%m.%Y") for d in work_days]

    for day in formatted_days:
        if day not in grouped_by_date:
            grouped_by_date[day] = defaultdict(lambda: defaultdict(list))

    for date_str in formatted_days:
        date_dt = datetime.strptime(date_str, "%d.%m.%Y")
        weekday = date_dt.weekday()

        grouped_by_date[date_str]["Проектные активности"][("ПРОЕКТ", "Участие в ежедневной командной планёрке, координация задач")]\
            .append("static")
        grouped_by_date[date_str]["Мониторинг"][("ПРОЕКТ", "Контроль метрик, состояния серверов и логов")]\
            .append("static")

        if weekday == 0:
            grouped_by_date[date_str]["Проектные активности"][("ПРОЕКТ", "Планирование работы: Оценка задач, постановка приоритетов")]\
                .append("static")
            grouped_by_date[date_str]["Проектные активности"][("ПРОЕКТ", "Подготовка отчёта за прошлую неделю")]\
                .append("static")

        if weekday == 4:
            grouped_by_date[date_str]["Проектные активности"][("ПРОЕКТ", "Ретроспектива недели: Обсуждение итогов недели, выводы")]\
                .append("static")


