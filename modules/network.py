# modules/network.py
import time
import urllib3
import requests
import cloudscraper
from . import config, logger, user_agent
from . import router_reboot
from .ip_utils import get_current_ip
from .turnstile_solver import solve_turnstile

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_gui_log_callback = None

def set_gui_log_callback(callback):
    global _gui_log_callback
    _gui_log_callback = callback

def _gui_log(message):
    if _gui_log_callback:
        _gui_log_callback(message)

scraper = cloudscraper.create_scraper(
    interpreter=config.CLOUDSCRAPER_INTERPRETER,
    delay=config.CLOUDSCRAPER_DELAY,
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True,
        'mobile': False
    }
)

def is_turnstile_page(html):
    return ('cf-turnstile' in html) or ('Проверка, что Вы не робот' in html)

def fetch_page_with_retry(url, max_attempts=5, timeout=None):
    if timeout is None:
        timeout = config.REQUEST_TIMEOUT

    if not hasattr(fetch_page_with_retry, 'ip_logged'):
        ip = get_current_ip()
        _gui_log(f"🌍 Текущий внешний IP: {ip}")
        fetch_page_with_retry.ip_logged = True

    for attempt in range(1, max_attempts + 1):
        headers = config.HEADERS.copy()
        headers['User-Agent'] = user_agent.get_random_user_agent()

        try:
            logger.log_info(f"🌐 Запрос к {url} (попытка {attempt}/{max_attempts})")
            _gui_log(f"🌐 Запрос к {url} (попытка {attempt}/{max_attempts})")

            response = scraper.get(url, headers=headers, timeout=timeout)

            logger.log_info(f"📊 Статус: {response.status_code}")
            _gui_log(f"📊 Статус: {response.status_code}")

            if response.status_code == 200:
                if is_turnstile_page(response.text):
                    logger.log_warning("⚠️ Обнаружена страница проверки Turnstile. Запускаем браузер...")
                    _gui_log("⚠️ Обнаружена страница проверки Turnstile. Запускаем браузер...")
                    html = solve_turnstile(url, timeout=timeout)
                    if html:
                        logger.log_info("✅ Turnstile успешно пройден!")
                        _gui_log("✅ Turnstile успешно пройден!")
                        return html
                    else:
                        logger.log_error("❌ Не удалось пройти Turnstile.")
                        _gui_log("❌ Не удалось пройти Turnstile.")
                        continue
                else:
                    logger.log_info(f"✅ Страница загружена, размер: {len(response.text)}")
                    _gui_log(f"✅ Страница загружена, размер: {len(response.text)}")
                    return response.text
            else:
                logger.log_warning(f"⚠️ Статус {response.status_code}, пробуем следующую попытку...")
                _gui_log(f"⚠️ Статус {response.status_code}, пробуем следующую попытку...")
                continue

        except requests.exceptions.ConnectTimeout as e:
            logger.log_error(f"⏰ ERR_CONNECTION_TIMED_OUT (попытка {attempt}): {e}")
            _gui_log(f"⏰ ERR_CONNECTION_TIMED_OUT (попытка {attempt})")

            if attempt == max_attempts:
                logger.log_error("🚫 Все попытки исчерпаны")
                _gui_log("🚫 Все попытки исчерпаны")
                return None

            logger.log_info("🔄 Пытаемся переподключить WAN для смены IP...")
            _gui_log("🔄 Пытаемся переподключить WAN для смены IP...")
            if router_reboot.reconnect_wan():
                logger.log_info("✅ WAN переподключён, пробуем снова")
                _gui_log("✅ WAN переподключён, пробуем снова")
                get_current_ip()
                timeout += 10
                continue
            else:
                logger.log_error("❌ Не удалось переподключить WAN, ждём 20 сек...")
                _gui_log("❌ Не удалось переподключить WAN, ждём 20 сек...")
                time.sleep(20)

        except Exception as e:
            logger.log_error(f"❌ Другая ошибка: {type(e).__name__} - {e}")
            _gui_log(f"❌ Другая ошибка: {type(e).__name__}")
            if attempt == max_attempts:
                return None
            time.sleep(5)

    return None

fetch_page = fetch_page_with_retry