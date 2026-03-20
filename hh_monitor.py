"""
HH.ru Vacancy Monitor
Отслеживает новые вакансии работодателя и отправляет уведомления в Telegram.
"""

import json
import logging
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────
load_dotenv()

EMPLOYER_ID = "YOUR_EMPLOYER_ID"
HH_API_URL = f"https://api.hh.ru/vacancies?employer_id={EMPLOYER_ID}&per_page=20"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VACANCIES_FILE = Path("vacancies.json")
REQUEST_TIMEOUT = 10  # секунды

# ──────────────────────────────────────────────
# Логирование
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Работа с файлом вакансий
# ──────────────────────────────────────────────
def load_sent_vacancies() -> set:
    """Загружает ID уже отправленных вакансий из JSON-файла."""
    if not VACANCIES_FILE.exists():
        logger.info("Файл %s не найден — создаём новый.", VACANCIES_FILE)
        return set()
    try:
        with VACANCIES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("sent_ids", []))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Ошибка чтения %s: %s", VACANCIES_FILE, e)
        return set()


def save_sent_vacancies(sent_ids: set) -> None:
    """Сохраняет ID отправленных вакансий в JSON-файл."""
    try:
        with VACANCIES_FILE.open("w", encoding="utf-8") as f:
            json.dump({"sent_ids": list(sent_ids)}, f, ensure_ascii=False, indent=2)
        logger.debug("Файл %s обновлён (%d записей).", VACANCIES_FILE, len(sent_ids))
    except OSError as e:
        logger.error("Ошибка записи %s: %s", VACANCIES_FILE, e)


# ──────────────────────────────────────────────
# HH API
# ──────────────────────────────────────────────
def fetch_vacancies() -> list[dict]:
    """
    Получает список вакансий с HH API.
    Возвращает список словарей с полями: id, name, alternate_url, published_at.
    """
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
    try:
        response = requests.get(HH_API_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        vacancies = [
            {
                "id": item["id"],
                "name": item["name"],
                "alternate_url": item["alternate_url"],
                "published_at": item.get("published_at", "—"),
            }
            for item in data.get("items", [])
        ]
        logger.info("Получено вакансий с HH: %d", len(vacancies))
        return vacancies
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к HH API.")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с HH API.")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP-ошибка HH API: %s", e)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Ошибка разбора ответа HH API: %s", e)
    return []


# ──────────────────────────────────────────────
# Telegram
# ──────────────────────────────────────────────
def send_telegram_message(text: str) -> bool:
    """Отправляет сообщение в Telegram через Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error(
            "TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы в .env"
        )
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info("Сообщение отправлено в Telegram.")
        return True
    except requests.exceptions.Timeout:
        logger.error("Таймаут при отправке в Telegram.")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с Telegram API.")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP-ошибка Telegram API: %s", e)
    return False


def format_message(vacancy: dict) -> str:
    """Форматирует сообщение о новой вакансии."""
    # Форматируем дату: 2024-05-01T10:00:00+0300 → 01.05.2024
    raw_date = vacancy.get("published_at", "")
    try:
        date_str = raw_date[:10]  # берём YYYY-MM-DD
        y, m, d = date_str.split("-")
        formatted_date = f"{d}.{m}.{y}"
    except (ValueError, AttributeError):
        formatted_date = raw_date or "—"

    return (
        "🚀 <b>Новая вакансия!</b>\n\n"
        f"📌 {vacancy['name']}\n"
        f"🔗 <a href=\"{vacancy['alternate_url']}\">Открыть на HH</a>\n"
        f"📅 {formatted_date}"
    )


# ──────────────────────────────────────────────
# Основная логика
# ──────────────────────────────────────────────
def check_new_vacancies() -> None:
    """Проверяет новые вакансии и отправляет уведомления."""
    sent_ids = load_sent_vacancies()
    vacancies = fetch_vacancies()

    if not vacancies:
        logger.warning("Список вакансий пуст или не получен.")
        return

    new_count = 0
    for vacancy in vacancies:
        vacancy_id = str(vacancy["id"])
        if vacancy_id not in sent_ids:
            logger.info("Новая вакансия: [%s] %s", vacancy_id, vacancy["name"])
            message = format_message(vacancy)
            success = send_telegram_message(message)
            if success:
                sent_ids.add(vacancy_id)
                new_count += 1
                # Пауза между сообщениями, чтобы не попасть под rate limit
                time.sleep(1)

    save_sent_vacancies(sent_ids)

    if new_count == 0:
        logger.info("Новых вакансий не найдено.")
    else:
        logger.info("Отправлено новых уведомлений: %d", new_count)


def main() -> None:
    logger.info("=" * 50)
    logger.info("HH Vacancy Monitor запущен.")
    check_new_vacancies()
    logger.info("Проверка завершена.")
    logger.info("=" * 50)


if __name__ == "__main__":
    logger.info("Запуск в режиме бесконечного цикла. Интервал: 5 минут.")
    while True:
        main()
        logger.info("Следующая проверка через 5 минут...")
        time.sleep(300)
