# modules/parser.py
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_ids_from_html(html):
    """
    Извлекает все значения data-id из HTML, используя парсер lxml.
    Возвращает список уникальных ID.
    """
    if not html:
        logger.warning("Получен пустой HTML")
        return []

    # Используем lxml для более надёжного парсинга
    soup = BeautifulSoup(html, 'lxml')

    # Ищем любые теги с атрибутом data-id
    elements = soup.find_all(attrs={'data-id': True})

    # Для отладки: выводим количество найденных элементов
    logger.info(f"Найдено элементов с data-id: {len(elements)}")

    if not elements:
        # Если ничего не найдено, возможно, data-id есть только у input
        # Попробуем искать конкретно input
        elements = soup.find_all('input', attrs={'data-id': True})
        logger.info(f"Поиск только input с data-id: {len(elements)}")

    # Собираем ID
    ids = []
    for elem in elements:
        id_val = elem.get('data-id')
        if id_val:
            ids.append(id_val.strip())

    # Убираем дубликаты и возвращаем
    unique_ids = list(set(ids))
    logger.info(f"Уникальных ID: {len(unique_ids)}")
    return unique_ids