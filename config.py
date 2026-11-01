"""Константы и настройки приложения."""

from pathlib import Path

# Пути
APP_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = APP_DIR / "activity_settings.json"
STATS_FILE = APP_DIR / "activity_stats.json"

# Значения по умолчанию
DEFAULT_WORK_MINUTES = 25
DEFAULT_REST_MINUTES = 5

# Границы настроек
MIN_WORK_MINUTES = 1
MAX_WORK_MINUTES = 240
MIN_REST_MINUTES = 1
MAX_REST_MINUTES = 120

# Параметры таймера
TICK_INTERVAL_MS = 150
MAX_PHASE_TRANSITIONS = 100

# Дни недели (русский)
DAY_NAMES_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Размеры окна
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 760
WINDOW_MIN_HEIGHT = 620

# Заголовок приложения
APP_TITLE = "\U0001f345 Таймер активности \u2014 Pomodoro"
APP_TAGLINE = "\u201cФокус \u2022 Результат \u2022 Баланс\u201d"
