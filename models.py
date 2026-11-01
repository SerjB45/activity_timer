"""Модели данных приложения."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Literal


Phase = Literal["work", "rest"]


@dataclass
class Settings:
    """Настройки таймера."""

    work_minutes: int = 25
    rest_minutes: int = 5


@dataclass
class DayStats:
    """Статистика за один день."""

    completed_cycles: int = 0
    work_seconds: float = 0.0
    rest_seconds: float = 0.0


@dataclass
class Stats:
    """Общая статистика (по дням)."""

    days: dict[str, DayStats] = field(default_factory=dict)

    def today(self) -> DayStats:
        """Вернуть статистику за сегодня (создаст запись при необходимости)."""
        key = date.today().isoformat()
        if key not in self.days or not isinstance(self.days[key], DayStats):
            self.days[key] = DayStats()
        record = self.days[key]
        # Нормализация данных
        record.completed_cycles = max(0, int(record.completed_cycles))
        record.work_seconds = max(0.0, float(record.work_seconds))
        record.rest_seconds = max(0.0, float(record.rest_seconds))
        return record


@dataclass
class TimerState:
    """Текущее состояние таймера для отображения в UI."""

    phase: Phase = "work"
    remaining: float = 0.0
    running: bool = False
    paused: bool = False
    activity_text: str = ""
    activity_color: str = ""
    detail_text: str = ""
    progress_fraction: float = 0.0
    cycle_label: str = ""
    today_cycles: int = 0


def format_minutes(total_seconds: float) -> str:
    """Форматирует секунды в строку вида '2 ч 15 мин' или '45 мин'."""
    minutes = max(0, total_seconds) // 60
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours} ч {mins} мин"
    return f"{mins} мин"


def format_timer(seconds: float) -> str:
    """Форматирует секунды в строку таймера MM:SS."""
    secs = max(0, math.ceil(seconds))
    minutes, secs_part = divmod(secs, 60)
    return f"{minutes:02d}:{secs_part:02d}"
