"""Репозитории для хранения данных (JSON)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from models import DayStats, Settings, Stats

from config import SETTINGS_FILE, STATS_FILE

logger = logging.getLogger(__name__)


def _load_json(path: Path, default: dict) -> dict:
    """Безопасная загрузка JSON с fallback на default."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.debug("Не удалось загрузить %s: %s", path.name, exc)
    return default


def _save_json(path: Path, data: dict) -> bool:
    """Безопасное сохранение JSON. Возвращает True при успехе."""
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError as exc:
        logger.error("Не удалось сохранить %s: %s", path.name, exc)
        return False


# ---------- SettingsRepository ----------


class SettingsRepository:
    """Хранение настроек таймера."""

    _file: Path = SETTINGS_FILE  # Для тестов можно подменить
    DEFAULT_WORK = 25
    DEFAULT_REST = 5
    MIN_WORK = 1
    MAX_WORK = 240
    MIN_REST = 1
    MAX_REST = 120

    @classmethod
    def load(cls) -> Settings:
        defaults = {"work_minutes": cls.DEFAULT_WORK, "rest_minutes": cls.DEFAULT_REST}
        file_path = getattr(cls, "_file", SETTINGS_FILE)
        data = _load_json(file_path, defaults)

        work = int(data.get("work_minutes", defaults["work_minutes"]))
        rest = int(data.get("rest_minutes", defaults["rest_minutes"]))

        if cls.MIN_WORK <= work <= cls.MAX_WORK:
            defaults["work_minutes"] = work
        if cls.MIN_REST <= rest <= cls.MAX_REST:
            defaults["rest_minutes"] = rest

        return Settings(**defaults)

    @classmethod
    def save(cls, settings: Settings) -> bool:
        file_path = getattr(cls, "_file", SETTINGS_FILE)
        data = {
            "work_minutes": int(settings.work_minutes),
            "rest_minutes": int(settings.rest_minutes),
        }
        return _save_json(file_path, data)


# ---------- StatsRepository ----------


class StatsRepository:
    """Хранение статистики."""

    _file: Path = STATS_FILE  # Для тестов можно подменить

    @classmethod
    def load(cls) -> Stats:
        file_path = getattr(cls, "_file", STATS_FILE)
        default: dict = {"days": {}}
        data = _load_json(file_path, default)

        days_data = data.get("days", {})
        if not isinstance(days_data, dict):
            days_data = {}

        days = {}
        for key, value in days_data.items():
            if isinstance(value, dict):
                days[key] = DayStats(
                    completed_cycles=int(value.get("completed_cycles", 0)),
                    work_seconds=float(value.get("work_seconds", 0)),
                    rest_seconds=float(value.get("rest_seconds", 0)),
                )
            else:
                days[key] = DayStats()

        return Stats(days=days)

    @classmethod
    def save(cls, stats: Stats) -> bool:
        file_path = getattr(cls, "_file", STATS_FILE)
        data = {"days": {}}
        for key, day_stats in stats.days.items():
            data["days"][key] = {
                "completed_cycles": day_stats.completed_cycles,
                "work_seconds": day_stats.work_seconds,
                "rest_seconds": day_stats.rest_seconds,
            }
        return _save_json(file_path, data)
