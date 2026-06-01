"""
Scrapper v0.91
Модульная версия парсера сайта list-org.com
Интуитивные подписи: Начальная / Конечная страница
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from urllib.parse import urlparse, parse_qs, urlencode
from threading import Thread
import time
import random
import os

# Импортируем наши модули
from modules import config, logger, network, parser, storage
from modules.network import set_gui_log_callback  # для связи с GUI
from modules.router_reboot import cleanup  # для закрытия драйвера при выходе


class Scrapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrapper v0.91")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        self.root.minsize(650, 550)

        # Настройка логирования (один раз)
        logger.setup_logging()

        # Устанавливаем callback для отправки сообщений в GUI
        set_gui_log_callback(self.log)

        # Настройка цветовой схемы
        self.setup_styles()

        # Переменные для сбора ID
        self.all_ids = []
        self.parsing_active = False
        self.paused = False

        # Счётчики страниц
        self.processed_pages = 0      # всего обработано страниц (включая повторные попытки)
        self.successful_pages = 0     # страницы, где найдены ID

        # Список страниц, на которых не найдены ID (после всех попыток в основном проходе)
        self.failed_pages = []
        self.current_retry_pass = 0
        self.max_retry_passes = getattr(config, 'MAX_RETRY_PASSES', 2)  # из конфига

        # Задержки (будут обновляться из GUI)
        self.min_delay = config.DEFAULT_MIN_DELAY
        self.max_delay = config.DEFAULT_MAX_DELAY

        # Создание интерфейса
        self.create_widgets()

        logger.log_info("Приложение запущено")

    def setup_styles(self):
        self.bg_color = "#f0f0f0"
        self.button_color = "#4CAF50"
        self.button_text_color = "white"
        self.parse_button_color = "#4CAF50"          # зелёный для Play
        self.pause_button_color = "#FFC107"          # жёлтый для Pause
        self.save_button_color = "#2196F3"
        self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        # Основной контейнер
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Верхняя часть (URL) ---
        top_frame = tk.Frame(main_container, bg=self.bg_color)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_frame, text="URL для парсинга:", bg=self.bg_color,
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.url_entry = tk.Entry(top_frame, font=("Arial", 10), bd=2,
                                   relief=tk.GROOVE, state="readonly",
                                   readonlybackground="white")
        self.url_entry.pack(fill=tk.X)

        self.url_entry.configure(state="normal")
        self.url_entry.insert(0, config.DEFAULT_URL)
        self.url_entry.configure(state="readonly")

        # --- Вторая строка: выбор диапазона страниц (поля ввода только цифр) ---
        dropdown_frame = tk.Frame(main_container, bg=self.bg_color)
        dropdown_frame.pack(fill=tk.X, pady=(0, 15))

        # Валидация на ввод только цифр
        vcmd = (self.root.register(self._validate_numeric), '%P')

        # Начальная страница
        start_frame = tk.Frame(dropdown_frame, bg=self.bg_color)
        start_frame.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(start_frame, text="Начальная страница:", bg=self.bg_color,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.start_entry = tk.Entry(start_frame, width=10, justify='center',
                                    validate='key', validatecommand=vcmd)
        self.start_entry.pack(side=tk.LEFT)
        self.start_entry.insert(0, str(config.DEFAULT_MIN_PAGE))
        self.start_entry.bind("<FocusOut>", self._validate_page_range)

        # Конечная страница
        end_frame = tk.Frame(dropdown_frame, bg=self.bg_color)
        end_frame.pack(side=tk.LEFT)
        tk.Label(end_frame, text="Конечная страница:", bg=self.bg_color,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.end_entry = tk.Entry(end_frame, width=10, justify='center',
                                  validate='key', validatecommand=vcmd)
        self.end_entry.pack(side=tk.LEFT)
        self.end_entry.insert(0, str(config.DEFAULT_MAX_PAGE))
        self.end_entry.bind("<FocusOut>", self._validate_page_range)

        # --- Третья строка: настройка задержек ---
        delay_frame = tk.Frame(main_container, bg=self.bg_color)
        delay_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(delay_frame, text="Задержка между запросами:", bg=self.bg_color,
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(delay_frame, text="от", bg=self.bg_color,
                 font=("Arial", 9)).pack(side=tk.LEFT)
        self.min_delay_spinbox = tk.Spinbox(delay_frame, from_=1, to=30,
                                             width=5, font=("Arial", 9),
                                             command=self.update_delays)
        self.min_delay_spinbox.pack(side=tk.LEFT, padx=(2, 5))
        self.min_delay_spinbox.delete(0, tk.END)
        self.min_delay_spinbox.insert(0, str(self.min_delay))

        tk.Label(delay_frame, text="до", bg=self.bg_color,
                 font=("Arial", 9)).pack(side=tk.LEFT)
        self.max_delay_spinbox = tk.Spinbox(delay_frame, from_=1, to=30,
                                             width=5, font=("Arial", 9),
                                             command=self.update_delays)
        self.max_delay_spinbox.pack(side=tk.LEFT, padx=(2, 10))
        self.max_delay_spinbox.delete(0, tk.END)
        self.max_delay_spinbox.insert(0, str(self.max_delay))

        tk.Label(delay_frame, text="секунд (случайно)", bg=self.bg_color,
                 font=("Arial", 9)).pack(side=tk.LEFT)

        # --- Четвёртая строка: кнопки ---
        button_frame = tk.Frame(main_container, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 20))

        # Кнопка Play (зелёная)
        self.parse_button = tk.Button(button_frame,
            text="▶ Старт", font=("Arial", 11, "bold"),
            bg=self.parse_button_color, fg=self.button_text_color,
            bd=0, padx=20, pady=8, cursor="hand2",
            command=self.start_parsing)
        self.parse_button.pack(side=tk.LEFT, padx=(0, 10))
        self.create_tooltip(self.parse_button, "Начать сбор ID компаний с сайта")

        # Кнопка Pause (жёлтая, изначально скрыта)
        self.pause_button = tk.Button(button_frame,
            text="⏸", font=("Arial", 14, "bold"),
            bg=self.pause_button_color, fg="black",
            bd=0, padx=20, pady=8, cursor="hand2",
            command=self.toggle_pause)
        self.pause_button.pack_forget()  # скрыта до старта
        self.create_tooltip(self.pause_button, "Приостановить парсинг")

        # Кнопка Stop (красная, изначально скрыта)
        self.stop_button = tk.Button(button_frame,
            text="⏹", font=("Arial", 14, "bold"),
            bg="#f44336", fg="white",
            bd=0, padx=20, pady=8, cursor="hand2",
            command=self.stop_parsing)
        self.stop_button.pack_forget()  # скрываем до старта
        self.create_tooltip(self.stop_button, "Остановить парсинг")

        self.save_button = tk.Button(button_frame,
            text="💾 Сохранить ID", font=("Arial", 11, "bold"),
            bg=self.save_button_color, fg=self.button_text_color,
            bd=0, padx=20, pady=8, cursor="hand2",
            command=self.save_ids_to_file, state="disabled")
        self.save_button.pack(side=tk.LEFT, padx=(10,0))
        self.create_tooltip(self.save_button, "Сохранить собранные ID в текстовый файл")

        self.progress = ttk.Progressbar(button_frame, mode='determinate', length=200)
        self.progress.pack(side=tk.LEFT, padx=(20, 0), expand=True, fill=tk.X)
        self.progress.pack_forget()

        # --- Счётчики ID и страниц ---
        counter_frame = tk.Frame(main_container, bg=self.bg_color)
        counter_frame.pack(fill=tk.X, pady=(0, 10))

        # Счётчик ID
        tk.Label(counter_frame, text="Собрано ID:", bg=self.bg_color,
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.id_counter_label = tk.Label(counter_frame, text="0",
                                         bg=self.bg_color,
                                         font=("Arial", 12, "bold"),
                                         fg="#4CAF50")
        self.id_counter_label.pack(side=tk.LEFT, padx=(5, 20))

        # Счётчик пройденных страниц (успешных)
        tk.Label(counter_frame, text="Пройдено страниц:", bg=self.bg_color,
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.passed_pages_label = tk.Label(counter_frame, text="0",
                                           bg=self.bg_color,
                                           font=("Arial", 12, "bold"),
                                           fg="#2196F3")
        self.passed_pages_label.pack(side=tk.LEFT, padx=(5, 20))

        # Счётчик потерянных страниц (где ID не найдены)
        tk.Label(counter_frame, text="Потеряно страниц:", bg=self.bg_color,
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.lost_pages_label = tk.Label(counter_frame, text="0",
                                         bg=self.bg_color,
                                         font=("Arial", 12, "bold"),
                                         fg="#f44336")
        self.lost_pages_label.pack(side=tk.LEFT, padx=(5, 0))

        # --- Лог-окно ---
        log_label_frame = tk.Frame(main_container, bg=self.bg_color)
        log_label_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(log_label_frame, text="Лог парсинга:", bg=self.bg_color,
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(main_container,
            font=("Courier", 10), wrap=tk.WORD, bd=2, relief=tk.GROOVE,
            bg="white", height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Автоанализ URL при старте
        self.root.after(100, self.analyze_url)

        # --- Нижняя панель ---
        bottom_frame = tk.Frame(main_container, bg=self.bg_color)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = tk.Label(bottom_frame, text="Готов к работе",
                                      bg=self.bg_color, font=("Arial", 9),
                                      anchor=tk.W)
        self.status_label.pack(side=tk.LEFT)

        self.logs_button = tk.Button(bottom_frame, text="📋 Логи",
            font=("Arial", 9), bg="#9C27B0", fg="white",
            bd=0, padx=15, pady=3, cursor="hand2",
            command=self.open_logs_folder)
        self.logs_button.pack(side=tk.RIGHT, padx=(0, 10))
        self.create_tooltip(self.logs_button, "Открыть папку с логами")

        self.clear_button = tk.Button(bottom_frame, text="🧹 Очистить",
            font=("Arial", 9), bg="#f44336", fg="white",
            bd=0, padx=15, pady=3, cursor="hand2",
            command=self.clear_log)
        self.clear_button.pack(side=tk.RIGHT)
        self.create_tooltip(self.clear_button, "Очистить лог и сбросить собранные ID")

    def _validate_numeric(self, new_value):
        """Разрешает только цифры (и пустую строку для возможности удаления)"""
        if new_value == "":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False

    def _validate_page_range(self, event=None):
        """Корректирует диапазон: если начальная > конечная, устанавливает конечную = начальной"""
        try:
            start_val = self.start_entry.get().strip()
            end_val = self.end_entry.get().strip()

            # Если поля пустые, подставляем значения по умолчанию
            if start_val == "":
                start_val = str(config.DEFAULT_MIN_PAGE)
                self.start_entry.delete(0, tk.END)
                self.start_entry.insert(0, start_val)
            if end_val == "":
                end_val = str(config.DEFAULT_MAX_PAGE)
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, end_val)

            start = int(start_val)
            end = int(end_val)

            if start > end:
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, str(start))
                logger.log_info(f"Конечная страница скорректирована на {start}")
            elif end < start:
                self.start_entry.delete(0, tk.END)
                self.start_entry.insert(0, str(end))
                logger.log_info(f"Начальная страница скорректирована на {end}")
        except ValueError:
            # Если не удалось преобразовать в числа, сбрасываем на дефолт
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, str(config.DEFAULT_MIN_PAGE))
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, str(config.DEFAULT_MAX_PAGE))
            logger.log_warning("Некорректный ввод страниц, установлены значения по умолчанию")

    def create_tooltip(self, widget, text):
        def enter(event):
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            x, y = event.x_root + 10, event.y_root + 10
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text=text, bg="#ffffe0",
                             relief=tk.SOLID, bd=1, font=("Arial", 9))
            label.pack()
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def update_delays(self):
        try:
            new_min = int(self.min_delay_spinbox.get())
            new_max = int(self.max_delay_spinbox.get())
            if new_min > new_max:
                self.max_delay_spinbox.delete(0, tk.END)
                self.max_delay_spinbox.insert(0, str(new_min))
                self.max_delay = new_min
            else:
                self.min_delay = new_min
                self.max_delay = new_max
            self.min_delay = max(1, min(30, self.min_delay))
            self.max_delay = max(self.min_delay, min(30, self.max_delay))
            logger.log_info(f"Задержки изменены: {self.min_delay}-{self.max_delay} сек")
        except ValueError:
            pass

    def analyze_url(self):
        self.url_entry.configure(state="normal")
        url = self.url_entry.get().strip()
        self.url_entry.configure(state="readonly")

        try:
            parsed = urlparse(url)
            if not parsed.query:
                self.log("GET параметры не найдены в URL")
                return
            params = parse_qs(parsed.query, keep_blank_values=True)
            self.log("=" * 50)
            self.log("АНАЛИЗ URL:")
            self.log(f"URL: {url}")
            self.log(f"Базовый URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
            self.log(f"Найдено параметров: {len(params)}")
            for key, values in params.items():
                if len(values) > 1:
                    self.log(f"• {key}:")
                    for i, val in enumerate(values, 1):
                        self.log(f"    {i}. {val if val else '<пусто>'}")
                else:
                    val = values[0] if values[0] else "<пусто>"
                    self.log(f"• {key}: {val}")
            self.log("=" * 50)
            logger.log_info(f"Анализ URL: {url}, параметров: {len(params)}")
        except Exception as e:
            logger.log_error(f"Ошибка при анализе URL: {str(e)}")

    def start_parsing(self):
        if self.parsing_active:
            return

        # Проверяем и корректируем диапазон страниц
        self._validate_page_range()

        self.update_delays()
        self.all_ids = []
        self.failed_pages = []
        self.processed_pages = 0
        self.successful_pages = 0
        self.current_retry_pass = 0
        self.update_stats()
        self.parse_button.config(state="disabled", text="⏳")
        self.save_button.config(state="disabled")
        self.progress.pack(side=tk.LEFT, padx=(20, 0), expand=True, fill=tk.X)
        self.progress['value'] = 0
        self.progress['maximum'] = 100
        self.parsing_active = True
        self.paused = False

        self.pause_button.config(text="⏸", state="normal")
        self.pause_button.pack(side=tk.LEFT, padx=(10,0))
        self.stop_button.pack(side=tk.LEFT, padx=(10,0))

        start_page = int(self.start_entry.get())
        end_page = int(self.end_entry.get())
        logger.log_info(f"Запуск парсинга страниц {start_page}-{end_page} "
                        f"с задержкой {self.min_delay}-{self.max_delay} сек")

        thread = Thread(target=self.parsing_process)
        thread.daemon = True
        thread.start()

    def toggle_pause(self):
        """Приостановить или возобновить парсинг."""
        if not self.parsing_active:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="▶", bg="#4CAF50")  # Меняем на зелёный Play
            self.status_label.config(text="Парсинг приостановлен")
            logger.log_info("⏸ Парсинг приостановлен")
            self.log("⏸ Парсинг приостановлен")
        else:
            self.pause_button.config(text="⏸", bg="#FFC107")  # Возвращаем жёлтую паузу
            self.status_label.config(text="Парсинг возобновлён")
            logger.log_info("▶ Парсинг возобновлён")
            self.log("▶ Парсинг возобновлён")

    def stop_parsing(self):
        if self.parsing_active:
            logger.log_info("⏹️ Пользователь запросил остановку парсинга")
            self.parsing_active = False
            self.stop_button.config(state="disabled", text="⏹️")  # Делаем неактивной, но символ оставляем
            self.status_label.config(text="Останавливается...")

    def update_stats(self):
        """Обновляет счётчики в GUI."""
        self.id_counter_label.config(text=str(len(self.all_ids)))
        self.passed_pages_label.config(text=str(self.successful_pages))
        self.lost_pages_label.config(text=str(self.processed_pages - self.successful_pages))

    def parsing_process(self):
        try:
            start_page = int(self.start_entry.get())
            end_page = int(self.end_entry.get())
            total_pages = end_page - start_page + 1

            self.url_entry.configure(state="normal")
            base_url = self.url_entry.get().strip()
            self.url_entry.configure(state="readonly")

            parsed_url = urlparse(base_url)
            base_path = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            query_params = parse_qs(parsed_url.query, keep_blank_values=True)

            self.root.after(0, self.log, f"\n🚀 Начинаем парсинг страниц с {start_page} по {end_page}")
            self.root.after(0, self.log, f"⏱️ Задержка: {self.min_delay}-{self.max_delay} сек")
            self.root.after(0, self.log, f"🔄 Макс. попыток на страницу: {getattr(config, 'PAGE_RETRY_LIMIT', 3)}")

            # ---- ОСНОВНОЙ ПРОХОД ----
            for current_page in range(start_page, end_page + 1):
                if not self.parsing_active:
                    break

                # Проверка паузы
                while self.paused and self.parsing_active:
                    time.sleep(0.5)
                if not self.parsing_active:
                    break

                query_params['page'] = [str(current_page)]
                new_query = urlencode(query_params, doseq=True)
                page_url = f"{base_path}?{new_query}"

                self.root.after(0, self.update_parsing_status,
                                f"Парсинг страницы {current_page}...")

                # Многократные попытки для текущей страницы
                page_attempt = 0
                success = False
                while page_attempt < getattr(config, 'PAGE_RETRY_LIMIT', 3) and self.parsing_active and not success:
                    page_attempt += 1
                    self.root.after(0, self.log, f"   Попытка {page_attempt}...")

                    html = network.fetch_page(page_url)
                    page_ids = parser.extract_ids_from_html(html) if html else []

                    if page_ids:
                        success = True
                        self.all_ids.extend(page_ids)
                        self.successful_pages += 1
                        self.root.after(0, self.update_id_counter)
                        self.root.after(0, self.log,
                            f"✓ Страница {current_page}: найдено {len(page_ids)} ID (попытка {page_attempt})")
                        preview = ', '.join(page_ids[:5])
                        self.root.after(0, self.log,
                            f"   ID: {preview}{'...' if len(page_ids) > 5 else ''}")
                    else:
                        self.root.after(0, self.log,
                            f"⚠️ Страница {current_page}: ID не найдены (попытка {page_attempt})")
                        if page_attempt < getattr(config, 'PAGE_RETRY_LIMIT', 3) and self.parsing_active:
                            time.sleep(getattr(config, 'PAGE_RETRY_DELAY', 5))

                self.processed_pages += 1
                self.root.after(0, self.update_stats)

                if not success:
                    # Добавляем страницу в список неудачных
                    self.failed_pages.append(current_page)
                    self.root.after(0, self.log,
                        f"❌ Страница {current_page}: не удалось получить ID после {getattr(config, 'PAGE_RETRY_LIMIT', 3)} попыток. Будет повторно проверена позже.")

                # Обновление прогресса
                progress = ((current_page - start_page + 1) / total_pages) * 100
                self.root.after(0, self.update_progress, progress)

                # Задержка перед следующей страницей, если не последняя
                if current_page < end_page and self.parsing_active:
                    delay = random.uniform(self.min_delay, self.max_delay)
                    self.root.after(0, self.log, f"⏳ Ожидание {delay:.1f} сек перед следующей страницей...")
                    sleep_until = time.time() + delay
                    while time.time() < sleep_until and self.parsing_active:
                        if self.paused:
                            while self.paused and self.parsing_active:
                                time.sleep(0.5)
                        else:
                            time.sleep(min(0.5, sleep_until - time.time()))

            # ---- ПОВТОРНЫЕ ПРОХОДЫ ДЛЯ НЕУДАЧНЫХ СТРАНИЦ ----
            retry_pass = 0
            while self.failed_pages and retry_pass < self.max_retry_passes and self.parsing_active:
                retry_pass += 1
                self.current_retry_pass = retry_pass
                self.root.after(0, self.log, f"\n🔄 Повторный проход {retry_pass} из {self.max_retry_passes} для страниц: {self.failed_pages}")
                # Копируем список, чтобы можно было удалять обработанные
                to_retry = self.failed_pages[:]
                self.failed_pages = []  # очищаем, будем добавлять снова те, что опять не получились

                for page in to_retry:
                    if not self.parsing_active:
                        break
                    while self.paused and self.parsing_active:
                        time.sleep(0.5)

                    self.root.after(0, self.update_parsing_status, f"Повторный парсинг страницы {page} (проход {retry_pass})...")
                    page_url = base_path + "?" + urlencode({**query_params, 'page': str(page)}, doseq=True)

                    page_attempt = 0
                    success = False
                    while page_attempt < getattr(config, 'PAGE_RETRY_LIMIT', 3) and self.parsing_active and not success:
                        page_attempt += 1
                        self.root.after(0, self.log, f"   Повторная попытка {page_attempt} для страницы {page}...")

                        html = network.fetch_page(page_url)
                        page_ids = parser.extract_ids_from_html(html) if html else []

                        if page_ids:
                            success = True
                            self.all_ids.extend(page_ids)
                            self.successful_pages += 1
                            self.root.after(0, self.update_id_counter)
                            self.root.after(0, self.log,
                                f"✅ Страница {page}: найдено {len(page_ids)} ID на повторном проходе {retry_pass}")
                        else:
                            self.root.after(0, self.log,
                                f"⚠️ Страница {page}: ID не найдены (повторная попытка {page_attempt})")
                            if page_attempt < getattr(config, 'PAGE_RETRY_LIMIT', 3) and self.parsing_active:
                                time.sleep(getattr(config, 'PAGE_RETRY_DELAY', 5))

                    self.processed_pages += 1
                    self.root.after(0, self.update_stats)

                    if not success:
                        self.failed_pages.append(page)
                        self.root.after(0, self.log,
                            f"❌ Страница {page}: не удалось получить ID после {retry_pass} повторных проходов.")

                    # Небольшая пауза между повторными страницами (можно использовать те же задержки)
                    if self.parsing_active and page != to_retry[-1]:
                        delay = random.uniform(self.min_delay, self.max_delay)
                        self.root.after(0, self.log, f"⏳ Ожидание {delay:.1f} сек перед следующей страницей...")
                        time.sleep(delay)

                if self.failed_pages:
                    self.root.after(0, self.log, f"📌 После прохода {retry_pass} остались страницы: {self.failed_pages}")
                else:
                    self.root.after(0, self.log, f"🎉 Все страницы успешно обработаны после {retry_pass} повторных проходов!")

            # ---- ИТОГ ----
            if self.failed_pages:
                final_msg = f"✅ Парсинг завершен! Собрано ID: {len(self.all_ids)}. Не удалось обработать страницы: {self.failed_pages}"
            else:
                final_msg = f"✅ Парсинг завершен! Собрано ID: {len(self.all_ids)}. Все страницы обработаны успешно."

            self.root.after(0, self.parsing_completed, final_msg)

        except Exception as e:
            logger.log_error(f"Критическая ошибка в процессе парсинга: {str(e)}")
            self.root.after(0, self.parsing_completed, f"❌ Ошибка: {str(e)}")

    def update_parsing_status(self, message):
        self.status_label.config(text=message)

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def update_id_counter(self):
        self.id_counter_label.config(text=str(len(self.all_ids)))
        if len(self.all_ids) > 0:
            self.save_button.config(state="normal")

    def log(self, message):
        """Добавляет сообщение в лог-окно GUI."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def parsing_completed(self, message):
        self.parsing_active = False
        self.paused = False
        self.parse_button.config(state="normal", text="▶ Старт")
        self.pause_button.pack_forget()
        self.stop_button.pack_forget()
        self.progress.pack_forget()
        self.status_label.config(text=message)
        self.log(message)
        logger.log_info(message)
        if len(self.all_ids) > 0:
            self.save_button.config(state="normal")

    def save_ids_to_file(self):
        if not self.all_ids:
            messagebox.showwarning("Нет данных", "Нет собранных ID для сохранения")
            return
        try:
            page_range = (int(self.start_entry.get()), int(self.end_entry.get()))
            delay_range = (self.min_delay, self.max_delay)
            detailed, simple = storage.save_ids_to_file(self.all_ids,
                                                         page_range,
                                                         delay_range)
            if detailed:
                self.log(f"\n💾 ID сохранены в файлы:")
                self.log(f"   - {detailed}")
                self.log(f"   - {simple}")
                logger.log_info(f"Сохранено ID: {len(set(self.all_ids))} уникальных")
                messagebox.showinfo("Успех",
                    f"ID сохранены!\nВсего: {len(self.all_ids)}\n"
                    f"Уникальных: {len(set(self.all_ids))}\n"
                    f"Файлы в папке 'output'")
        except Exception as e:
            logger.log_error(f"Ошибка сохранения файла: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def open_logs_folder(self):
        logs_path = os.path.abspath(config.LOGS_DIR)
        if os.path.exists(logs_path):
            os.startfile(logs_path)
            logger.log_info("Открыта папка с логами")
        else:
            messagebox.showinfo("Информация", "Папка с логами еще не создана")

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.all_ids = []
        self.processed_pages = 0
        self.successful_pages = 0
        self.update_stats()
        self.save_button.config(state="disabled")
        self.status_label.config(text="Лог очищен")
        logger.log_info("Лог очищен пользователем")
        self.analyze_url()


def main():
    root = tk.Tk()
    app = Scrapper(root)
    # Поднимаем окно на передний план
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    from modules.router_reboot import cleanup
    root.protocol("WM_DELETE_WINDOW", lambda: (cleanup(), logger.log_info("Приложение закрыто"), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()