# modules/turnstile_solver.py
import time
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from . import logger

def solve_turnstile(url, timeout=45):
    """
    Открывает страницу с защитой Cloudflare в реальном браузере,
    ждёт автоматического прохождения проверки (без ручных кликов)
    и возвращает HTML целевой страницы с data-id.
    """
    driver = None
    try:
        logger.log_info("🚀 Запуск браузера Edge для автоматического прохождения Cloudflare...")

        driver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'drivers', 'msedgedriver.exe')
        if not os.path.exists(driver_path):
            raise Exception(f"❌ Драйвер не найден: {driver_path}")

        options = EdgeOptions()
        # Критические настройки для скрытия автоматизации
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--start-minimized')  # окно свёрнуто, чтобы не мешать
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        options.binary_location = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"

        service = EdgeService(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=options)

        # Дополнительное скрытие автоматизации
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.log_info(f"🌐 Загрузка страницы: {url}")
        driver.get(url)

        # Если сразу есть data-id – возвращаем HTML (редкий случай)
        if _has_data_id(driver):
            logger.log_info("✅ Страница с результатами загружена сразу (без проверки).")
            return driver.page_source

        # Ожидаем, пока URL вернётся к исходному (без /bot)
        # Это главный признак, что Cloudflare пройден
        original_path = url.split('/search')[1] if '/search' in url else ''
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: '/bot' not in d.current_url and original_path in d.current_url
            )
            logger.log_info(f"✅ URL вернулся к исходному после проверки: {driver.current_url}")
        except TimeoutException:
            logger.log_warning("⚠️ Редирект на исходный URL не произошёл за отведённое время.")
            # Проверим, может, мы уже на нужной странице?
            if _has_data_id(driver):
                logger.log_info("✅ Но data-id присутствуют – считаем успехом.")
            else:
                logger.log_error("❌ Проверка Cloudflare не пройдена (таймаут редиректа).")
                return None

        # Дополнительно ждём появления data-id (до 15 секунд)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-id]'))
            )
            logger.log_info("✅ Элементы с data-id появились на странице.")
        except TimeoutException:
            logger.log_warning("⚠️ Элементы с data-id не найдены после ожидания. Возможно, страница пуста.")
            # Отладочный вывод
            debug_html = driver.page_source[:500]
            logger.log_info(f"📄 Первые 500 символов страницы: {debug_html}")

        html = driver.page_source
        logger.log_info(f"📄 Страница после проверки загружена, размер: {len(html)}")
        return html

    except WebDriverException as e:
        logger.log_error(f"❌ WebDriver ошибка: {e}")
        return None
    except Exception as e:
        logger.log_error(f"❌ Непредвиденная ошибка: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def _has_data_id(driver):
    """Проверяет, есть ли на странице элементы с атрибутом data-id."""
    try:
        driver.find_element(By.CSS_SELECTOR, '[data-id]')
        return True
    except:
        return False