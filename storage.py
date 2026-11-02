from __future__ import annotations

import json
import logging
import math
from pathlib import Path

from models import DayStats, Settings, Stats

from config import (
    DEFAULT_REST_MINUTES,
    DEFAULT_WORK_MINUTES,
    MAX_REST_MINUTES,
    MAX_WORK_MINUTES,
    MIN_REST_MINUTES,
    MIN_WORK_MINUTES,
    SETTINGS_FILE,
    STATS_FILE,
)

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


def _read_int(value: object, default: int, field: str, path: Path) -> int:
    try:
        if isinstance(value, bool):
            raise ValueError("boolean is not an integer setting")
        return int(value)
    except (TypeError, ValueError, OverflowError):
        logger.warning(
            "Некорректное поле %s в %s; используется %s",
            field,
            path.name,
            default,
        )
        return default


def _read_float(
    value: object, default: float, field: str, path: Path
) -> float:
    try:
        if isinstance(value, bool):
            raise ValueError("boolean is not a numeric statistic")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("statistic must be finite")
        return max(0.0, result)
    except (TypeError, ValueError, OverflowError):
        logger.warning(
            "Некорректное поле %s в %s; используется %s",
            field,
            path.name,
            default,
        )
        return default


class SettingsRepository:
    """Хранение настроек таймера."""

    _file: Path = SETTINGS_FILE  # Для тестов можно подменить
    DEFAULT_WORK = DEFAULT_WORK_MINUTES
    DEFAULT_REST = DEFAULT_REST_MINUTES
    MIN_WORK = MIN_WORK_MINUTES
    MAX_WORK = MAX_WORK_MINUTES
    MIN_REST = MIN_REST_MINUTES
    MAX_REST = MAX_REST_MINUTES

    @classmethod
    def load(cls) -> Settings:
        defaults = {"work_minutes": cls.DEFAULT_WORK,
                    "rest_minutes": cls.DEFAULT_REST}
        file_path = getattr(cls, "_file", SETTINGS_FILE)
        data = _load_json(file_path, defaults)

        work = _read_int(
            data.get("work_minutes", defaults["work_minutes"]),
            defaults["work_minutes"],
            "work_minutes",
            file_path,
        )
        rest = _read_int(
            data.get("rest_minutes", defaults["rest_minutes"]),
            defaults["rest_minutes"],
            "rest_minutes",
            file_path,
        )

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
                    completed_cycles=max(
                        0,
                        _read_int(
                            value.get("completed_cycles", 0),
                            0,
                            "completed_cycles",
                            file_path,
                        ),
                    ),
                    work_seconds=_read_float(
                        value.get("work_seconds",
                                  0), 0.0, "work_seconds", file_path
                    ),
                    rest_seconds=_read_float(
                        value.get("rest_seconds",
                                  0), 0.0, "rest_seconds", file_path
                    ),
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
