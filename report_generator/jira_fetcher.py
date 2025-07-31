from datetime import datetime
from atlassian import Jira
from .utils import shorten_name_auto, wrap_text
from .config import logger
import os


def fetch_jira_activity(start_date, end_date):
    jira = Jira(
        url=os.getenv("JIRA_SERVER"),
        username=os.getenv("JIRA_USERNAME"),
        password=os.getenv("JIRA_TOKEN"),
        cloud=False
    )

    jql = (
        f'updated >= "{start_date}" AND updated <= "{end_date}" '
        f'AND assignee = "{os.getenv("JIRA_USERNAME")}" ORDER BY updated ASC'
    )

    try:
        issues = jira.jql(jql).get('issues', [])
    except Exception as e:
        logger.error(f"Ошибка при выполнении JQL-запроса: {e}")
        return []

    activities = []

    for issue in issues:
        issue_key = issue['key']
        fields = issue['fields']
        updated = fields['updated'].split('T')[0]
        date = datetime.strptime(updated, '%Y-%m-%d').strftime('%d.%m.%Y')
        summary = fields.get('summary', '')
        status = fields.get('status', {}).get('name', '')
        project_name = fields['project']['name']

        # Основное изменение
        activities.append({
            'date': date,
            'action': 'Ведение JIRA',
            'project': shorten_name_auto(project_name),
            'details': f'Перевёл в "{status}" задачу {issue_key} {shorten_name_auto(wrap_text(summary), 300)}'
        })

        # Комментарии
        try:
            comments_data = jira.get(f'rest/api/2/issue/{issue_key}/comment')
        except Exception as e:
            logger.warning(f"Ошибка при получении комментариев по задаче {issue_key}: {e}")
            continue

        for comment in comments_data.get('comments', []):
            author = comment['author'].get('name') or comment['author'].get('displayName')
            if author != os.getenv("JIRA_USERNAME"):
                continue

            comment_date = comment['created'].split('T')[0]
            comment_date = datetime.strptime(comment_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            if not (start_date <= datetime.strptime(comment_date, '%d.%m.%Y').date() <= end_date):
                continue

            comment_body = comment.get('body', '').strip()
            activities.append({
                'date': comment_date,
                'action': 'Ведение JIRA',
                'project': shorten_name_auto(project_name),
                'details': f'В задаче "{issue_key}" написал коммент: {shorten_name_auto(wrap_text(comment_body), 300)}'
            })

    return activities

