# modules/ip_utils.py
import requests
from . import logger

def get_current_ip():
    """
    Узнаёт текущий внешний IP через сервис api.ipify.org.
    Возвращает строку с IP или 'Unknown' при ошибке.
    """
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        if response.status_code == 200:
            ip = response.json().get('ip', 'Unknown')
            logger.log_info(f"🌍 Текущий внешний IP: {ip}")
            return ip
        else:
            logger.log_warning(f"Не удалось получить IP (статус {response.status_code})")
            return 'Unknown'
    except Exception as e:
        logger.log_error(f"Ошибка при получении внешнего IP: {e}")
        return 'Unknown'