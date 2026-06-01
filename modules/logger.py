# modules/logger.py
import logging
import os
from datetime import datetime
from . import config

_loggers = {}

def setup_logging():
    """Настраивает корневой логгер и логгер для запросов с гарантией записи в файл."""
    try:
        # Создаём папку для логов, если её нет
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        print(f"📁 Папка для логов: {os.path.abspath(config.LOGS_DIR)}")
    except Exception as e:
        print(f"❌ Не удалось создать папку логов: {e}")
        # Пробуем использовать текущую директорию как запасной вариант
        config.LOGS_DIR = "."
        print(f"⚠️ Логи будут сохраняться в текущую папку: {os.path.abspath('.')}")

    log_filename = os.path.join(config.LOGS_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.txt")
    print(f"📄 Файл лога: {os.path.abspath(log_filename)}")

    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8', mode='a'),
            logging.StreamHandler()
        ],
        force=True  # переопределяем предыдущие настройки
    )

    # Отдельный логгер для запросов
    request_logger = logging.getLogger('requests')
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False

    try:
        request_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a')
        request_handler.setFormatter(logging.Formatter('%(asctime)s - REQUEST - %(message)s'))
        request_logger.addHandler(request_handler)
    except Exception as e:
        print(f"❌ Не удалось создать файл лога запросов: {e}")

    _loggers['main'] = logging.getLogger('main')
    _loggers['request'] = request_logger
    logging.getLogger('main').info("🟢 Логирование запущено")

def log_info(message):
    _loggers.get('main', logging.getLogger()).info(message)

def log_warning(message):
    _loggers.get('main', logging.getLogger()).warning(message)

def log_error(message):
    _loggers.get('main', logging.getLogger()).error(message)

def log_request(method, url, status_code=None, response_time=None):
    msg = f"{method} {url}"
    if status_code:
        msg += f" - Status: {status_code}"
    if response_time:
        msg += f" - Time: {response_time:.2f}s"
    _loggers.get('request', logging.getLogger('requests')).info(msg)