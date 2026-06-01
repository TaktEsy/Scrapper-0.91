# modules/proxy_manager.py
import requests
import random
import os
from . import config, logger

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0

    def load_proxies(self, test=True):
        if not config.USE_PROXIES:
            logger.log_info("Прокси отключены в настройках")
            return []

        if config.PROXY_MODE == "url":
            self._load_from_urls()
        elif config.PROXY_MODE == "file":
            self._load_from_file()
        else:
            logger.log_info("Режим прокси: none")
            return []

        self.proxies = list(set(self.proxies))
        logger.log_info(f"Загружено {len(self.proxies)} прокси (до проверки)")

        if test and self.proxies:
            self._test_and_filter_proxies()

        random.shuffle(self.proxies)
        logger.log_info(f"После проверки осталось {len(self.proxies)} рабочих прокси")
        return self.proxies

    def _load_from_urls(self):
        self.proxies = []
        for url in config.PROXY_URLS:
            try:
                logger.log_info(f"Загрузка прокси из {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    new_proxies = [
                        line.strip()
                        for line in response.text.strip().split('\n')
                        if line.strip() and ':' in line
                    ]
                    self.proxies.extend(new_proxies)
                    logger.log_info(f"Добавлено {len(new_proxies)} прокси из {url}")
                else:
                    logger.log_warning(f"Не удалось загрузить {url}: статус {response.status_code}")
            except Exception as e:
                logger.log_error(f"Ошибка загрузки {url}: {str(e)}")

    def _load_from_file(self):
        if not os.path.exists(config.PROXY_FILE):
            logger.log_warning(f"Файл {config.PROXY_FILE} не найден")
            self.proxies = []
            return
        try:
            with open(config.PROXY_FILE, 'r', encoding='utf-8') as f:
                self.proxies = [
                    line.strip()
                    for line in f
                    if line.strip() and ':' in line
                ]
            logger.log_info(f"Загружено {len(self.proxies)} прокси из {config.PROXY_FILE}")
        except Exception as e:
            logger.log_error(f"Ошибка чтения файла {config.PROXY_FILE}: {str(e)}")
            self.proxies = []

    def _test_and_filter_proxies(self):
        working = []
        test_url = "https://httpbin.org/ip"
        for proxy_str in self.proxies:
            proxy_dict = self._format_proxy(proxy_str)
            try:
                r = requests.get(
                    test_url,
                    proxies=proxy_dict,
                    timeout=config.PROXY_TEST_TIMEOUT,
                    verify=config.PROXY_VERIFY_SSL
                )
                if r.status_code == 200:
                    working.append(proxy_str)
                else:
                    logger.log_info(f"Прокси {proxy_str} не работает (статус {r.status_code})")
            except Exception as e:
                logger.log_info(f"Прокси {proxy_str} не работает: {type(e).__name__}")
        self.proxies = working

    def _format_proxy(self, proxy_str):
        """Возвращает словарь прокси в зависимости от типа"""
        proxy_str = proxy_str.strip()
        if '://' in proxy_str:
            proxy_str = proxy_str.split('://', 1)[1]
        if config.PROXY_TYPE == "socks5":
            return {
                'http': f'socks5://{proxy_str}',
                'https': f'socks5://{proxy_str}'
            }
        else:  # http
            return {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }

    def get_next_proxy(self):
        if not self.proxies:
            return None
        proxy_str = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return self._format_proxy(proxy_str)

# Глобальный экземпляр
proxy_manager = ProxyManager()