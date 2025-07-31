from datetime import datetime
from atlassian import Confluence
from .config import logger
import os


def fetch_confluence_activity(start_date, end_date):
    user = os.getenv("CONFLUENCE_USERNAME")
    confluence = Confluence(
        url=os.getenv("CONFLUENCE_URL"),
        username=os.getenv("CONFLUENCE_USERNAME"),
        password=os.getenv("CONFLUENCE_API_TOKEN"),
        cloud=False
    )

    cql = (
        f"type=page AND lastmodified >= \"{start_date}\" AND lastmodified <= \"{end_date}\" "
        f"AND contributor = \"{user}\""
    )

    activities = []

    try:
        results = confluence.cql(cql, limit=100)
    except Exception as e:
        logger.error(f"Ошибка при выполнении CQL-запроса: {e}")
        results = {}

    for page in results.get("results", []):
        activity = classify_confluence_page(confluence, page)
        if activity:
            activities.append(activity)

    views = fetch_confluence_recent_views(confluence, start_date, end_date)
    activities.extend(views)

    return activities


def classify_confluence_page(confluence, page):
    try:
        page_id = page["content"]["id"]
        title = page["content"]["title"]
        last_modified_str = page["lastModified"][:10]
        date = datetime.strptime(last_modified_str, "%Y-%m-%d").strftime("%d.%m.%Y")
        project_name = page.get("resultGlobalContainer", {}).get("title", "Confluence")

        # История страницы
        history = confluence.get(f'rest/api/content/{page_id}/history')
        created_by = history.get("createdBy", {}).get("accountId") or history.get("createdBy", {}).get("username")
        created_date = datetime.strptime(history.get("createdDate").split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
        last_updated_by = history.get("lastUpdated", {}).get("by", {}).get("accountId") or \
                          history.get("lastUpdated", {}).get("by", {}).get("username")
        version = history.get("lastUpdated", {}).get("number", 1)
        current_user = os.getenv("JIRA_USERNAME")

        if created_by == current_user and created_date == date:
            action = f"Создал новую страницу и {version} раз вносил доработки"
        elif last_updated_by == current_user:
            action = "Редактировал страницу Confluence"
        else:
            action = "Изучал документацию в Confluence"

        return {
            "date": date,
            "action": "Ведение базы знаний",
            "project": project_name,
            "details": f"{action}: '{title}'"
        }
    except Exception as e:
        logger.warning(f"Ошибка при обработке страницы Confluence: {e}")
        return None


def fetch_confluence_recent_views(confluence, start_date, end_date):
    activities = []
    try:
        resp = confluence.get("/rest/recentlyviewed/1.0/recent")
    except Exception as e:
        logger.warning(f"Ошибка при получении истории просмотров Confluence: {e}")
        return activities

    for entry in resp:
        try:
            timestamp = datetime.fromtimestamp(entry["lastSeen"] / 1000)
            if start_date <= timestamp.date() <= end_date:
                activities.append({
                    "date": timestamp.strftime("%d.%m.%Y"),
                    "action": "Анализ",
                    "project": "ПРОЕКТ",
                    "details": f"Анализировал документацию: '{entry['title']}'"
                })
        except Exception as e:
            logger.warning(f"Ошибка в формате данных просмотров: {e}")
            continue

    return activities

