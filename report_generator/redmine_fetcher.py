from datetime import datetime
from redminelib import Redmine
from .config import logger, REDMINE_STATUS_CACHE
import os


def get_status_name(redmine, status_id):
    """
    Кешированное получение имени статуса Redmine по ID.
    """
    if status_id not in REDMINE_STATUS_CACHE:
        for status in redmine.issue_status.all():
            REDMINE_STATUS_CACHE[str(status.id)] = status.name
    return REDMINE_STATUS_CACHE.get(status_id, f"#{status_id}")


def fetch_redmine_activity(start_date, end_date):
    redmine = Redmine(
        os.getenv("REDMINE_URL"),
        key=os.getenv("REDMINE_API_KEY")
    )
    user_id = int(os.getenv("REDMINE_USER_ID"))
    activities = []

    # 1. Списание трудозатрат
    try:
        time_entries = redmine.time_entry.filter(
            user_id=user_id,
            from_date=start_date,
            to_date=end_date
        )
        for entry in time_entries:
            activities.append({
                "date": entry.spent_on.strftime('%d.%m.%Y'),
                "action": "Ведение Redmine",
                "project": "ПРОЕКТ",
                "details": f"Списание {entry.hours} ч: {entry.comments or 'без комментария'}"
            })
    except Exception as e:
        logger.warning(f"Ошибка при получении трудозатрат Redmine: {e}")

    # 2. Журналы задач: статусы, комментарии
    try:
        issues = redmine.issue.filter(
            assigned_to_id=user_id,
            status_id='*',
            updated_on=f"><{start_date}|{end_date}"
        )
    except Exception as e:
        logger.warning(f"Ошибка при получении задач Redmine: {e}")
        return activities

    for issue in issues:
        try:
            journals = issue.journals
        except Exception:
            continue  # нет доступа к журналу

        for journal in journals:
            if journal.user.id != user_id:
                continue

            journal_date = journal.created_on.strftime('%d.%m.%Y')

            for detail in journal.details:
                if detail.get('property') == 'attr' and detail.get('name') == 'status_id':
                    old_status = get_status_name(redmine, detail.get('old_value'))
                    new_status = get_status_name(redmine, detail.get('new_value'))
                    activities.append({
                        "date": journal_date,
                        "action": "Ведение Redmine",
                        "project": "ПРОЕКТ",
                        "details": f"Изменил статус задачи #{issue.id}: {old_status} → {new_status}"
                    })

            if journal.notes:
                activities.append({
                    "date": journal_date,
                    "action": "Ведение Redmine",
                    "project": "ПРОЕКТ",
                    "details": f"Комментарий к задаче #{issue.id}: '{journal.notes}'"
                })

    return activities

