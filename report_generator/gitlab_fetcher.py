from datetime import datetime, timedelta
from collections import defaultdict
from .utils import shorten_name_auto, wrap_text
from .config import logger, GITLAB_URL, GITLAB_TOKEN, GITLAB_USERNAME
import traceback

import gitlab

gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)

def get_project_name(project_id, cache):
    if project_id in cache:
        return cache[project_id]
    try:
        project = gl.projects.get(project_id)
        cache[project_id] = project.name
        return project.name
    except Exception:
        logger.warning(f"Не удалось получить имя проекта {project_id} {traceback.format_exc()}")
        cache[project_id] = f'Проект {project_id}'
        return cache[project_id]


def fetch_gitlab_events(start_date, end_date):
    events = []
    try:
        
        gl.auth()
        users = gl.users.list(username=GITLAB_USERNAME)
        if not users:
            logger.error("Пользователь не найден.")
            return []
        user = users[0]
        page, per_page = 1, 100

        while True:
            page_events = user.events.list(
                after=(start_date - timedelta(days=1)).isoformat(),
                before=(end_date + timedelta(days=3)).isoformat(),
                sort='asc',
                page=page,
                per_page=per_page
            )
            if not page_events:
                break
            events.extend(page_events)
            page += 1
        return events
    except Exception as e:
        logger.error(f"Ошибка при получении событий GitLab: {e} {traceback.format_exc()}")
        return []


def process_gitlab_events(events, start_date, end_date):
    grouped_by_date = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    project_cache = {}

    action_translations = {
        'pushed to': 'Git: Работал над задачей',
        'pushed new': 'Git: Начал новую задачу',
        'opened': 'Git: Оформил новый MR',
        'approved': 'Git: Согласовал изменения',
        'accepted': 'Git: Принял работу по задаче',
        'commented on': 'Git: Провёл code-review',
        'deleted': 'Оптимизация',
        'merged': 'Объединил изменения в основную ветку',
        'closed': 'Git: Закрыл задачу/запрос',
        'created': 'Git: Создание/загрузка',
        'joined': 'Git: Доступ',
    }

    for event in events:
        raw_date = datetime.strptime(event.created_at.split('T')[0], "%Y-%m-%d")
        if not (start_date <= raw_date.date() <= end_date):
            continue

        date = raw_date.strftime("%d.%m.%Y")
        action = event.action_name
        project_id = event.project_id
        project_name = get_project_name(project_id, project_cache)
        action_desc = action_translations.get(action, action)

        if action == 'pushed to':
            msg = event.push_data.get('commit_title', 'работа над задачей')
            commit_id = event.push_data.get('commit_to', 'работа над задачей')
            details = f"{msg} commit to: {commit_id}"
        elif action == 'deleted':
            ref = event.push_data.get('ref', 'ветка без названия')
            details = f"Удалена неактуальная ветка: {ref}"
        elif action == 'commented on':
            comment = shorten_name_auto(event.note['body'], 500) + "..."
            details = f"Комментарий (code review): '{wrap_text(comment)}'"
        elif action in ['opened', 'approved', 'accepted', 'merged', 'closed']:
            target = getattr(event, 'target_title', '') or 'задача/запрос'
            details = target
        elif action == 'created':
            details = f"Создан репозиторий {project_name}"
        elif action == 'joined':
            details = f"Получен доступ к проекту '{project_name}'"
        else:
            ref = event.push_data.get('ref', '(не указана ветка)')
            commit_id = event.push_data.get('commit_to', 'работа над задачей')
            details = f"Работа в ветке '{ref}' commit to: {commit_id}"

        grouped_by_date[date][action_desc][(shorten_name_auto(project_name), details)].append(event)

    return grouped_by_date

