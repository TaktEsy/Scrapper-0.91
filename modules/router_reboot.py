# modules/router_reboot.py
import time
import socket
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from . import config, logger
from .ip_utils import get_current_ip

# Глобальный драйвер для переиспользования
_driver = None

def _get_driver():
    global _driver
    if _driver is not None:
        try:
            _driver.current_url
            return _driver
        except:
            _driver = None

    driver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'drivers', 'msedgedriver.exe')
    if not os.path.exists(driver_path):
        raise Exception(f"❌ Драйвер не найден: {driver_path}")

    options = EdgeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    # Окно будет свёрнутым, чтобы не мешать
    options.add_argument('--start-minimized')
    if config.ROUTER_BROWSER_HEADLESS:
        options.add_argument('--headless=new')

    options.binary_location = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    service = EdgeService(executable_path=driver_path)
    _driver = webdriver.Edge(service=service, options=options)
    return _driver

def _close_driver():
    """Закрывает драйвер при завершении работы программы (вызывается из main)."""
    global _driver
    if _driver:
        _driver.quit()
        _driver = None

def _get_selector(selector_dict):
    by_map = {
        'id': By.ID, 'name': By.NAME, 'xpath': By.XPATH, 'css': By.CSS_SELECTOR,
        'class': By.CLASS_NAME, 'tag': By.TAG_NAME, 'link': By.LINK_TEXT,
        'partial_link': By.PARTIAL_LINK_TEXT,
    }
    return by_map.get(selector_dict['by'].lower(), By.XPATH), selector_dict['value']

def _ensure_logged_in(driver):
    """
    Проверяет, открыта ли сессия. Если нет – выполняет вход.
    Возвращает True, если после проверки/входа находимся на защищённой странице.
    """
    # Сначала пробуем открыть страницу WAN
    logger.log_info(f"🌐 Переход на страницу WAN: {config.ROUTER_WAN_URL}")
    driver.get(config.ROUTER_WAN_URL)
    time.sleep(2)  # небольшая пауза для редиректа

    current_url = driver.current_url.lower()
    logger.log_info(f"Текущий URL после перехода: {current_url}")

    if "login" in current_url:
        logger.log_info("🔑 Сессия не активна, выполняем вход...")
        # Переходим на страницу логина
        driver.get(config.ROUTER_LOGIN_URL)
        time.sleep(1)

        try:
            username_by, username_val = _get_selector(config.ROUTER_USERNAME_SELECTOR)
            password_by, password_val = _get_selector(config.ROUTER_PASSWORD_SELECTOR)
            login_by, login_val = _get_selector(config.ROUTER_LOGIN_BUTTON_SELECTOR)

            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((username_by, username_val))
            )
            password_field = driver.find_element(password_by, password_val)
            login_button = driver.find_element(login_by, login_val)

            username_field.send_keys(config.ROUTER_USERNAME)
            password_field.send_keys(config.ROUTER_PASSWORD)
            login_button.click()
            logger.log_info("🔑 Данные введены, ожидаем входа...")
            time.sleep(3)  # даём время на редирект

            # Проверяем, что мы больше не на странице логина
            if "login" in driver.current_url.lower():
                logger.log_error("❌ Вход не удался (всё ещё на странице логина)")
                return False

            logger.log_info("✅ Вход выполнен успешно")
        except Exception as e:
            logger.log_error(f"❌ Ошибка при входе: {e}")
            return False
    else:
        # Уже на странице WAN или другой – проверяем, виден ли индикатор сессии
        try:
            success_by, success_val = _get_selector(config.ROUTER_SUCCESS_INDICATOR)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((success_by, success_val))
            )
            logger.log_info("✅ Сессия активна, вход не требуется")
        except TimeoutException:
            logger.log_warning("⚠️ Индикатор сессии не найден, но редиректа на логин не было. Возможно, страница другая.")
            # Продолжаем, может кнопка всё равно будет доступна
    return True

def _apply_wan_settings(driver):
    """Нажимает кнопку 'Применить изменения' на странице WAN."""
    try:
        apply_by, apply_val = _get_selector(config.ROUTER_APPLY_BUTTON_SELECTOR)
        apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((apply_by, apply_val))
        )
        apply_button.click()
        logger.log_info("✅ Кнопка 'Применить изменения' нажата")
        return True
    except Exception as e:
        logger.log_error(f"❌ Не удалось нажать кнопку: {e}")
        return False

def login_and_apply():
    """
    Запускает браузер, проверяет сессию, при необходимости логинится,
    затем нажимает кнопку 'Применить изменения'.
    """
    driver = None
    try:
        driver = _get_driver()

        # 1. Убедиться, что мы залогинены (и залогиниться, если нет)
        if not _ensure_logged_in(driver):
            logger.log_error("❌ Не удалось обеспечить авторизацию")
            return False

        # 2. Применить настройки WAN
        if not _apply_wan_settings(driver):
            return False

        # 3. Дать время роутеру перезапустить соединение
        time.sleep(5)
        return True

    except Exception as e:
        logger.log_error(f"❌ Ошибка в login_and_apply: {e}")
        return False
    # НЕ закрываем драйвер, оставляем для следующих вызовов

def reconnect_wan(max_attempts=2):
    if not config.ROUTER_REBOOT_ENABLED:
        return False

    old_ip = get_current_ip()
    logger.log_info(f"📌 Текущий IP до перезагрузки: {old_ip}")

    for attempt in range(1, max_attempts + 1):
        logger.log_info(f"🔄 Попытка {attempt}/{max_attempts} переподключения WAN...")
        if login_and_apply():
            logger.log_info("✅ Команда отправлена, ожидаем восстановления интернета...")
            if wait_for_internet(timeout=60):
                new_ip = get_current_ip()
                logger.log_info(f"📌 Новый IP: {new_ip}")
                if new_ip != old_ip:
                    logger.log_info(f"✅ IP успешно сменился: {old_ip} -> {new_ip}")
                    return True
                else:
                    logger.log_warning("⚠️ IP не изменился после переподключения.")
            else:
                logger.log_error("❌ Интернет не появился после переподключения.")
        else:
            logger.log_error(f"❌ Не удалось выполнить автоматизацию (попытка {attempt})")

        if attempt < max_attempts:
            logger.log_info("⏳ Ждём 10 сек перед следующей попыткой...")
            time.sleep(10)

    logger.log_error("🚫 Не удалось переподключить WAN после нескольких попыток.")
    return False

def wait_for_internet(host="8.8.8.8", port=53, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            time.sleep(2)
    return False

def cleanup():
    """Закрыть драйвер при выходе (вызывается из main)."""
    _close_driver()