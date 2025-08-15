import argparse
from datetime import datetime
from .config import logger, vacations
from .gitlab_fetcher import fetch_gitlab_events, process_gitlab_events
from .jira_fetcher import fetch_jira_activity
from .confluence_fetcher import fetch_confluence_activity
from .redmine_fetcher import fetch_redmine_activity
from .week_generator import get_week_ranges, ensure_full_week
from .pdf_builder import generate_pdf
from .uploader import upload_file_to_ftp, send_pdf_by_email


def main():
    parser = argparse.ArgumentParser(description="Генерация отчётов за указанный период.")
    parser.add_argument('--start', required=True, help='Дата начала (дд.мм.гггг)')
    parser.add_argument('--end', required=True, help='Дата окончания (дд.мм.гггг)')
    parser.add_argument('--email', action='store_true', help='Отправить отчёт по почте')
    parser.add_argument('--ftp', action='store_true', help='Загрузить отчёт на FTP')
    args = parser.parse_args()

    start_period = datetime.strptime(args.start, "%d.%m.%Y").date()
    end_period = datetime.strptime(args.end, "%d.%m.%Y").date()

    logger.info(f"Создание отчётов с {args.start} по {args.end}")
    week_ranges = get_week_ranges(start_period, end_period, vacations)

    for week_start, week_end in week_ranges:
        logger.info(f"Обработка недели: {week_start.strftime('%d.%m.%Y')} — {week_end.strftime('%d.%m.%Y')}")

        gitlab_events = fetch_gitlab_events(week_start, week_end)
        grouped_gitlab = process_gitlab_events(gitlab_events)

        jira_activities = fetch_jira_activity(week_start, week_end)
        confluence_activities = fetch_confluence_activity(week_start, week_end)
        redmine_activities = fetch_redmine_activity(week_start, week_end)

        # Объединяем всё в grouped_by_date
        grouped_by_date = grouped_gitlab
        for act in jira_activities + confluence_activities + redmine_activities:
            date = act['date']
            action = act['action']
            project = act['project']
            details = act['details']
            grouped_by_date[date][action][(project, details)].append("static")

        ensure_full_week(grouped_by_date, week_start, week_end, vacations)
        pdf_path = generate_pdf(grouped_by_date, week_start, week_end)

        if args.ftp:
            upload_file_to_ftp(pdf_path)
        if args.email:
            period_str = f"{week_start.strftime('%d.%m.%Y')}-{week_end.strftime('%d.%m.%Y')}"
            send_pdf_by_email(pdf_path, period_str)


if __name__ == "__main__":
    main()

