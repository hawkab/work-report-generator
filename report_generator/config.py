import os
from datetime import datetime
import holidays
from dotenv import load_dotenv
import logging
import colorlog
import json

# Загрузка .env
load_dotenv('./.env')

# Логирование
log_colors = {
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'bold_red',
}

# Формат с цветами
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)-8s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=log_colors
)

# Настраиваем handler с цветами
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Получаем логгер и очищаем старые хендлеры
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(console_handler)

# Основные переменные
RU_HOLIDAYS = holidays.RU()

vacations = []

# Кэш статусов Redmine
REDMINE_STATUS_CACHE = {}

# Переменные окружения (пример использования)
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_USERNAME = os.getenv("GITLAB_USERNAME")

def load_vacations(path="vacations.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    vacations = [
        (
            datetime.fromisoformat(entry["from"]).date(),
            datetime.fromisoformat(entry["to"]).date()
        )
        for entry in data
    ]
    return vacations


def print_logo():
    print(
        "\033[92m" +  # зелёный
        r"""
   __          __        _      _____                       _
   \ \        / /       | |    |  __ \                     | |
    \ \  /\  / ___  _ __| | __ | |__) |___ _ __   ___  _ __| |_
     \ \/  \/ / _ \| '__| |/ / |  _  // _ | '_ \ / _ \| '__| __|
      \  /\  | (_) | |  |   <  | | \ |  __| |_) | (_) | |  | |_
       \/__\/ \___/|_|  |_|\_\ |_|  \_\___| .__/ \___/|_|   \__|
      / ____|                         | | | |
     | |  __  ___ _ __   ___ _ __ __ _| |_|_|_  _ __
     | | |_ |/ _ | '_ \ / _ | '__/ _` | __/ _ \| '__|
     | |__| |  __| | | |  __| | | (_| | || (_) | |
      \_____|\___|_| |_|\___|_|  \__,_|\__\___/|_|
        """ +
        "\033[94m" +  # синий
        "\n         Work Report Generator © 2025 hawkab\n" +
        "\033[0m"     # сброс цвета
    )
print_logo()

vacations = load_vacations("vacations.json")

logger.info('Загружен vacations.json:')
for start, end in vacations:
    logger.info(f"Отпуск с {start} по {end}")