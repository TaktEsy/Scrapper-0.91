# modules/config.py
# Настройки приложения Scrapper v0.91

# ===== ОСНОВНЫЕ НАСТРОЙКИ =====
DEFAULT_URL = "https://www.list-org.com/search?type=all&work=on&is_email=on&p1_max=5000000&sort=param1&page=90"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
}

DEFAULT_MIN_PAGE = 1
DEFAULT_MAX_PAGE = 2
DEFAULT_MIN_DELAY = 5
DEFAULT_MAX_DELAY = 12
LOGS_DIR = "logs"
OUTPUT_DIR = "output"

# ===== НАСТРОЙКИ ПРОКСИ (отключены) =====
USE_PROXIES = False
PROXY_TYPE = "socks5"
PROXY_MODE = "url"
PROXY_URLS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/socks5.txt"
]
PROXY_FILE = "proxies.txt"
REFRESH_PROXIES_BEFORE_START = True
PROXY_VERIFY_SSL = False
PROXY_TEST_TIMEOUT = 10

# ===== НАСТРОЙКИ ПОВТОРНЫХ ПОПЫТОК =====
PAGE_RETRY_LIMIT = 3          # количество попыток для одной страницы при отсутствии data-id
PAGE_RETRY_DELAY = 2

MAX_RETRY_PASSES = 3

# ===== НАСТРОЙКИ CLOUDSCRAPER =====
CLOUDSCRAPER_DELAY = 15
CLOUDSCRAPER_INTERPRETER = 'js2py'  # или 'nodejs', если установлен
REQUEST_TIMEOUT = 30

# ===== НАСТРОЙКИ РОУТЕРА ДЛЯ ПЕРЕПОДКЛЮЧЕНИЯ WAN =====
ROUTER_REBOOT_ENABLED = True
ROUTER_USERNAME = "admin"          # замените на свой логин
ROUTER_PASSWORD = "password"       # замените на свой пароль

# URL страницы входа
ROUTER_LOGIN_URL = "http://..."

# Селекторы для формы входа (найдите через F12 на странице логина)
ROUTER_USERNAME_SELECTOR = {"by": "name", "value": "username"}   # пример: {"by": "name", "value": "username"}
ROUTER_PASSWORD_SELECTOR = {"by": "name", "value": "password"}   # пример: {"by": "name", "value": "password"}
ROUTER_LOGIN_BUTTON_SELECTOR = {"by": "xpath", "value": "//input[@type='submit' or @value='Авторизоваться']"}

# Селектор элемента, который появляется после успешного входа (например, ссылка на WAN)
ROUTER_SUCCESS_INDICATOR = {"by": "xpath", "value": "//a[contains(text(), 'WAN')] | //span[contains(text(), 'WAN')]"}

# URL страницы настроек WAN
ROUTER_WAN_URL = "http://192.168.0.1/admin/..."

# Селектор кнопки "Применить изменения" на странице WAN
ROUTER_APPLY_BUTTON_SELECTOR = {"by": "xpath", "value": "//input[@value='Применить изменения']"}

# Настройки браузера для автоматизации
ROUTER_BROWSER_START_MINIMIZED = True   # запускать окно свёрнутым
ROUTER_BROWSER_HEADLESS = False         # headless-режим (не рекомендуется для сложных JS)
ROUTER_REBOOT_USERNAME = "admin"
ROUTER_REBOOT_PASSWORD = "password"

