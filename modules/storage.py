import os
from datetime import datetime
from . import config

def save_ids_to_file(ids, page_range, delay_range):
    """
    Сохраняет список ID в два файла (подробный и простой) внутри папки output.
    page_range: кортеж (min_page, max_page)
    delay_range: кортеж (min_delay, max_delay)
    Возвращает имена сохранённых файлов.
    """
    if not ids:
        return None, None

    # Создаём папку output, если её нет
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{config.OUTPUT_DIR}/ids_{timestamp}"
    detailed_file = base_filename + ".txt"
    simple_file = base_filename + "_simple.txt"

    # Убираем дубликаты и сортируем
    unique_ids = sorted(list(set(ids)))

    # Подробный файл
    with open(detailed_file, 'w', encoding='utf-8') as f:
        f.write(f"# Scrapper v0.9 - Собранные ID компаний\n")
        f.write(f"# Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"# Диапазон страниц: {page_range[0]} - {page_range[1]}\n")
        f.write(f"# Задержка: {delay_range[0]}-{delay_range[1]} сек\n")
        f.write(f"# Всего ID: {len(unique_ids)} (уникальных: {len(unique_ids)})\n")
        f.write("#" + "="*60 + "\n\n")
        f.write("ID компаний:\n")
        f.write(", ".join(unique_ids))
        f.write("\n\n" + "#" + "="*60 + "\n")
        f.write("# Построчный список:\n")
        for i, id_val in enumerate(unique_ids, 1):
            f.write(f"{i:4d}. {id_val}\n")

    # Простой файл (только ID через запятую)
    with open(simple_file, 'w', encoding='utf-8') as f:
        f.write(",".join(unique_ids))

    return detailed_file, simple_file