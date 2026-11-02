from __future__ import annotations

import logging
import sys
import time
from datetime import date, timedelta
from typing import Callable

from models import (
    DayStats, Phase, Settings, Stats, TimerState, format_minutes, format_timer
)
from config import (
    DAY_NAMES_RU,
    MAX_PHASE_TRANSITIONS,
    MAX_REST_MINUTES,
    MAX_WORK_MINUTES,
    MIN_REST_MINUTES,
    MIN_WORK_MINUTES,
    STATS_SAVE_INTERVAL_SECONDS,
)
from storage import StatsRepository

logger = logging.getLogger(__name__)


class TimerService:
    """Управление таймером: старт, пауза, стоп, тики."""

    def __init__(
        self,
        settings: Settings,
        stats: Stats,
        on_sound: Callable[[], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._settings = settings
        self._stats = stats
        self._on_sound = on_sound
        self._on_error = on_error or (lambda msg: logger.error("%s", msg))

        self._phase: Phase = "work"
        self._remaining: float = settings.work_minutes * 60.0
        self._running: bool = False
        self._paused: bool = False
        self._deadline: float | None = None
        self._phase_started_at: float | None = None
        self._last_accounted_at: float | None = None
        self._phase_elapsed: float = 0.0
        self._cycle_work_seconds: float = 0.0
        self._cycle_rest_seconds: float = 0.0
        self._last_stats_save_at: float | None = None

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def remaining(self) -> float:
        return self._remaining

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def stats(self) -> Stats:
        return self._stats

    def start(self) -> None:
        """Запустить таймер."""
        if self._running:
            return
        self._do_start()

    def pause(self) -> None:
        """Поставить таймер на паузу."""
        if not self._running or self._paused:
            return

        self._account_elapsed(time.monotonic())
        self._remaining = max(
            0.0, (self._deadline or time.monotonic()) - time.monotonic())
        self._paused = True
        self._save_stats(time.monotonic())

    def resume(self) -> None:
        """Продолжить таймер после паузы."""
        if not self._running or not self._paused:
            return

        self._paused = False
        now = time.monotonic()
        self._deadline = now + self._remaining
        self._phase_started_at = now
        self._last_accounted_at = now

    def stop(self) -> None:
        """Остановить таймер и сохранить статистику."""
        if self._running and not self._paused:
            self._account_elapsed(time.monotonic())

        self._running = False
        self._paused = False
        self._phase = "work"
        self._remaining = self._settings.work_minutes * 60.0
        self._deadline = None
        self._phase_started_at = None
        self._last_accounted_at = None
        self._phase_elapsed = 0.0
        self._cycle_work_seconds = 0.0
        self._cycle_rest_seconds = 0.0

        self._save_stats()

    def tick(self) -> TimerState:
        """Выполнить тик таймера и вернуть состояние для UI."""
        if not self._running or self._paused or self._deadline is None:
            return self._build_state()

        now = time.monotonic()
        transitions = 0

        # Обработка переходов между фазами
        while (
            now >= self._deadline
            and self._running
            and transitions < MAX_PHASE_TRANSITIONS
        ):
            transitions += 1
            boundary = self._deadline
            self._account_elapsed(boundary)
            self._finish_phase()
            if not self._running:
                return self._build_state()
            self._deadline = boundary + self._phase_duration()
            self._phase_started_at = boundary
            self._phase_elapsed = 0.0
            self._last_accounted_at = boundary

        self._account_elapsed(now)
        self._remaining = max(0.0, self._deadline - now)

        return self._build_state()

    def update_settings(self, work_minutes: int, rest_minutes: int) -> bool:
        """Обновить настройки (только если таймер не запущен).

        Возвращает True при успехе, False если валидация не пройдена.
        """
        if self._running:
            return False
        return self._validate_and_apply(work_minutes, rest_minutes)

    def start_with_validation(
        self, work_minutes: int, rest_minutes: int
    ) -> bool:
        """Запустить таймер с валидацией настроек.

        Возвращает True при успехе, False если валидация не пройдена.
        """
        if self._running:
            return False
        if not self._validate_and_apply(work_minutes, rest_minutes):
            return False
        self._do_start()
        return True

    def _validate_and_apply(
        self, work_minutes: int, rest_minutes: int
    ) -> bool:
        """Проверить границы значений настроек."""
        if not (MIN_WORK_MINUTES <= work_minutes <= MAX_WORK_MINUTES):
            msg = (
                f"Время работы: {work_minutes} мин. "
                f"Допустимо: {MIN_WORK_MINUTES}–{MAX_WORK_MINUTES} мин."
            )
            self._on_error(msg)
            return False
        if not (MIN_REST_MINUTES <= rest_minutes <= MAX_REST_MINUTES):
            msg = (
                f"Время отдыха: {rest_minutes} мин. "
                f"Допустимо: {MIN_REST_MINUTES}–{MAX_REST_MINUTES} мин."
            )
            self._on_error(msg)
            return False
        self._settings.work_minutes = work_minutes
        self._settings.rest_minutes = rest_minutes
        self._remaining = work_minutes * 60.0
        return True

    def _do_start(self) -> None:
        """Внутренний запуск таймера (без валидации)."""
        self._phase = "work"
        self._remaining = self._settings.work_minutes * 60.0
        self._running = True
        self._paused = False
        self._phase_elapsed = 0.0
        self._cycle_work_seconds = 0.0
        self._cycle_rest_seconds = 0.0

        now = time.monotonic()
        self._last_stats_save_at = now
        self._deadline = now + self._remaining
        self._phase_started_at = now
        self._last_accounted_at = now

    def _phase_duration(self) -> float:
        minutes = (
            self._settings.work_minutes if self._phase == "work"
            else self._settings.rest_minutes
        )
        return float(minutes * 60)

    def _account_elapsed(self, now: float) -> None:
        if self._last_accounted_at is None:
            self._last_accounted_at = now
            return

        elapsed = max(0.0, now - self._last_accounted_at)
        if elapsed:
            record = self._stats.today()
            if self._phase == "work":
                record.work_seconds += elapsed
                self._cycle_work_seconds += elapsed
            else:
                record.rest_seconds += elapsed
                self._cycle_rest_seconds += elapsed
            self._phase_elapsed += elapsed
            self._last_accounted_at = now
            if (
                self._last_stats_save_at is None
                or now - self._last_stats_save_at
                >= STATS_SAVE_INTERVAL_SECONDS
            ):
                self._save_stats(now)

    def _save_stats(self, now: float | None = None) -> None:
        StatsRepository.save(self._stats)
        self._last_stats_save_at = time.monotonic() if now is None else now

    def _finish_phase(self) -> None:
        self._on_sound()

        if self._phase == "work":
            self._phase = "rest"
        else:
            self._phase = "work"
            record = self._stats.today()
            record.completed_cycles += 1
            self._cycle_work_seconds = 0.0
            self._cycle_rest_seconds = 0.0

        self._phase_elapsed = 0.0
        self._save_stats()

    def _build_state(self) -> TimerState:
        """Собрать состояние для отображения."""
        phase = self._phase
        running = self._running
        paused = self._paused

        # Теущее состояние активности
        if not running:
            activity_text = "ГОТОВ К РАБОТЕ"
        elif paused:
            activity_text = "ПАУЗА"
        elif phase == "work":
            activity_text = "ВРЕМЯ РАБОТАТЬ"
        else:
            activity_text = "ВРЕМЯ ОТДЫХАТЬ"

        # Подробный текст
        if paused:
            detail_text = "Отсчёт приостановлен — нажми «Продолжить»"
        elif not running:
            detail_text = "Настрой время и нажми «Старт»"
        elif phase == "work":
            detail_text = "Работа над задачей"
        else:
            detail_text = "Восстановись перед следующим циклом"

        # Прогресс
        if phase == "work":
            total = max(1, self._settings.work_minutes * 60)
        else:
            total = max(1, self._settings.rest_minutes * 60)
        progress_fraction = min(1.0, max(0.0, self._remaining / total))

        # Информация о цикле
        record = self._stats.today()
        cycle_phase = "работа" if phase == "work" else "отдых"
        cycle_label = f"Текущий цикл: {cycle_phase}"
        return TimerState(
            phase=phase,
            remaining=self._remaining,
            running=running,
            paused=paused,
            activity_text=activity_text,
            detail_text=detail_text,
            progress_fraction=progress_fraction,
            cycle_label=cycle_label,
            today_cycles=record.completed_cycles,
        )

    def get_formatted_timer(self) -> str:
        return format_timer(self._remaining)

    def get_today_stats(self) -> DayStats:
        return self._stats.today()

    def format_minutes(self, seconds: float) -> str:
        return format_minutes(seconds)

    def get_week_data(self) -> list[tuple[str, int, date]]:
        """Вернуть данные для графика за последние 7 дней."""
        values = []
        for offset in range(6, -1, -1):
            day = date.today() - timedelta(days=offset)
            entry = self._stats.days.get(day.isoformat(), None)
            if entry is None:
                cycles = 0
            else:
                cycles = int(entry.completed_cycles)
            values.append((day, cycles))

        # Берём названия дней из самих объектов date, а не хардкодим
        return list(zip(
            [DAY_NAMES_RU[d.weekday()] for d, _ in values],
            [v for _, v in values],
            [d for d, _ in values],
        ))


def play_sound() -> None:
    """Воспроизвести звук уведомления."""
    try:
        if sys.platform == "win32":
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        else:
            # Fallback для tkinter — bell() вызывается из UI
            pass
    except Exception:
        logger.warning("Не удалось воспроизвести звук", exc_info=True)
